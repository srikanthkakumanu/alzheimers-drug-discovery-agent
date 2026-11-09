---
{"id":"candidate-N","provenance":"synthetic","target":"Tau","modality":"small-molecule hypothesis","disposition":"blocked","scores":{"efficacy":null,"safety":3,"bbb":4,"manufacturing":3},"weighted_score":null,"score_status":"provisional","hard_blocks":["replication_failure"],"gates":{"identity":"unknown","orthogonal_activity":"pass","replication":"fail","cns_exposure_engagement":"unknown","safety":"unknown","manufacturing":"unknown"},"human_approval":false,"experiment_ids":["EXP-003","EXP-005","EXP-007","EXP-008","EXP-009","EXP-010","EXP-011","EXP-012","EXP-013","EXP-014"],"literature_ids":["paper-007","paper-010","paper-019"],"rating_evidence":{"efficacy":["EXP-014"],"safety":["EXP-010","EXP-011"],"bbb":["EXP-009"],"manufacturing":["EXP-013"]},"score_history":[{"weighted_score":72.0,"scores":{"efficacy":4,"safety":3,"bbb":4,"manufacturing":3},"basis":["EXP-005","EXP-007","EXP-008"],"status":"disputed","challenged_by":"EXP-014","use":"historical illustration only; not current ranking"}]}
---

# Candidate N — Replication-conflict example

**SYNTHETIC DEMONSTRATION** — fictional profile; no structure, synthesized material, or real measurement exists. Hypothesis: reduce pathological Tau aggregation/seeding; binding and mechanism unproven.

| Disposition | Current score | Hard blocks | Human approval |
| --- | --- | --- | --- |
| **blocked** | unknown (missing or disputed rating) | replication_failure | no |

## Snapshot
Promising first-site results fail to reproduce at the second fictional site. Its earlier 72/100 score is retained only as disputed history; current efficacy and total are unknown.

**Score history (not current):** 72/100 from [EXP-005](../experiments/EXP-005.md), [EXP-007](../experiments/EXP-007.md), [EXP-008](../experiments/EXP-008.md); status **disputed**, challenged by [EXP-014](../experiments/EXP-014.md). Use for audit only, never for ranking.

## Ratings (0–5, higher is better)
| Dimension | Rating | Rating evidence |
| --- | --- | --- |
| Efficacy | null | [EXP-014](../experiments/EXP-014.md) |
| Safety | 3 | [EXP-010](../experiments/EXP-010.md), [EXP-011](../experiments/EXP-011.md) |
| BBB / CNS transport | 4 | [EXP-009](../experiments/EXP-009.md) |
| Developability (manufacturing) | 3 | [EXP-013](../experiments/EXP-013.md) |

Current efficacy is null because EXP-014 conflicts with EXP-005/007/008. The earlier efficacy rating 4 remains in score_history, not the current score. Safety 3: EXP-010/011; BBB 4: EXP-009; manufacturing 3: EXP-013.

Gates: identity **unknown** · orthogonal_activity **pass** · replication **fail** · cns_exposure_engagement **unknown** · safety **unknown** · manufacturing **unknown**.

Context-only records (linked, not rating evidence): [EXP-003](../experiments/EXP-003.md), [EXP-012](../experiments/EXP-012.md).

## Next action
Quarantine the efficacy claim and investigate the conflict; a high score cannot override replication failure.

Background literature (does not report this candidate): [paper-007](../literature/paper-007.md), [paper-010](../literature/paper-010.md), [paper-019](../literature/paper-019.md). Rules: [scoring contract](../config/scoring-model.json) · [candidate index](README.md).
