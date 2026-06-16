# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any
import unittest
from unittest import mock


try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only without dev deps.
    jsonschema = None


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "capture"
    / "enterocto_capture.py"
)
SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "evidence-manifest.schema.json"
)
SPEC = importlib.util.spec_from_file_location("enterocto_capture", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WorkflowTestCase(unittest.TestCase):
    def policy(self) -> dict[str, Any]:
        return {
            "capture_enabled": False,
            "allowed_interfaces": ["lo"],
            "max_duration_seconds": 60,
            "max_capture_kilobytes": 50000,
            "allow_private_addresses": True,
            "allow_loopback_addresses": True,
            "allow_multicast_addresses": False,
            "allow_unspecified_addresses": False,
            "run_tshark_analysis": True,
        }

    def capture_policy(self) -> dict[str, Any]:
        policy = self.policy()
        policy["capture_enabled"] = True
        return policy

    def event(self, case_id: str = "case-001") -> dict[str, Any]:
        return {
            "case_id": case_id,
            "capture": {
                "interface": "lo",
                "host": "127.0.0.1",
                "port": 18789,
                "duration_seconds": 10,
                "max_kilobytes": 5000,
            },
        }

    def write_inputs(
        self, base: Path, policy: dict[str, Any], event: dict[str, Any] | None = None
    ) -> tuple[Path, Path]:
        event_path = base / "event.json"
        policy_path = base / "policy.json"
        event_path.write_text(json.dumps(event or self.event()), encoding="utf-8")
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        return event_path, policy_path

    def read_manifest(self, case_dir: Path) -> dict[str, Any]:
        return json.loads((case_dir / "manifest.json").read_text(encoding="utf-8"))

    def run_with_fake_versions(self, *args: Any, **kwargs: Any) -> Path:
        with mock.patch.object(MODULE, "first_version_line", return_value=None):
            return MODULE.run_workflow(*args, **kwargs)


class ValidationTests(WorkflowTestCase):
    def test_rejects_path_traversal_case_id(self) -> None:
        event = self.event("../escape")
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate_inputs(event, self.policy())

    def test_rejects_schema_disallowed_case_id_with_double_dot(self) -> None:
        event = self.event("a..b")
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate_inputs(event, self.policy())

    def test_accepts_simple_case_id_with_safe_separators(self) -> None:
        event = self.event("a-b_c.1")
        values = MODULE.validate_inputs(event, self.policy())
        self.assertEqual(values["case_id"], "a-b_c.1")

    def test_rejects_unlisted_interface(self) -> None:
        event = self.event()
        event["capture"]["interface"] = "eth99"
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate_inputs(event, self.policy())

    def test_rejects_unparsed_filter_input(self) -> None:
        event = self.event()
        event["capture"]["host"] = "127.0.0.1 or port 22"
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate_inputs(event, self.policy())

    def test_rejects_string_false_for_capture_enabled(self) -> None:
        policy = self.policy()
        policy["capture_enabled"] = "false"
        with self.assertRaisesRegex(MODULE.ValidationError, "must be a boolean"):
            MODULE.validate_inputs(self.event(), policy)

    def test_rejects_integer_boolean_policy_values(self) -> None:
        for value in (0, 1):
            with self.subTest(value=value):
                policy = self.policy()
                policy["capture_enabled"] = value
                with self.assertRaisesRegex(MODULE.ValidationError, "must be a boolean"):
                    MODULE.validate_inputs(self.event(), policy)

    def test_accepts_json_boolean_policy_values(self) -> None:
        for value in (False, True):
            with self.subTest(value=value):
                policy = self.policy()
                policy["capture_enabled"] = value
                values = MODULE.validate_inputs(self.event(), policy)
                self.assertIs(values["capture_enabled"], value)

    def test_rejects_other_boolean_policy_fields_with_wrong_type(self) -> None:
        for field in MODULE.BOOLEAN_POLICY_FIELDS:
            with self.subTest(field=field):
                policy = self.policy()
                policy[field] = "true"
                with self.assertRaisesRegex(MODULE.ValidationError, "must be a boolean"):
                    MODULE.validate_inputs(self.event(), policy)

    def test_build_command_uses_argument_vector(self) -> None:
        command = MODULE.build_dumpcap_command(
            "/usr/bin/dumpcap",
            "lo",
            "host 127.0.0.1 and port 18789",
            10,
            5000,
            Path("/tmp/capture.pcapng"),
        )
        self.assertEqual(command[0], "/usr/bin/dumpcap")
        self.assertIn("duration:10", command)
        self.assertIn("filesize:5000", command)


class WorkflowTests(WorkflowTestCase):
    def test_dry_run_creates_manifest_without_packet_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.policy())

            case_dir = self.run_with_fake_versions(
                event_path,
                policy_path,
                base / "evidence",
                execute=False,
            )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["mode"], "dry-run")
            self.assertEqual(manifest["status"], "planned")
            self.assertEqual(manifest["capture"]["status"], "planned")
            self.assertFalse(manifest["capture"]["enabled"])
            self.assertEqual(manifest["analysis"]["status"], "planned")
            self.assertTrue((case_dir / "hashes" / "sha256sum.txt").exists())
            self.assertFalse((case_dir / "packet" / "capture.pcapng").exists())

    def test_execute_requires_policy_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.policy())

            with self.assertRaises(MODULE.ValidationError):
                self.run_with_fake_versions(
                    event_path,
                    policy_path,
                    base / "evidence",
                    execute=True,
                )

    def test_missing_dumpcap_fails_before_case_directory_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            evidence_root = base / "evidence"
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            with mock.patch.object(MODULE.shutil, "which", return_value=None):
                with self.assertRaisesRegex(MODULE.ValidationError, "dumpcap"):
                    self.run_with_fake_versions(
                        event_path,
                        policy_path,
                        evidence_root,
                        execute=True,
                    )

            self.assertFalse((evidence_root / "case-001").exists())

    def test_dumpcap_nonzero_exit_writes_failed_manifest_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run") as run:
                        run.return_value = subprocess.CompletedProcess(
                            ["/usr/bin/dumpcap"], 1, stdout="", stderr="failed"
                        )
                        case_dir = MODULE.run_workflow(
                            event_path,
                            policy_path,
                            base / "evidence",
                            execute=True,
                        )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["capture"]["status"], "failed")
            self.assertEqual(manifest["capture"]["return_code"], 1)
            self.assertEqual(manifest["analysis"]["status"], "not-requested")
            self.assertTrue((case_dir / "hashes" / "sha256sum.txt").exists())

    def test_dumpcap_timeout_writes_failed_manifest_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run") as run:
                        run.side_effect = subprocess.TimeoutExpired(
                            cmd=["/usr/bin/dumpcap"], timeout=30
                        )
                        case_dir = MODULE.run_workflow(
                            event_path,
                            policy_path,
                            base / "evidence",
                            execute=True,
                        )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["capture"]["status"], "failed")
            self.assertIn("timeout", manifest["capture"]["error"])
            self.assertTrue((case_dir / "hashes" / "sha256sum.txt").exists())

    def test_tshark_success_is_recorded_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess:
                if command[0].endswith("dumpcap"):
                    Path(command[-1]).write_bytes(b"pcap")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                return subprocess.CompletedProcess(command, 0, stdout="hierarchy", stderr="")

            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                        case_dir = MODULE.run_workflow(
                            event_path,
                            policy_path,
                            base / "evidence",
                            execute=True,
                        )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["capture"]["status"], "completed")
            self.assertEqual(manifest["analysis"]["status"], "completed")
            self.assertEqual(
                manifest["analysis"]["artifacts"],
                ["analysis/protocol-hierarchy.txt"],
            )

    def test_tshark_nonzero_exit_is_recorded_without_failing_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess:
                if command[0].endswith("dumpcap"):
                    Path(command[-1]).write_bytes(b"pcap")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                return subprocess.CompletedProcess(command, 2, stdout="", stderr="bad pcap")

            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                        case_dir = MODULE.run_workflow(
                            event_path,
                            policy_path,
                            base / "evidence",
                            execute=True,
                        )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["capture"]["status"], "completed")
            self.assertEqual(manifest["analysis"]["status"], "failed")
            self.assertEqual(manifest["analysis"]["return_code"], 2)

    def test_tshark_timeout_is_recorded_without_failing_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess:
                if command[0].endswith("dumpcap"):
                    Path(command[-1]).write_bytes(b"pcap")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                raise subprocess.TimeoutExpired(cmd=command, timeout=60)

            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                        case_dir = MODULE.run_workflow(
                            event_path,
                            policy_path,
                            base / "evidence",
                            execute=True,
                        )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["capture"]["status"], "completed")
            self.assertEqual(manifest["analysis"]["status"], "timeout")
            self.assertTrue((case_dir / "hashes" / "sha256sum.txt").exists())

    def test_tshark_artifact_write_failure_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())
            original_write = MODULE.write_text_artifact

            def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess:
                if command[0].endswith("dumpcap"):
                    Path(command[-1]).write_bytes(b"pcap")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                return subprocess.CompletedProcess(command, 0, stdout="hierarchy", stderr="")

            def fake_write(path: Path, value: str | bytes | None) -> None:
                if path.name == "protocol-hierarchy.txt":
                    raise OSError("blocked")
                original_write(path, value)

            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                        with mock.patch.object(
                            MODULE, "write_text_artifact", side_effect=fake_write
                        ):
                            case_dir = MODULE.run_workflow(
                                event_path,
                                policy_path,
                                base / "evidence",
                                execute=True,
                            )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["capture"]["status"], "completed")
            self.assertEqual(manifest["analysis"]["status"], "failed")
            self.assertIn("artifact could not be written", manifest["analysis"]["error"])
            self.assertTrue((case_dir / "hashes" / "sha256sum.txt").exists())

    def test_tshark_unavailable_is_recorded_without_failing_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            def fake_resolve(name: str) -> str | None:
                return "/usr/bin/dumpcap" if name == "dumpcap" else None

            def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess:
                Path(command[-1]).write_bytes(b"pcap")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with mock.patch.object(MODULE, "resolve_executable", side_effect=fake_resolve):
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.shutil, "which", return_value="/usr/bin/tool"):
                        with mock.patch.object(
                            MODULE.subprocess, "run", side_effect=fake_run
                        ):
                            case_dir = MODULE.run_workflow(
                                event_path,
                                policy_path,
                                base / "evidence",
                                execute=True,
                            )

            manifest = self.read_manifest(case_dir)
            self.assertEqual(manifest["capture"]["status"], "completed")
            self.assertEqual(manifest["analysis"]["status"], "tool-unavailable")


