# Isolated Dumpcap Lab Validation

This guide is for validating EnterOcto Ink + Vault with a real Dumpcap capture
in an isolated lab. Do not run this procedure on production networks or hosts
that may carry customer, employee, credential, or business traffic.

## Recommended Lab

- Ubuntu 24.04 LTS VM or WSL2 Ubuntu.
- No real company traffic.
- Loopback or an isolated virtual network only.
- Synthetic test traffic only.
- No customer data, credentials, private keys, or access tokens.
- Evidence deleted securely after validation.

## Install External Tools

Install Wireshark command-line tools through the operating system package
manager for this isolated lab only. For normal deployment and operations,
follow the official Wireshark installation documentation and your operating
system's package guidance:

```text
https://www.wireshark.org/docs/wsug_html_chunked/ChapterBuildInstall.html
```

Do not copy Dumpcap, TShark, or Wireshark binaries into this repository.

```bash
sudo apt update
sudo apt install wireshark-common tshark
```

During installation, Ubuntu may ask whether non-superusers can capture packets.
Granting capture privileges to a group or setting capabilities on Dumpcap
changes the host trust boundary. Use the narrowest lab-only permission model
that satisfies the test, document it, and remove it after validation. Do not
blindly apply unrestricted setuid or broad `chmod 4755` guidance.

## Generate Synthetic Traffic

Start a local HTTP server on loopback and keep it running:

```bash
python3 -m http.server 18789 --bind 127.0.0.1
```

Do not generate the HTTP request yet. Send the request only after the EnterOcto
capture command below has started, so the request occurs during the capture
window.

## Lab Policy

Use the dedicated lab policy:

```text
config/capture-policy.lab.json.example
```

It enables capture only for interface `lo`, limits duration to 10 seconds,
limits capture size to 5 MB, allows loopback addresses, and disables multicast
and unspecified addresses. Do not weaken the safe defaults in
`config/capture-policy.example.json` for lab convenience.

## Run Capture

In a second terminal, start the EnterOcto capture workflow:

```bash
python3 scripts/capture/enterocto_capture.py \
  --event examples/sample-event.json \
  --policy config/capture-policy.lab.json.example \
  --output-dir ./evidence-lab \
  --execute
```

While the capture command is still running, use a third terminal to generate a
small loopback request:

```bash
curl http://127.0.0.1:18789/
```

## Acceptance Checks

- Dumpcap exits cleanly.
- `packet/capture.pcapng` exists.
- The PCAPNG file is no larger than the policy limit.
- Manifest `mode` is `capture`.
- Manifest `capture.status` is `completed`.
- Manifest `analysis.status` is `completed`, `failed`, `timeout`, or
  `tool-unavailable` with a clear reason.
- `hashes/sha256sum.txt` includes generated artifacts and `manifest.json`.
- `sha256sum -c hashes/sha256sum.txt` succeeds from the case directory.
- Evidence file permissions are no broader than owner read/write where the
  filesystem supports POSIX modes.
- The capture contains only synthetic loopback traffic.
- Lab evidence is deleted after review according to the test plan.

## Cleanup

Stop the local HTTP server, remove temporary capture privileges that were added
for the lab, and delete the `evidence-lab` directory after any required review
is complete.
