#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""EnterOcto Ink + Vault reference MVP.

Validates an event and capture policy, creates a restricted evidence directory,
optionally invokes independently installed Dumpcap, optionally analyzes the
capture with TShark, and writes a SHA-256 evidence manifest.

Dry-run is the default. Packet capture requires both policy capture_enabled=true
and the --execute command-line flag.
"""

from __future__ import annotations

import argparse
import datetime as dt
import getpass
import hashlib
import ipaddress
import json
import mimetypes
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import sys
from typing import Any

SCHEMA_VERSION = "0.1.0"
CASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
INTERFACE_RE = re.compile(r"^[A-Za-z0-9_.:@-]{1,64}$")


class ValidationError(ValueError):
    """Raised when untrusted input violates the capture policy."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"Top-level JSON value must be an object: {path}")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_version_line(executable: str) -> str | None:
    path = shutil.which(executable)
    if path is None:
        return None
    try:
        result = subprocess.run(
            [path, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return path
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0] if text else path


def validate_case_id(value: Any) -> str:
    if not isinstance(value, str) or not CASE_ID_RE.fullmatch(value):
        raise ValidationError(
            "case_id must start with an alphanumeric character and contain only "
            "letters, numbers, dot, underscore, or hyphen (maximum 64 characters)"
        )
    if value in {".", ".."} or ".." in value:
        raise ValidationError("case_id must not contain '..'")
    return value


def validate_interface(value: Any, allowed: list[str]) -> str:
    if not isinstance(value, str) or not INTERFACE_RE.fullmatch(value):
        raise ValidationError("capture.interface contains unsupported characters")
    if value not in allowed:
        raise ValidationError(
            f"capture.interface {value!r} is not in policy allowed_interfaces"
        )
    return value


def validate_integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValidationError(f"{name} must be between {minimum} and {maximum}")
    return value


def validate_address(value: Any, policy: dict[str, Any]) -> str:
    if not isinstance(value, str):
        raise ValidationError("capture.host must be an IPv4 or IPv6 address")
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValidationError("capture.host must be an IPv4 or IPv6 address") from exc

    checks = [
        ("is_private", "allow_private_addresses", "private"),
        ("is_loopback", "allow_loopback_addresses", "loopback"),
        ("is_multicast", "allow_multicast_addresses", "multicast"),
        ("is_unspecified", "allow_unspecified_addresses", "unspecified"),
    ]
    for attribute, setting, label in checks:
        if getattr(address, attribute) and not bool(policy.get(setting, False)):
            raise ValidationError(f"{label} addresses are disabled by policy")
    return address.compressed


def validate_inputs(
    event: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    case_id = validate_case_id(event.get("case_id"))
    capture = event.get("capture")
    if not isinstance(capture, dict):
        raise ValidationError("event.capture must be an object")

    allowed_interfaces = policy.get("allowed_interfaces")
    if (
        not isinstance(allowed_interfaces, list)
        or not allowed_interfaces
        or not all(isinstance(item, str) for item in allowed_interfaces)
    ):
        raise ValidationError("policy.allowed_interfaces must be a non-empty list")

    interface = validate_interface(capture.get("interface"), allowed_interfaces)
    host = validate_address(capture.get("host"), policy)
    port = validate_integer(capture.get("port"), "capture.port", 1, 65535)

    policy_duration = validate_integer(
        policy.get("max_duration_seconds"),
        "policy.max_duration_seconds",
        1,
        3600,
    )
    policy_size = validate_integer(
        policy.get("max_capture_kilobytes"),
        "policy.max_capture_kilobytes",
        1,
        10 * 1024 * 1024,
    )
    duration = validate_integer(
        capture.get("duration_seconds"),
        "capture.duration_seconds",
        1,
        policy_duration,
    )
    max_kilobytes = validate_integer(
        capture.get("max_kilobytes"),
        "capture.max_kilobytes",
        1,
        policy_size,
    )

    return {
        "case_id": case_id,
        "interface": interface,
        "host": host,
        "port": port,
        "duration_seconds": duration,
        "max_kilobytes": max_kilobytes,
    }


def capture_filter(host: str, port: int) -> str:
    # host and port are already parsed and validated. No user-supplied filter
    # expression is accepted.
    return f"host {host} and port {port}"


def build_dumpcap_command(
    executable: str,
    interface: str,
    filter_expression: str,
    duration_seconds: int,
    max_kilobytes: int,
    output_file: Path,
) -> list[str]:
    return [
        executable,
        "-i",
        interface,
        "-f",
        filter_expression,
        "-a",
        f"duration:{duration_seconds}",
        "-a",
        f"filesize:{max_kilobytes}",
        "-w",
        str(output_file),
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)


def artifact_record(case_dir: Path, path: Path) -> dict[str, Any]:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "path": path.relative_to(case_dir).as_posix(),
        "media_type": media_type,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def create_case_directory(output_root: Path, case_id: str) -> Path:
    output_root = output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_root.chmod(0o700)

    case_dir = output_root / case_id
    if case_dir.exists():
        raise ValidationError(f"Evidence case already exists: {case_dir}")
    case_dir.mkdir(mode=0o700)
    (case_dir / "packet").mkdir(mode=0o700)
    (case_dir / "analysis").mkdir(mode=0o700)
    (case_dir / "hashes").mkdir(mode=0o700)
    return case_dir


def run_workflow(
    event_path: Path,
    policy_path: Path,
    output_root: Path,
    execute: bool,
) -> Path:
    os.umask(0o077)
    event = load_json(event_path)
    policy = load_json(policy_path)
    values = validate_inputs(event, policy)

    capture_allowed = bool(policy.get("capture_enabled", False))
    capture_mode = execute and capture_allowed
    if execute and not capture_allowed:
        raise ValidationError(
            "--execute was requested but policy.capture_enabled is false"
        )

    case_dir = create_case_directory(output_root, values["case_id"])
    event_copy = case_dir / "alert.json"
    policy_copy = case_dir / "capture-policy.json"
    write_json(event_copy, event)
    write_json(policy_copy, policy)

    pcap_path = case_dir / "packet" / "capture.pcapng"
    filter_expression = capture_filter(values["host"], values["port"])
    dumpcap_path = shutil.which("dumpcap")
    command_executable = dumpcap_path or "dumpcap"
    command = build_dumpcap_command(
        command_executable,
        values["interface"],
        filter_expression,
        values["duration_seconds"],
        values["max_kilobytes"],
        pcap_path,
    )
    command_file = case_dir / "capture-command.json"
    write_json(
        command_file,
        {
            "shell": False,
            "argv": command,
            "note": "Arguments are executed directly; no shell interpolation is used.",
        },
    )

    started_at = None
    finished_at = None
    return_code = None
    error: str | None = None
    status = "planned"

    if capture_mode:
        if dumpcap_path is None:
            raise ValidationError("dumpcap is required when capture is enabled")
        started_at = utc_now()
        try:
            result = subprocess.run(
                command,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=values["duration_seconds"] + 20,
            )
            return_code = result.returncode
            (case_dir / "capture.stdout.txt").write_text(
                result.stdout, encoding="utf-8"
            )
            (case_dir / "capture.stderr.txt").write_text(
                result.stderr, encoding="utf-8"
            )
            status = "completed" if result.returncode == 0 and pcap_path.exists() else "failed"
            if status == "failed":
                error = f"dumpcap exited with return code {result.returncode}"
        except subprocess.TimeoutExpired as exc:
            status = "failed"
            error = f"dumpcap exceeded workflow timeout: {exc}"
        finally:
            finished_at = utc_now()

        if (
            status == "completed"
            and bool(policy.get("run_tshark_analysis", True))
            and shutil.which("tshark")
        ):
            analysis_path = case_dir / "analysis" / "protocol-hierarchy.txt"
            analysis = subprocess.run(
                ["tshark", "-r", str(pcap_path), "-q", "-z", "io,phs"],
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            analysis_path.write_text(
                (analysis.stdout or "") + (analysis.stderr or ""),
                encoding="utf-8",
            )
            analysis_path.chmod(0o600)

    artifact_paths = [
        event_copy,
        policy_copy,
        command_file,
        case_dir / "capture.stdout.txt",
        case_dir / "capture.stderr.txt",
        pcap_path,
        case_dir / "analysis" / "protocol-hierarchy.txt",
    ]
    artifacts = [
        artifact_record(case_dir, path)
        for path in artifact_paths
        if path.exists() and path.is_file()
    ]

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "case_id": values["case_id"],
        "created_at": utc_now(),
        "mode": "capture" if capture_mode else "dry-run",
        "status": status,
        "source_event": {
            "path": "alert.json",
            "sha256": sha256_file(event_copy),
        },
        "capture": {
            "enabled": capture_mode,
            "interface": values["interface"],
            "host": values["host"],
            "port": values["port"],
            "duration_seconds": values["duration_seconds"],
            "max_kilobytes": values["max_kilobytes"],
            "filter": filter_expression,
            "command": command,
            "started_at": started_at,
            "finished_at": finished_at,
            "return_code": return_code,
        },
        "environment": {
            "hostname": socket.gethostname(),
            "python_version": platform.python_version(),
            "operator": {
                "username": getpass.getuser(),
                "uid": os.getuid(),
                "gid": os.getgid(),
            },
            "tools": {
                "dumpcap": first_version_line("dumpcap"),
                "tshark": first_version_line("tshark"),
            },
        },
        "artifacts": artifacts,
        "error": error,
    }

    manifest_path = case_dir / "manifest.json"
    write_json(manifest_path, manifest)

    hash_lines = [
        f"{record['sha256']}  {record['path']}"
        for record in artifacts
    ]
    hash_lines.append(f"{sha256_file(manifest_path)}  manifest.json")
    hash_file = case_dir / "hashes" / "sha256sum.txt"
    hash_file.write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    hash_file.chmod(0o600)

    return case_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an EnterOcto Ink + Vault evidence case."
    )
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("./evidence"))
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform capture. Policy capture_enabled must also be true.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        case_dir = run_workflow(
            args.event,
            args.policy,
            args.output_dir,
            args.execute,
        )
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"system error: {exc}", file=sys.stderr)
        return 3

    print(case_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
