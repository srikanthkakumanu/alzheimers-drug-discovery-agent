# Decision register

All ADRs are **accepted** (2026-11-09) except ADR-012, **superseded** by ADR-021. Load only the record you need. Conventions (status values, supersession): [adr/README.md](adr/README.md).

| ID | Decision | Type | Key consequence |
| --- | --- | --- | --- |
| [ADR-001](adr/ADR-001.md) | Tau-first research scope | research-scope | Focused scenario; negative Tau trials must stay visible |
| [ADR-002](adr/ADR-002.md) | Evidence provenance and separation of synthetic data | data-architecture | Every claim traceable to published, synthetic, proposed, or unknown |
| [ADR-003](adr/ADR-003.md) | Layered progressive context disclosure | context-architecture | Small default context; directory rules load only when needed |
| [ADR-004](adr/ADR-004.md) | Document-defined roles before automated orchestration | orchestration-architecture | Roles reusable later; no runtime yet |
| [ADR-005](adr/ADR-005.md) | Evidence-backed ratings with explicit uncertainty | decision-model | Missing or disputed ratings leave totals unknown |
| [ADR-006](adr/ADR-006.md) | Human-controlled advancement with independent gates | decision-governance | Failed gate blocks regardless of score |
| [ADR-007](adr/ADR-007.md) | Indexed durable memory and relative scenario history | memory-architecture | Lessons stay small; history loads on demand |
| [ADR-008](adr/ADR-008.md) | Disabled integration inventory and local secret boundaries | integration-architecture | Offline review; connectors added one at a time |
| [ADR-009](adr/ADR-009.md) | Versioned regulatory references and bounded interpretation | evidence-governance | Draft guidance never presented as binding |
| [ADR-010](adr/ADR-010.md) | Offline document validation and bounded hook feedback | development-tooling | Structural checks only; not scientific validation |

## Technology decisions — accepted 2026-11-09
| ID | Decision | Type |
| --- | --- | --- |
| [ADR-011](adr/ADR-011.md) | Typer CLI as the first interface | interface |
| ~~[ADR-012](adr/ADR-012.md)~~ | Python 3.12 with uv and ruff — superseded by ADR-021 | language-and-tooling |
| [ADR-013](adr/ADR-013.md) | Pydantic v2 models and strict typing | data-architecture |
| [ADR-014](adr/ADR-014.md) | LangGraph as the run coordinator | orchestration-architecture |
| ~~[ADR-015](adr/ADR-015.md)~~ | OpenAI as the application LLM provider — superseded by ADR-022 | integration-architecture |
| [ADR-016](adr/ADR-016.md) | Files plus SQLite for storage | data-architecture |
| [ADR-017](adr/ADR-017.md) | Index lookup plus SQLite FTS5 retrieval | retrieval-architecture |
| [ADR-018](adr/ADR-018.md) | LangSmith tracing with pytest evaluation | observability |
| [ADR-019](adr/ADR-019.md) | Docker for packaging and runs | deployment |
| [ADR-020](adr/ADR-020.md) | GitHub Actions quality gates | development-tooling |
| [ADR-021](adr/ADR-021.md) | Python 3.13 runtime with uv and ruff | language-and-tooling |
| [ADR-022](adr/ADR-022.md) | Low-cost LLM providers (Groq, Google, Mistral) via OpenAI-compatible endpoints | integration-architecture |

Still open: verify provider prices, monthly budget ([TASK.md](TASK.md)).
