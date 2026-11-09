# Goals and success criteria

All targets are **proposals for owner review**; none has been measured. Evaluation method: [evaluation plan](docs/delivery/evaluation-plan.md).

## Product goals (future system)
| ID | Goal | Proposed success signal | Traces to |
| --- | --- | --- | --- |
| G-1 | Trustworthy evidence synthesis | Zero fabricated citations and zero unlabeled synthetic claims in the evaluation set | FR-02, FR-03 |
| G-2 | Uncertainty stays visible | Every null rating, failed gate, and disputed score in the evaluation set is reported | FR-04, FR-05 |
| G-3 | Decisions stay human | Zero generated approvals or implied study authorizations | FR-08, ADR-006 |
| G-4 | Useful next step | Reviewers rate the proposed next study as decision-relevant in most cases (threshold set by owner) | FR-06 |
| G-5 | Bounded cost | Each run stays within the owner-set token/cost budget, or returns an explicit partial result | NFR-04 |
| G-6 | Traceability | Every material conclusion links to record IDs and a decision owner | NFR-06 |

## Design-phase exit criteria
| Criterion | Evidence |
| --- | --- |
| Scope agreed | Owner disposition on [BRD](docs/product/brd.md) |
| Material decisions resolved | ADRs accepted or rejected in [DECISIONS.md](DECISIONS.md) |
| Stack and budget chosen | Stack recorded ([TD-01–TD-10](docs/architecture/tech-stack.md)); budget still open |
| First slice approved | [implementation plan](docs/delivery/implementation-plan.md) |
| Repository consistent | `python3 scripts/validate_repository.py` passes |

## Explicit non-goals
Autonomous experimentation, patient or dosing recommendations, regulatory submissions, claims of discovery success, and measured productivity or cost savings without evaluation data.
