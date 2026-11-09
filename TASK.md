# Active task — evaluation report and second-slice scope

Owner: project owner. The first slice ran live on 2026-11-09 ([STATUS.md](STATUS.md)): run `run-20261109-190842-19f12d` stayed within budget, kept N blocked, cited only real record IDs, and the owner recorded A/G follow-up, N blocked. Providers and models: [ADR-022](adr/ADR-022.md).

## Steps
1. Score the closed run's packet against EV-02–EV-13 ([evaluation plan](docs/delivery/evaluation-plan.md)); note any check the live eval test does not yet automate.
2. Decide whether to close or discard the earlier open run `run-20261109-190555-c07d1e` (pre-fix reviewer output).
3. Choose the second-slice scope (decision 6 below) using what the evaluation shows.

## Owner decisions still open
| # | Decision | Where it is framed |
| --- | --- | --- |
| 1 | Verify the paid-tier prices in `.env.example` against each provider's price page | [tech-stack](docs/architecture/tech-stack.md) |
| 2 | Monthly LLM budget (per-run cap is $0.10) | [cost design](docs/architecture/observability-and-cost.md) |
| 3 | Evaluation release thresholds | [evaluation plan](docs/delivery/evaluation-plan.md) |
| 4 | Data scope beyond public literature and synthetic records; whether to enable Tavily | [data governance](docs/architecture/security-and-data-governance.md) |
| 5 | Keep the portfolio Tau-only (no comparator candidates)? | [research strategy](knowledge/research-strategy.md) |
| 6 | Scope of the second slice (researcher/planner/regulatory nodes, FTS5) | [implementation plan](docs/delivery/implementation-plan.md) |

## Done when
EV-02–EV-13 results are recorded with the run ID, and the second-slice scope is chosen. Update [STATUS.md](STATUS.md) afterwards.
