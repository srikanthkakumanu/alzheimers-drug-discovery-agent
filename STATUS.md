# Project status

Updated **2026-11-09**. This file is the single source of truth for project phase; other documents link here instead of restating it.

| Area | State |
| --- | --- |
| Phase | **Design package complete; awaiting owner review.** No application implementation authorized. |
| Active task | [Owner review](TASK.md) |
| Decisions | ADR-001–010 **proposed**; ADR-011–020 (technology) **accepted** ([register](DECISIONS.md)) |
| Technology stack | **Selected 2026-11-09:** Python 3.12 + uv, Pydantic v2, strict typing (mypy), Typer CLI, LangGraph, OpenAI, SQLite + FTS5, LangSmith, Docker ([ADR-011–ADR-020](docs/architecture/tech-stack.md)). Open: exact model IDs, budget values |
| Application code | None. Repository tooling (validator, 53 tests, Stop hook) rewritten 2026-11-09; offline checks only. |
| Live integrations | None; [integration inventory](config/mcp.json) is disabled |
| Latest documentation pass | Gap fixes: application, prompt, and testing design; ADR-011–020; literature 021–023 ([review log](docs/review-log.md)) |
| Known gaps | OpenAI model IDs and budgets (owner); no LICENSE chosen; EMA guidance unverified; portfolio has no non-Tau comparator candidates (confirm intent) |

## Demonstration scenario (separate from project progress)
**SYNTHETIC DEMONSTRATION:** 15 fictional candidates, 20 experiment records, 12 fictional campaign periods, plus 23 real publications summarized at abstract level.

| Group | Candidates | Meaning |
| --- | --- | --- |
| Follow-up | A (72), G (66) | Next evidence: identity, measured free CNS exposure, direct engagement |
| Blocked | C (artifact), D (hERG signal), N (replication failure; earlier 72 is disputed history) | Hard block; score cannot override |
| Hold / deprioritized | B, E, H, I, J, K, L / M | Specific gaps in each record |
| Provisional | F (invalid assay), O (untested slot) | No valid ratings |

No candidate is approved or promoted. Scores are qualitative illustrations. Detail: [candidate index](molecules/README.md).
