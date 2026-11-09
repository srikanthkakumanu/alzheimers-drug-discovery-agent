# Project status

Updated **2026-11-09**. This file is the single source of truth for project phase; other documents link here instead of restating it.

| Area | State |
| --- | --- |
| Phase | **Design package complete; awaiting owner review.** No application implementation authorized. |
| Active task | [Owner review](TASK.md) |
| Decisions | 10 ADRs, all **proposed** ([register](DECISIONS.md)) |
| Open technology choices | Interface, language, coordinator, LLM provider/model, storage, retrieval, deployment ([options](docs/architecture/tech-stack.md)) |
| Application code | None. Existing Python validator, tests, and Stop hook are offline repository checks only. |
| Live integrations | None; [integration inventory](config/mcp.json) is disabled |
| Latest documentation pass | Layered restructure and content consolidation ([review log](docs/review-log.md)) |

## Demonstration scenario (separate from project progress)
**SYNTHETIC DEMONSTRATION:** 15 fictional candidates, 20 experiment records, 12 fictional campaign periods, plus 20 real publications summarized at abstract level.

| Group | Candidates | Meaning |
| --- | --- | --- |
| Follow-up | A (72), G (66) | Next evidence: identity, measured free CNS exposure, direct engagement |
| Blocked | C (artifact), D (hERG signal), N (replication failure; earlier 72 is disputed history) | Hard block; score cannot override |
| Hold / deprioritized | B, E, H, I, J, K, L / M | Specific gaps in each record |
| Provisional | F (invalid assay), O (untested slot) | No valid ratings |

No candidate is approved or promoted. Scores are qualitative illustrations. Detail: [candidate index](molecules/README.md).
