# Security Policy

## Project status

EnterOcto is currently an early prototype. No release is considered production
ready, and no version is currently covered by a long-term security support
commitment.

Security fixes will be applied to the default branch when maintainers confirm
that a reported issue affects the project.

## Reporting a vulnerability

Please do **not** open a public issue for a suspected vulnerability.

Use GitHub's private vulnerability reporting feature for this repository when
it is available:

1. Open the repository's **Security** tab.
2. Select **Advisories**.
3. Choose **Report a vulnerability**.
4. Include the affected file, revision, impact, reproduction steps, and a safe
   proof of concept.

If private vulnerability reporting is not available, contact JoyYoungAI
through the company's official contact channel and clearly identify the report
as an **EnterOcto security vulnerability**. Do not send customer packet
captures, production credentials, private keys, access tokens, or personal data
unless a secure transfer method has been agreed upon.

## Information to include

A useful report should contain:

- affected commit, tag, or file;
- operating system and relevant tool versions;
- attack prerequisites and required privileges;
- impact on confidentiality, integrity, or availability;
- reproducible steps using synthetic data;
- whether packet capture, Active Response, or elevated privileges are involved;
- suggested mitigation, when known.

## Sensitive evidence

EnterOcto may process packet captures, command lines, file paths, host details,
identities, credentials, and tokens.

Before sharing evidence:

- remove or replace secrets;
- use synthetic traffic whenever possible;
- minimize packet captures to the smallest reproducible sample;
- remove customer and employee identifiers;
- document any remaining sensitive fields;
- use an agreed encrypted transfer channel.

Never attach production PCAP/PCAPNG files to a public GitHub issue.

## Safe testing

Only test EnterOcto on systems and networks that you own or are explicitly
authorized to assess.

Do not run unreviewed capture or response code with unrestricted root
privileges. Keep capture interfaces, destinations, duration, file size, output
paths, and retention limits allowlisted.

## Response process

Maintainers will make a best effort to:

1. confirm receipt of a complete report;
2. reproduce and assess the issue;
3. coordinate a fix and disclosure timeline;
4. credit the reporter when requested and appropriate.

Response times are targets, not a service-level agreement.

## Scope

Security issues include, but are not limited to:

- command or argument injection;
- path traversal or unsafe file permissions;
- privilege escalation;
- capture-filter bypass;
- unbounded packet capture or disk exhaustion;
- leakage of credentials, tokens, or sensitive evidence;
- unsafe Active Response behavior;
- evidence tampering or incorrect integrity metadata;
- dependency or packaging issues that cross documented license boundaries.

General feature requests and non-sensitive bugs may be reported through public
issues.

## Disclosure

Please allow maintainers a reasonable opportunity to investigate and remediate
confirmed vulnerabilities before public disclosure.

This policy does not authorize testing against third-party systems or upstream
projects.
