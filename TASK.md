# Active task — first live run and evaluation

Owner: project owner. The first slice is built and tested offline ([implementation plan](docs/delivery/implementation-plan.md)). Next: run it against OpenAI within the $0.10 per-run cap and judge the packets.

## Steps
1. In `.env`, set `NEUROQUEST_MODEL_ECONOMICAL`, `NEUROQUEST_MODEL_CAPABLE` (escalation is unused in this slice) and `NEUROQUEST_MODEL_PRICES` with current prices for those IDs ([.env.example](.env.example)).
2. Run `uv run neuroquest review A G N`; read the packet; record decisions with `uv run neuroquest decide <run_id> -d A=… -d G=… -d N=blocked --reason "…"`.
3. Run the live evaluation: `uv run pytest -m eval` ([testing strategy](docs/delivery/testing-strategy.md)).
4. Report packet quality against EV-02–EV-13 ([evaluation plan](docs/delivery/evaluation-plan.md)).

## Owner decisions still open
| # | Decision | Where it is framed |
| --- | --- | --- |
| 1 | OpenAI model IDs and prices per tier | [tech-stack](docs/architecture/tech-stack.md) |
| 2 | Monthly LLM budget (per-run cap is $0.10) | [cost design](docs/architecture/observability-and-cost.md) |
| 3 | Evaluation release thresholds | [evaluation plan](docs/delivery/evaluation-plan.md) |
| 4 | Data scope beyond public literature and synthetic records; whether to enable Tavily | [data governance](docs/architecture/security-and-data-governance.md) |
| 5 | Repository license | [README](README.md) |
| 6 | Keep the portfolio Tau-only (no comparator candidates)? | [research strategy](knowledge/research-strategy.md) |
| 7 | Scope of the second slice (researcher/planner/regulatory nodes, FTS5) | [implementation plan](docs/delivery/implementation-plan.md) |

## Done when
A live review of A G N stays within budget, keeps N blocked, cites only real record IDs, and the owner records a decision. Update [STATUS.md](STATUS.md) afterwards.
