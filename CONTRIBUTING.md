# Contributing to EnterOcto

Thank you for helping JoyYoungAI build maintainable open-source security
integrations.

EnterOcto combines independently maintained tools through documented
interfaces. Contributions must preserve technical, security, and licensing
boundaries.

## Before contributing

Please review:

- `README.md`
- `SECURITY.md`
- `THIRD_PARTY_NOTICES.md`
- `REPO-SPLIT.md`
- the upstream license of every project touched by the change

Do not submit confidential customer material, production packet captures,
credentials, tokens, private keys, or personal data.

## Repository boundaries

The main `JoyYoungAI/EnterOcto` repository is Apache-2.0.

Suitable contributions include:

- EnterOcto-authored source code;
- schemas and evidence formats;
- wrappers for separately installed command-line tools;
- original Zeek scripts;
- original Falco rules;
- tests, synthetic fixtures, and documentation.

Do not place the following in this repository without an explicit licensing
review:

- copied or adapted Wazuh decoders, rules, or data files;
- Wazuh source code or binaries;
- Wireshark, TShark, or Dumpcap source code or binaries;
- third-party files with removed notices;
- code linked into a single work with GPLv2-only components.

Wazuh-native integration content belongs in the planned
`JoyYoungAI/EnterOcto-Wazuh` repository under GPL-2.0-only.

## Development workflow

1. Create a focused branch.
2. Keep changes small and reviewable.
3. Add or update tests.
4. Update documentation when behavior, security assumptions, or licensing
   boundaries change.
5. Run:

```bash
python3 -m unittest discover -s tests -v
```

6. Open a pull request using a clear title and description.

## Commit certification

Contributors should certify commits using the Developer Certificate of Origin
(DCO) sign-off:

```text
Signed-off-by: Your Name <your-email@example.com>
```

With Git:

```bash
git commit -s -m "feat: describe the change"
```

By signing off, you certify that you have the right to submit the contribution
under the repository's license.

## Source provenance

For every non-trivial contribution, state whether the work is:

- entirely original;
- adapted from another project; or
- generated with assistance from an automated tool.

For adapted material, include:

- upstream project and file;
- upstream revision or tag;
- original license;
- retained copyright and attribution;
- a prominent modification notice;
- the date and nature of the modification.

Do not copy code from a source whose license is unknown or incompatible.

## Security-sensitive changes

Packet capture, evidence handling, and response code require extra review.

Document:

- threat scenario;
- expected telemetry;
- trust boundaries;
- required privileges;
- input validation;
- resource limits and timeouts;
- output permissions;
- false-positive and failure impact;
- rollback behavior;
- test evidence.

Capture filters must be assembled from validated fields. Do not concatenate
untrusted alert data into shell commands.

## Detection contributions

Detection rules should include:

- purpose and threat scenario;
- supported platform and versions;
- example positive event;
- example benign event;
- expected false positives;
- tuning guidance;
- test fixture.

## Test data

Use synthetic data. Remove secrets and identifiers. Keep packet fixtures small,
documented, and legally redistributable.

## Pull request checklist

- [ ] The contribution belongs in this repository.
- [ ] I documented source provenance and applicable licenses.
- [ ] I did not include sensitive or customer data.
- [ ] Tests pass.
- [ ] Security assumptions and privileges are documented.
- [ ] Documentation is updated.
- [ ] Commits include DCO sign-off.

## Code of conduct

Be respectful, technically precise, and constructive. A dedicated code of
conduct may be added as the contributor community grows.
