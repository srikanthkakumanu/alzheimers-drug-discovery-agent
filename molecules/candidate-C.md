---
{"id":"candidate-C","provenance":"synthetic","target":"Tau","modality":"small-molecule hypothesis","disposition":"blocked","scores":{"efficacy":0,"safety":null,"bbb":null,"manufacturing":3},"weighted_score":null,"score_status":"provisional","hard_blocks":["assay_artifact"],"gates":{"identity":"unknown","orthogonal_activity":"fail","replication":"unknown","cns_exposure_engagement":"unknown","safety":"unknown","manufacturing":"unknown"},"human_approval":false,"experiment_ids":["EXP-001","EXP-004","EXP-006","EXP-013"],"literature_ids":["paper-019"],"rating_evidence":{"efficacy":["EXP-004","EXP-006"],"safety":[],"bbb":[],"manufacturing":["EXP-013"]}}
---

# Candidate C — Optical artifact control

**SYNTHETIC DEMONSTRATION** — fictional profile; no structure, synthesized material, or real measurement exists. Hypothesis: reduce pathological Tau aggregation/seeding; binding and mechanism unproven.

| Disposition | Current score | Hard blocks | Human approval |
| --- | --- | --- | --- |
| **blocked** | unknown (missing or disputed rating) | assay_artifact | no |

## Snapshot
The primary screen signal disappears in the orthogonal readout and interferes with the dye.

## Ratings (0–5, higher is better)
| Dimension | Rating | Rating evidence |
| --- | --- | --- |
| Efficacy | 0 | [EXP-004](../experiments/EXP-004.md), [EXP-006](../experiments/EXP-006.md) |
| Safety | null | — |
| BBB / CNS transport | null | — |
| Developability (manufacturing) | 3 | [EXP-013](../experiments/EXP-013.md) |

Efficacy 0: EXP-004/006 artifact; safety and BBB are null because measurements are missing; manufacturing 3: EXP-013.

Gates: identity **unknown** · orthogonal_activity **fail** · replication **unknown** · cns_exposure_engagement **unknown** · safety **unknown** · manufacturing **unknown**.

Context-only records (linked, not rating evidence): [EXP-001](../experiments/EXP-001.md).

## Next action
Retain as an artifact case; reopen only with new independent non-optical evidence.

Background literature (does not report this candidate): [paper-019](../literature/paper-019.md). Rules: [scoring contract](../config/scoring-model.json) · [candidate index](README.md).
