# Third-Party Notices

EnterOcto is licensed under the Apache License 2.0. This file documents the
third-party projects with which EnterOcto is designed to interoperate.

Unless a future release explicitly states otherwise, the main EnterOcto
repository does **not** redistribute third-party binaries or source code from
the projects listed below. Users install and operate those projects separately.

## Dependency and integration policy

EnterOcto Core should communicate with external tools through documented
boundaries such as:

- JSON, logs, syslog, sockets, or APIs
- command-line execution
- pipes and files
- independently installed services

Do not copy third-party source code, rules, decoders, data files, or binaries
into this repository without first reviewing and preserving the applicable
license, copyright, attribution, source-offer, and modification requirements.

## Zeek

- Project: Zeek Network Security Monitor
- Upstream: https://github.com/zeek/zeek
- License: BSD-style three-clause license
- Upstream license: https://github.com/zeek/zeek/blob/master/COPYING
- Intended use: separately installed network telemetry source

Redistribution of Zeek source or binaries requires retention of its copyright,
license conditions, and disclaimer. Project and contributor names may not be
used to endorse derived products without permission.

## Falco

- Project: Falco
- Upstream: https://github.com/falcosecurity/falco
- License: Apache License 2.0
- Upstream license: https://github.com/falcosecurity/falco/blob/master/COPYING
- Intended use: separately installed Linux and container runtime telemetry source

If Falco code or files are copied or modified, preserve the upstream license,
copyright and attribution notices, mark modified files, and preserve any
applicable NOTICE content.

## Wazuh

- Project: Wazuh
- Upstream: https://github.com/wazuh/wazuh
- License: GNU General Public License version 2, with upstream-specific notices
  and exceptions
- Upstream license: https://github.com/wazuh/wazuh/blob/master/LICENSE
- Intended use: separately installed manager, agent, correlation and response platform

Wazuh states that its GPLv2 license applies to source code, decoders, rules and
other included data files unless otherwise specified. Wazuh-specific decoders,
rules, copied data files, or derivative integration content should not be placed
in the Apache-2.0 EnterOcto Core repository.

The recommended location for Wazuh-specific integration content is a separate
repository:

    JoyYoungAI/EnterOcto-Wazuh

That repository should use `GPL-2.0-only`, preserve upstream notices, and
clearly identify original EnterOcto-authored files and any adapted upstream
files.

## Wireshark, TShark and Dumpcap

- Project: Wireshark
- Upstream: https://github.com/wireshark/wireshark
- License: GNU General Public License version 2
- Upstream license: https://github.com/wireshark/wireshark/blob/master/COPYING
- Intended use: independently installed packet-capture executables invoked by CLI

EnterOcto Core should invoke TShark or Dumpcap as external executables and
consume their output. Do not embed, statically link, or copy Wireshark source
code into the Apache-2.0 core repository without a separate licensing review.

Generated PCAP or PCAPNG evidence is incident data. Its handling is governed by
privacy, security, retention, and organizational policy rather than being
automatically relicensed under EnterOcto.

## No endorsement

References to third-party projects are descriptive. EnterOcto is not endorsed
by Zeek, Falco, Wazuh, Wireshark, or their respective maintainers.

## Distribution review

Before publishing a release archive, installer, container image, appliance, or
commercial bundle, create a software bill of materials and review whether the
distribution contains any third-party source code, data files, rules, libraries,
or binaries. If it does, satisfy every applicable upstream license obligation.

This notice is an engineering compliance guide and is not legal advice.
