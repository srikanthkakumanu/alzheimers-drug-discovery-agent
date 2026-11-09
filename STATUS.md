# Project status

Updated **2026-11-09**. This file is the single source of truth for project phase; other documents link here instead of restating it.

| Area | State |
| --- | --- |
| Phase | **Implementation — first slice built** (reviewer → portfolio → human decision). Awaiting a first live run on low-cost providers (Groq, Google Gemini; [ADR-022](adr/ADR-022.md)). |
| Active task | [First live run and evaluation](TASK.md) |
| Decisions | All ADRs **accepted** 2026-11-09; ADR-012 superseded by ADR-021 (Python 3.13); ADR-015 superseded by ADR-022 (low-cost providers) ([register](DECISIONS.md)) |
| Technology stack | Python 3.13 + uv, Pydantic v2, `mypy --strict`, Typer CLI, LangGraph, `openai` SDK against Groq / Google Gemini / Mistral, SQLite, LangSmith, Docker ([tech-stack](docs/architecture/tech-stack.md)) |
| Application | `src/neuroquest`: CLI `review`/`decide`/`runs`/`show`/`validate`; deterministic scoring and gate guard; $0.10 per-run cap; 40 offline tests; Docker image builds |
| Repository checks | Validator + 53 tests; Stop hook; CI runs both plus lint, types, offline tests, image build |
| Not built yet | Researcher, planner, regulatory nodes; FTS5 search; `evidence`/`plan` commands; live evaluation results |
| Live integrations | Groq, Google Gemini, Mistral (OpenAI optional) and LangSmith in the app (keys from `.env`); research connectors (PubMed, Tavily, …) disabled |
| Known gaps | model IDs must be copied into `.env` and provider prices verified; EMA guidance unverified; portfolio is Tau-only (confirm) |

## Demonstration scenario (separate from project progress)
**SYNTHETIC DEMONSTRATION:** 15 fictional candidates, 20 experiment records, 12 fictional campaign periods, plus 23 real publications summarized at abstract level.

| Group | Candidates | Meaning |
| --- | --- | --- |
| Follow-up | A (72), G (66) | Next evidence: identity, measured free CNS exposure, direct engagement |
| Blocked | C (artifact), D (hERG signal), N (replication failure; earlier 72 is disputed history) | Hard block; score cannot override |
| Hold / deprioritized | B, E, H, I, J, K, L / M | Specific gaps in each record |
| Provisional | F (invalid assay), O (untested slot) | No valid ratings |

No candidate is approved or promoted. Scores are qualitative illustrations. Detail: [candidate index](molecules/README.md).
