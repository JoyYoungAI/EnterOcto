# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "capture"
    / "enterocto_capture.py"
)
SPEC = importlib.util.spec_from_file_location("enterocto_capture", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidationTests(unittest.TestCase):
    def policy(self) -> dict:
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

    def event(self) -> dict:
        return {
            "case_id": "case-001",
            "capture": {
                "interface": "lo",
                "host": "127.0.0.1",
                "port": 18789,
                "duration_seconds": 10,
                "max_kilobytes": 5000,
            },
        }

    def test_rejects_path_traversal_case_id(self) -> None:
        event = self.event()
        event["case_id"] = "../escape"
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate_inputs(event, self.policy())

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

    def test_dry_run_creates_manifest_without_packet_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path = base / "event.json"
            policy_path = base / "policy.json"
            event_path.write_text(json.dumps(self.event()), encoding="utf-8")
            policy_path.write_text(json.dumps(self.policy()), encoding="utf-8")

            case_dir = MODULE.run_workflow(
                event_path,
                policy_path,
                base / "evidence",
                execute=False,
            )

            manifest = json.loads(
                (case_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["mode"], "dry-run")
            self.assertEqual(manifest["status"], "planned")
            self.assertFalse(manifest["capture"]["enabled"])
            self.assertTrue((case_dir / "hashes" / "sha256sum.txt").exists())
            self.assertFalse((case_dir / "packet" / "capture.pcapng").exists())

    def test_execute_requires_policy_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            event_path = base / "event.json"
            policy_path = base / "policy.json"
            event_path.write_text(json.dumps(self.event()), encoding="utf-8")
            policy_path.write_text(json.dumps(self.policy()), encoding="utf-8")

            with self.assertRaises(MODULE.ValidationError):
                MODULE.run_workflow(
                    event_path,
                    policy_path,
                    base / "evidence",
                    execute=True,
                )


if __name__ == "__main__":
    unittest.main()
