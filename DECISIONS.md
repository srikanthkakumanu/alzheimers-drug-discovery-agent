# Decision register

All ADRs are **proposed** pending owner review. Load only the record you need. Conventions (status values, supersession): [adr/README.md](adr/README.md).

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

## Decisions not yet framed as ADRs
Interface, application language, coordinator, LLM provider and model tiers, persistence, retrieval, deployment, and run budget. Options and criteria: [tech-stack.md](docs/architecture/tech-stack.md). Each choice becomes a new ADR (ADR-011 onward) when the owner decides.
