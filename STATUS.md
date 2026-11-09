# Project status

Updated **2026-11-10**. This file is the single source of truth for project phase; other documents link here instead of restating it.

| Area | State |
| --- | --- |
| Phase | **Implementation — first slice live** (reviewer → portfolio → human decision). First live run on low-cost providers ([ADR-022](adr/ADR-022.md)) passed; owner decision recorded. |
| Active task | [Evaluation report and second-slice scope](TASK.md) |
| Last live run | `run-20261109-190842-19f12d`: A G N, $0.0018 of $0.10, N kept blocked, all cited IDs real; owner decided A/G follow-up, N blocked. Live eval test passed. Earlier run `…190555-c07d1e` (before the reviewer claim fix) left open |
| Evaluation | [First results](docs/delivery/evaluation-results.md): 0 fabricated citations, 0 promotions, 0 gate errors; contradictory claims (EV-02/03) now caught by a deterministic check; EV-10 passes with a one-gate discriminating study; EV-07–09 need the second slice |
| Decisions | All ADRs **accepted** 2026-11-09; ADR-012 superseded by ADR-021 (Python 3.13); ADR-015 superseded by ADR-022 (low-cost providers) ([register](DECISIONS.md)) |
| Technology stack | Python 3.13 + uv, Pydantic v2, `mypy --strict`, Typer CLI, LangGraph, `openai` SDK against Groq / Google Gemini / Mistral, SQLite, LangSmith, Docker ([tech-stack](docs/architecture/tech-stack.md)) |
| Application | `src/neuroquest`: CLI `review`/`decide`/`runs`/`show`/`validate`; deterministic scoring and gate guard; $0.10 per-run cap; 53 offline tests; Docker image builds |
| Repository checks | Validator + 53 tests; Stop hook; CI runs both plus lint, types, offline tests, image build |
| Not built yet | Researcher, planner, regulatory nodes; FTS5 search; `evidence`/`plan` commands; full EV-02–EV-13 report |
| Live integrations | Groq, Google Gemini, Mistral (OpenAI optional) and LangSmith in the app (keys from `.env`); research connectors (PubMed, Tavily, …) disabled |
| Known gaps | Groq free tier unusable for the reviewer and Mistral rate-limited, so both active tiers run on Gemini Flash-Lite; provider prices unverified; EMA guidance unverified; portfolio is Tau-only (confirm) |

## Demonstration scenario (separate from project progress)
**SYNTHETIC DEMONSTRATION:** 15 fictional candidates, 20 experiment records, 12 fictional campaign periods, plus 23 real publications summarized at abstract level.

| Group | Candidates | Meaning |
| --- | --- | --- |
| Follow-up | A (72), G (66) | Next evidence: identity, measured free CNS exposure, direct engagement |
| Blocked | C (artifact), D (hERG signal), N (replication failure; earlier 72 is disputed history) | Hard block; score cannot override |
| Hold / deprioritized | B, E, H, I, J, K, L / M | Specific gaps in each record |
| Provisional | F (invalid assay), O (untested slot) | No valid ratings |

No candidate is approved or promoted. Scores are qualitative illustrations. Detail: [candidate index](molecules/README.md).
