# Active task — owner review of the design package

Owner: project owner. Output: an accept / revise / reject disposition for each item below, recorded in the relevant ADR or document. Implementation starts only after a separate explicit request.

## Review sequence
Follow the [review plan](docs/delivery/review-plan.md). Start with [PROJECT.md](PROJECT.md), then [BRD](docs/product/brd.md), [requirements](docs/product/requirements.md), [architecture](docs/architecture/architecture.md), and the [decision register](DECISIONS.md). Use the [documentation index](docs/README.md) for detail; do not load evidence records for design review.

## Decisions required from the owner
| # | Decision | Where it is framed |
| --- | --- | --- |
| 1 | Confirm personas, use cases, and out-of-scope boundaries | [BRD](docs/product/brd.md) |
| 2 | Accept, revise, or reject each proposed ADR | [DECISIONS.md](DECISIONS.md) |
| 3 | Confirm Tau-first demonstration scope | [ADR-001](adr/ADR-001.md) |
| 4 | ~~Select interface, language, coordinator, provider, storage~~ **Done 2026-11-09**; still choose OpenAI model IDs per tier | [tech-stack](docs/architecture/tech-stack.md) |
| 5 | Set a per-run and monthly LLM budget and the exhausted-budget behavior | [cost design](docs/architecture/observability-and-cost.md) |
| 6 | Approve evaluation scenarios and release thresholds | [evaluation plan](docs/delivery/evaluation-plan.md) |
| 7 | Approve the first implementation slice | [implementation plan](docs/delivery/implementation-plan.md) |
| 8 | Decide data scope beyond public literature and synthetic records | [data governance](docs/architecture/security-and-data-governance.md) |

## Done when
- Every row above has a recorded owner disposition.
- Accepted ADRs change status from `proposed` to `accepted` with a review date; rejected ones are retained with reasons.
- [STATUS.md](STATUS.md) reflects the new phase.

Scientific questions about the synthetic scenario (for example the A/G/N comparison) are evaluation cases, not this task.
