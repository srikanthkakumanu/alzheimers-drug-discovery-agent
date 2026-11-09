# Candidate records — rules (auto-loaded in `molecules/`)

All records are **SYNTHETIC DEMONSTRATION** data.
- **Score:** `weighted_score = (40·efficacy + 30·safety + 20·bbb + 10·manufacturing) / 5`, 1 decimal. Any `null` rating ⇒ `null` total, `score_status: provisional`. Never impute. Rubric anchors: [scoring-model.json](../config/scoring-model.json) (open only if needed).
- **Current vs history:** a disputed rating becomes `null`; the old value moves to `score_history` (see candidate-N) and is never ranked.
- **Evidence:** a non-null rating cites, in `rating_evidence`, a completed experiment listing this candidate in `measured_candidate_ids`.
- **Gates:** any `fail` or `hard_blocks` entry ⇒ disposition `blocked`. `human_approval` stays `false`; nothing is `promoted`.
- **Editing:** keep `experiment_ids` reciprocal with experiments’ `candidate_ids`. Update frontmatter, then body table and gate line, then [README.md](README.md) and [STATUS.md](../STATUS.md).
