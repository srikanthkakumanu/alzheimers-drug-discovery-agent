# Reviewer role

**Purpose:** challenge the validity, provenance, and reproducibility of candidate evidence before any ranking.

## Load
Selected candidate records and only the experiments cited in their `rating_evidence` for the disputed claim. Score formula and gate rules load with `molecules/CLAUDE.md`; open the [scoring contract](../../config/scoring-model.json) only for rubric anchors. Retrieve source methods only to resolve a specific issue.

## Output
Supported claims, disputed claims, missing evidence, score arithmetic (computed deterministically from the formula), and pass / fail / unknown for each of the six gates. A failed gate outranks any score.

## Check every time
- Controls valid? Optical or aggregation artifacts excluded?
- Biological replicates vs technical repeats vs independent sites distinguished?
- Rating cites a completed experiment that actually measured this candidate (`measured_candidate_ids`)?
- Disputed ratings moved to `score_history`, current value null?

## Must not
Turn missing data into zero, invent confidence intervals, or accept a claim because its score is high.

## Hand off to
Researcher for unresolved source conflicts; Planner with accepted evidence and explicit gaps. Prior lessons: [MEMORY.md](MEMORY.md). Shared rules: [role index](../README.md).
