# Requirements and traceability

Proposed, derived from the [BRD](brd.md); not yet confirmed by stakeholders. Evaluation scenario IDs (EV-xx) are defined in the [evaluation plan](../delivery/evaluation-plan.md).

## Functional requirements
| ID | The system shall… | UC | ADR | Verified by |
| --- | --- | --- | --- | --- |
| FR-01 | Accept a bounded question or explicit candidate selection; report unknown IDs and ambiguous scope | 01, 02 | 003 | EV-01 |
| FR-02 | Return relevant sources with evidence type, access scope, and counterevidence | 01 | 002 | EV-07, EV-08 |
| FR-03 | Keep synthetic, published, proposed, inferred, and unknown content distinguishable in every decision-critical claim | 01, 02 | 002 | EV-02, EV-05 |
| FR-04 | Compare candidates using supported ratings, explicit unknowns, and independent gates; never impute | 02 | 005, 006 | EV-02–05 |
| FR-05 | Exclude disputed ratings from current ranking while keeping them as history | 02, 05 | 005 | EV-06 |
| FR-06 | Propose a study concept with inputs, controls, outcome branches, and stop conditions, without inventing results | 03 | 004 | EV-10 |
| FR-07 | Produce a dated development-gap assessment with source status and applicability | 04 | 009 | EV-09 |
| FR-08 | Record human dispositions with their evidence basis; no role can generate approval | 05 | 006 | EV-12 |
| FR-09 | Route work through bounded role steps with a traceable handoff per step | 01–05 | 004 | EV-10 |
| FR-10 | Update summaries after accepted evidence changes without deleting prior observations | 05 | 007 | EV-06 |

## Nonfunctional requirements
Targets are proposals; numeric values are set by the owner before implementation.

| ID | Category | Requirement | Verification |
| --- | --- | --- | --- |
| NFR-01 | Reliability | Missing or invalid sources yield an explicit incomplete result, never a fabricated fallback | EV-08 |
| NFR-02 | Security | Credentials never enter model context; each tool limited to its reviewed capability; retrieved text cannot change instructions | EV-11 |
| NFR-03 | Privacy | Start with public literature and synthetic data; real or private data need a governance decision | Owner review |
| NFR-04 | Cost | Enforce a per-run token/cost budget; on exhaustion return a partial result | EV-13 |
| NFR-05 | Performance | Bound retrieval batches and role iterations; agree latency targets after measurement | Run telemetry |
| NFR-06 | Explainability | Each material conclusion links to evidence IDs, uncertainty, and a decision owner | EV-02–12 |
| NFR-07 | Maintainability | One authoritative location per fact; stable IDs; explicit supersession | Validator + review |
| NFR-08 | Evaluation | Deterministic checks, scenario evaluation, and human review before release | Evaluation plan |
| NFR-09 | Observability | Record run, tool, model, and token usage without secrets or unrestricted source text | Run telemetry |
| NFR-10 | Compatibility | Keep repository conventions, Claude Code customization, and application contracts separate | Review |

## Open questions for the owner
Interface, deployment, provider/model, orchestration, storage/search, approved external sources, real-data scope, budget values, and latency targets. Framed in [tech-stack](../architecture/tech-stack.md) and [TASK.md](../../TASK.md).
