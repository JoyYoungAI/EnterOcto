# EnterOcto Ink + Vault MVP

## Purpose

This MVP proves the smallest evidence-preservation loop:

```text
Event JSON
    ↓
Input and policy validation
    ↓
Bounded Dumpcap capture
    ↓
Optional TShark analysis
    ↓
SHA-256 artifact inventory
    ↓
Evidence manifest
```

It is a reference implementation, not a production deployment package.

## Safety defaults

- Dry-run is the default.
- Capture requires both policy opt-in and `--execute`.
- No shell is used to invoke Dumpcap or TShark.
- The capture filter is built from a parsed IP address and validated port.
- Interfaces must appear in a policy allowlist.
- Duration and file size are bounded by policy.
- Evidence directories use restrictive permissions.
- Existing case directories are not overwritten.
- Customer data is not required for tests.

## Dry-run

```bash
python3 scripts/capture/enterocto_capture.py \
  --event examples/sample-event.json \
  --policy config/capture-policy.example.json \
  --output-dir ./evidence
```

The command prints the created case directory.

Expected output structure:

```text
evidence/demo-20260616-001/
├── alert.json
├── capture-command.json
├── capture-policy.json
├── manifest.json
├── analysis/
├── hashes/
│   └── sha256sum.txt
└── packet/
```

The dry-run manifest uses `mode: dry-run`, top-level `status: planned`,
`capture.status: planned`, and `analysis.status: planned` when analysis is
enabled by policy.

## Enabling capture

1. Install Dumpcap independently using the operating system's supported package.
2. Configure capture privileges according to the platform's security guidance.
3. Review the capture interface and legal authorization.
4. Copy the example policy and set:

```json
{
  "capture_enabled": true
}
```

5. Run with `--execute`.

Do not use unrestricted `sudo` as the normal operating model. Prefer a narrowly
configured capture group or capability model appropriate to the operating
system.

If Dumpcap fails after a case directory has been created, the workflow writes a
failed manifest and SHA-256 inventory whenever possible. TShark is treated as an
analysis phase: a TShark timeout or non-zero exit code is recorded under the
manifest `analysis` object without changing a successful packet capture into a
failed capture.

## Event input

The MVP accepts a structured event with these required capture fields:

- `case_id`
- `capture.interface`
- `capture.host`
- `capture.port`
- `capture.duration_seconds`
- `capture.max_kilobytes`

It deliberately does not accept a raw BPF capture filter from the alert.

## Evidence integrity

The workflow writes SHA-256 values for generated artifacts and the manifest.
A hash proves that a file has not changed relative to the recorded digest; it
does not by itself prove legal chain of custody.

Future work should add:

- manifest signing;
- trusted timestamps;
- storage access logs;
- retention and deletion records;
- time-synchronization status;
- case ownership and evidence transfer records.

## Schema validation

The manifest follows:

```text
schemas/evidence-manifest.schema.json
```

The MVP runtime does not require the external `jsonschema` package. Development
and CI schema tests install `requirements-dev.txt` and validate dry-run, failed
capture, and analysis-timeout manifests against the schema.

## Tests

```bash
python3 -m compileall scripts tests
python3 -m unittest discover -s tests -v
```

Tests use dry-run mode and do not require packet-capture privileges.
