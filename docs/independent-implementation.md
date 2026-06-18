# EnterOcto Independent Implementation Plan

## Purpose

EnterOcto does not replace the official deployment guides for Zeek, Falco,
Wazuh, Wireshark, TShark, or Dumpcap. Those upstream projects remain the source
of truth for installation, upgrade, hardening, and operational maintenance.

EnterOcto provides an independent integration implementation on top of those
separately installed tools. The implementation focuses on connecting telemetry,
policy, evidence capture, manifest generation, and audit-ready handoff in a
safe and maintainable way.

In short:

- upstream projects provide the sensors, runtimes, managers, and packet tools;
- EnterOcto provides the integration logic, evidence workflow, schemas,
  policies, adapters, tests, and operator documentation;
- production deployments should combine official upstream guidance with
  EnterOcto-specific integration procedures.

## Implementation Boundary

EnterOcto-owned implementation may include:

- Python reference workflows for Ink + Vault evidence handling;
- JSON schemas for evidence manifests and future timelines;
- capture policies and validation rules;
- adapters that invoke separately installed CLI tools;
- synthetic examples and lab-only validation profiles;
- documentation for integration assumptions and operational handoff;
- tests that prove dry-run safety, failure handling, and schema compatibility.

EnterOcto should not include:

- copied Zeek, Falco, Wazuh, Wireshark, TShark, or Dumpcap binaries;
- copied Wazuh decoders or rules in the Apache-2.0 core repository;
- production packet captures or customer evidence;
- unofficial replacements for upstream deployment manuals;
- broad privilege-elevation scripts that bypass local security review.

## Reference Architecture

The independent implementation is organized around a narrow integration flow:

```text
Upstream telemetry
    ↓
EnterOcto event normalization
    ↓
Policy validation
    ↓
Bounded evidence capture or dry-run plan
    ↓
Optional packet analysis
    ↓
Manifest and hash inventory
    ↓
Operator review and retention handoff
```

This flow keeps upstream tools independent while giving EnterOcto a consistent
evidence contract.

## Initial Implementation Tracks

### Track 1 — Ink + Vault Reference Workflow

Goal: provide a safe command-line evidence workflow.

Deliverables:

- `scripts/capture/enterocto_capture.py`
- capture policy examples
- evidence manifest schema
- dry-run by default
- failed-manifest behavior
- SHA-256 inventory
- unit tests and schema validation tests

Status: initial MVP in progress.

### Track 2 — Event Normalization

Goal: define the minimal event shape EnterOcto accepts from upstream telemetry
or operator input.

Planned deliverables:

- event schema
- example events for Zeek-like, Falco-like, and Wazuh-like sources
- normalization notes for host, process, network, and timing fields
- validation tests using synthetic data only

### Track 3 — Upstream Adapter Contracts

Goal: document how EnterOcto talks to external tools without bundling them.

Planned deliverables:

- Zeek log input contract
- Falco JSON event input contract
- Wazuh alert input contract
- Dumpcap command adapter contract
- TShark analysis adapter contract
- version and capability checks

### Track 4 — Lab Profiles

Goal: provide safe validation recipes that do not touch production traffic.

Planned deliverables:

- isolated loopback capture profile
- synthetic traffic generator examples
- lab acceptance checklist
- cleanup and evidence deletion guidance
- explicit warnings against customer data and broad capture permissions

### Track 5 — Operator Handoff

Goal: make generated evidence understandable and reviewable.

Planned deliverables:

- manifest field reference
- hash verification instructions
- case directory layout
- retention and deletion notes
- review checklist for analysts
- known limitations

## Deployment Positioning

EnterOcto documentation should use this pattern:

1. Link to official upstream deployment guidance for installing each tool.
2. State the EnterOcto integration assumptions.
3. Provide EnterOcto-specific configuration examples.
4. Provide dry-run validation first.
5. Provide isolated lab validation second.
6. Leave production deployment decisions to the operator's security,
   compliance, and infrastructure policies.

Example wording:

```markdown
Install and operate Zeek, Falco, Wazuh, Wireshark, TShark, and Dumpcap by
following their official documentation. EnterOcto assumes those tools are
installed, licensed, configured, and maintained independently. This guide only
describes the EnterOcto integration layer and reference workflow.
```

## Safety Principles

- Dry-run must remain the default.
- Real packet capture must require explicit policy opt-in and explicit CLI
  execution.
- External commands must use argument vectors and `shell=False`.
- Capture scope must be derived from validated fields, not raw user-provided
  filters.
- Evidence directories must use restrictive permissions.
- Failures after case directory creation should still produce a manifest and
  hash inventory whenever possible.
- TShark analysis failures must not erase or invalidate a successful packet
  capture.
- Documentation must not encourage broad production capture without review.

## Example Future File Layout

```text
docs/
├── independent-implementation.md
├── lab-real-capture.md
├── mvp-ink-vault.md
└── operations/
    ├── adapter-contracts.md
    ├── event-normalization.md
    ├── evidence-review-checklist.md
    └── production-readiness.md
```

## Open Questions

- Which upstream telemetry source should be normalized first: Zeek, Falco, or
  Wazuh alerts?
- Should EnterOcto define a stable event schema before adding more adapters?
- Should production examples stay in this repository, or live in a separate
  deployment repository later?
- What minimum evidence retention metadata is required for the first operator
  review workflow?
- Which parts should remain reference implementation versus productized
  modules?
