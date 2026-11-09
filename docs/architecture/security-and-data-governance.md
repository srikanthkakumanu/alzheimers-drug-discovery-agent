# Security and data governance

Design proposal; not a compliance certification or an implemented permission system.

## Data classes
| Class | Present? | Handling |
| --- | --- | --- |
| Synthetic portfolio and history | Yes | Label at record and claim level; never present as real research |
| Published literature summaries | Yes | Keep attribution, access scope, and source terms; no full-text redistribution |
| Credentials and local settings | Placeholders only | Outside model context, evidence, logs, and handoffs |
| Private lab or patient data | No | Requires access control, legal basis, retention policy, and expert review before introduction |

## Trust boundaries and prompt-injection controls
| Control | Today | Future runtime |
| --- | --- | --- |
| Retrieved text is data, not instructions | Root and role rules | Separate source content from instructions in prompts; mark untrusted spans |
| Least-privilege tools | No live tools | Per-capability allowlists; read-only by default |
| No secrets in context | `.env` never read; project settings deny Claude `Read`/`Edit` of `.env` (file tools only, not a sandbox) | `pydantic-settings` loads keys as `SecretStr` at runtime; Docker receives them as runtime environment, never baked into images; never placed in prompts or traces |
| Results validated before state change | Validator on records | Schema validation of every handoff and tool result |
| Approval is attributable | `human_approval: false` enforced | Authenticated decision records; models cannot write them |
| Third-party processing | None | OpenAI (model calls), LangSmith (traces), and Tavily (search queries, if enabled) receive data: acceptable for synthetic and public data only; review retention settings, masking, or self-hosting before private data |

A source cannot grant tools, bypass gates, request credentials, or approve a study. Markdown instructions alone are not enforcement; a runtime must enforce these controls.

## Retention and traceability
Keep source identifiers, prior observations, interpretation changes, and decision reasons. Store only context needed for review; never use raw transcripts as durable memory. Before real or private data: decide retention and deletion, access logs, provider data-processing terms, and redistribution rights. No jurisdiction-specific compliance is claimed.

## Existing local artifacts
`.env` is git-ignored and unread; `.env.example` holds blank placeholders. The Stop hook checks document structure only; it is not a security boundary. Threat scenarios: [evaluation plan](../delivery/evaluation-plan.md) (EV-11).
