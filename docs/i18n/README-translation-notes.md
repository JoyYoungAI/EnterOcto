# README Translation Notes

This file defines the Taiwan Traditional Chinese terminology used by
`README.zh-TW.md`. It is a maintenance aid for keeping the English and
Traditional Chinese README files aligned.

## Locale

- Language: Traditional Chinese
- Region: Taiwan
- File suffix: `zh-TW`
- Tone: professional, precise, governance-oriented

## Source of Truth

`README.md` is the canonical source for project scope, licensing, security
boundaries, and implementation status. `README.zh-TW.md` should track it as
closely as practical.

If the English and Traditional Chinese versions disagree, treat the English
version as authoritative and open an issue or pull request to synchronize the
translation.

## Product Tone

Prefer wording around visibility, governance, evidence, review, and controlled
response. Avoid framing EnterOcto as fighting, hunting, or attacking a named
opponent.

Preferred concepts:

- observable
- explainable
- auditable
- governed
- evidence-preserving
- policy-driven

Avoid overly combative wording unless the English source explicitly requires it.

## Term Glossary

| English term | Taiwan Traditional Chinese |
|---|---|
| AI Agent Visibility, Evidence, and Governance | AI Agent 可觀測性、證據保存與治理 |
| unmanaged AI agent activity | 未納管的 AI Agent 活動 |
| visibility | 可觀測性 |
| investigation | 調查 |
| evidence preservation | 證據保存 |
| governed response | 治理式回應 |
| governed response controls | 受治理的回應控制 |
| integration prototype | 整合原型 |
| upstream projects | 上游專案 |
| official deployment guidance | 官方部署指南 |
| evidence manifest | 證據 manifest |
| manifest | manifest |
| hash inventory | 雜湊清單 |
| policy | policy |
| dry-run | dry-run |
| packet capture | 封包擷取 |
| bounded packet capture | 有界限的封包擷取 |
| telemetry | 遙測資料 |
| runtime event | runtime 事件 |
| correlation | 關聯 |
| risk scoring | 風險評分 |
| evidence capsule | 證據膠囊 |
| operator | 操作者 |
| analyst | 分析人員 |
| Active Response | Active Response |
| least privilege | 最小權限 |
| retention | 保存期限 |
| redaction | 遮罩 |
| chain of custody | 保管鏈 |

## Module Names

Do not translate EnterOcto module names. Explain their meanings in Chinese
when helpful.

| Name | Translation note |
|---|---|
| EnterOcto Trace | Keep as-is; describe as investigation and runtime tracing. |
| EnterOcto Ink | Keep as-is; describe as targeted evidence capture. |
| EnterOcto Vault | Keep as-is; describe as evidence retention. |
| EnterOcto Grip | Keep as-is; describe as future governed response. |

## Tool Names

Do not translate upstream project or executable names:

- Zeek
- Falco
- Wazuh
- Wireshark
- TShark
- Dumpcap
- Sysmon
- ETW
- Microsoft Defender

## Style Rules

- Use `AI Agent` instead of translating it as an ordinary Chinese noun.
- Keep repository names, file paths, commands, schema names, and licenses in
  their original form.
- Prefer `上游專案` over `上游項目`.
- Prefer `整合` over `集成`.
- Prefer `部署` over `佈署`.
- Prefer `設定` for configuration unless referring to a specific file named
  `config`.
- Preserve warning callouts and security caveats.
- Do not soften legal, licensing, or security constraints.