@unittest.skipIf(jsonschema is None, "jsonschema is not installed")
class SchemaValidationTests(WorkflowTestCase):
    def setUp(self) -> None:
        assert jsonschema is not None
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.validator = jsonschema.Draft202012Validator(self.schema)

    def assert_valid_manifest(self, manifest: dict[str, Any]) -> None:
        errors = sorted(self.validator.iter_errors(manifest), key=str)
        self.assertEqual([], errors)

    def test_schema_rejects_case_id_with_double_dot(self) -> None:
        manifest = {
            "schema_version": "0.1.0",
            "case_id": "a..b",
            "created_at": "2026-06-16T00:00:00Z",
            "mode": "dry-run",
            "status": "planned",
            "source_event": {"path": "alert.json", "sha256": "0" * 64},
            "capture": {
                "enabled": False,
                "status": "planned",
                "interface": "lo",
                "host": "127.0.0.1",
                "port": 18789,
                "duration_seconds": 10,
                "max_kilobytes": 5000,
                "filter": "host 127.0.0.1 and port 18789",
                "command": ["dumpcap"],
                "started_at": None,
                "finished_at": None,
                "return_code": None,
                "error": None,
            },
            "analysis": {
                "requested": True,
                "tool_available": False,
                "status": "planned",
                "return_code": None,
                "started_at": None,
                "finished_at": None,
                "error": None,
                "artifacts": [],
            },
            "environment": {
                "hostname": "host",
                "python_version": "3.11.0",
                "operator": {"username": "user", "uid": 0, "gid": 0},
                "tools": {"dumpcap": None, "tshark": None},
            },
            "artifacts": [],
            "error": None,
        }
        errors = list(self.validator.iter_errors(manifest))
        self.assertTrue(errors)

    def test_schema_accepts_case_id_with_safe_separators(self) -> None:
        jsonschema.Draft202012Validator(
            self.schema["properties"]["case_id"]
        ).validate("a-b_c.1")

    def test_dry_run_manifest_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.policy())
            case_dir = self.run_with_fake_versions(
                event_path,
                policy_path,
                base / "evidence",
                execute=False,
            )
            self.assert_valid_manifest(self.read_manifest(case_dir))

    def test_capture_failed_manifest_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())
            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run") as run:
                        run.return_value = subprocess.CompletedProcess(
                            ["/usr/bin/dumpcap"], 1, stdout="", stderr="failed"
                        )
                        case_dir = MODULE.run_workflow(
                            event_path,
                            policy_path,
                            base / "evidence",
                            execute=True,
                        )
            self.assert_valid_manifest(self.read_manifest(case_dir))

    def test_analysis_timeout_manifest_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path, policy_path = self.write_inputs(base, self.capture_policy())

            def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess:
                if command[0].endswith("dumpcap"):
                    Path(command[-1]).write_bytes(b"pcap")
                    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
                raise subprocess.TimeoutExpired(cmd=command, timeout=60)

            with mock.patch.object(MODULE, "resolve_executable") as resolve:
                resolve.side_effect = lambda name: f"/usr/bin/{name}"
                with mock.patch.object(MODULE, "first_version_line", return_value=None):
                    with mock.patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                        case_dir = MODULE.run_workflow(
                            event_path,
                            policy_path,
                            base / "evidence",
                            execute=True,
                        )
            self.assert_valid_manifest(self.read_manifest(case_dir))


if __name__ == "__main__":
    unittest.main()
