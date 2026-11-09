# Active task — first live run and evaluation

Owner: project owner. The first slice is built and tested offline ([implementation plan](docs/delivery/implementation-plan.md)). Next: run it against the low-cost providers ([ADR-022](adr/ADR-022.md): Groq, Google Gemini, Mistral) within the $0.10 per-run cap and judge the packets.

## Steps
1. In `.env`, copy the `NEUROQUEST_MODEL_*` lines from [.env.example](.env.example) (economical `groq:…`, capable `google:…`; escalation is unused in this slice) and confirm `GROQ_API_KEY` and `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) are set.
2. Run `uv run neuroquest review A G N`; read the packet; record decisions with `uv run neuroquest decide <run_id> -d A=… -d G=… -d N=blocked --reason "…"`.
3. Run the live evaluation: `uv run pytest -m eval` ([testing strategy](docs/delivery/testing-strategy.md)).
4. Report packet quality against EV-02–EV-13 ([evaluation plan](docs/delivery/evaluation-plan.md)).

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
A live review of A G N stays within budget, keeps N blocked, cites only real record IDs, and the owner records a decision. Update [STATUS.md](STATUS.md) afterwards.
