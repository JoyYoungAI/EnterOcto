# EnterOcto Repository and License Model

## Decision

Use a small, license-separated repository model rather than placing every
integration in one repository.

## Repository 1 — EnterOcto

**Proposed URL**

    https://github.com/JoyYoungAI/EnterOcto

**License**

    Apache-2.0

**Purpose**

The main product family, shared schemas, investigation logic, evidence
orchestration, documentation, original Zeek integrations, original Falco
integrations, tests, examples, and external-tool adapters.

**Allowed content**

- EnterOcto-authored source code
- evidence and timeline schemas
- CLI wrappers that invoke separately installed tools
- original Zeek scripts written for EnterOcto
- original Falco rules written for EnterOcto
- product documentation and architecture
- integration interfaces and sample configuration
- test fixtures that contain no sensitive or upstream-copyrighted content

**Do not place here without a license review**

- copied or adapted Wazuh decoders and rules
- Wazuh source code or bundled Wazuh binaries
- Wireshark or TShark source code or binaries
- third-party files whose notices were removed
- a single executable linked against GPLv2 components

## Repository 2 — EnterOcto-Wazuh

**Proposed URL**

    https://github.com/JoyYoungAI/EnterOcto-Wazuh

**License**

    GPL-2.0-only

**Purpose**

The Wazuh-native integration pack.

**Expected content**

- Wazuh decoders
- Wazuh correlation rules
- Wazuh Active Response scripts that are distributed as part of the Wazuh pack
- installation instructions specific to Wazuh
- test events and rule validation
- attribution and upstream notices

**Required files**

- `LICENSE` containing GPL version 2
- `README.md`
- `NOTICE` or attribution file where applicable
- `THIRD_PARTY_NOTICES.md`
- SPDX headers on original source and configuration files where practical

## External tools that remain separate

The following tools should be installed separately and should not be included
in EnterOcto release archives by default:

- Zeek
- Falco
- Wazuh
- Wireshark
- TShark
- Dumpcap

EnterOcto Core communicates with them through logs, JSON, APIs, sockets, files,
pipes, or command-line execution.

## Optional future repositories

Do not create these until their scope is large enough to justify maintenance:

| Repository | Suggested license | Purpose |
|---|---|---|
| `EnterOcto-Detection-Packs` | Apache-2.0, with per-file exceptions | Vendor-neutral Zeek/Falco/Sysmon detection content |
| `EnterOcto-Docs` | Apache-2.0 or CC BY 4.0 | Long-form documentation and website |
| `EnterOcto-Lab` | Apache-2.0 | Safe simulation and testing environment |

## Recommended organization layout

```text
JoyYoungAI/
├── EnterOcto                 Apache-2.0
└── EnterOcto-Wazuh           GPL-2.0-only
```

Start with only these two repositories. Additional repositories should be
created only when independent releases, maintainers, or license boundaries
make them necessary.

## Release rule

The main `EnterOcto` release must not silently bundle GPLv2 binaries or
Wazuh-owned rules. If a future installer or container image redistributes them,
that distribution requires a fresh license-compliance review, complete notices,
and any required corresponding source-code offer.

## File-level licensing

Use SPDX identifiers where practical.

For EnterOcto Core files:

```text
SPDX-License-Identifier: Apache-2.0
```

For EnterOcto-Wazuh files:

```text
SPDX-License-Identifier: GPL-2.0-only
```

For adapted third-party files, keep the upstream copyright and license header,
add a clear modification notice, and do not replace the upstream license with
the repository's default license.

This document is an engineering compliance plan and is not legal advice.
