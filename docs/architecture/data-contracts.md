# Data contracts

Field-level contracts for repository records and proposed application records. Frontmatter uses JSON (a YAML subset) so the dependency-free validator can parse it. Decision: [ADR-002](../../adr/ADR-002.md), [ADR-005](../../adr/ADR-005.md).

## Candidate (`molecules/candidate-X.md`)
| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | Equals filename |
| `provenance` | `"synthetic"` | Body shows **SYNTHETIC DEMONSTRATION** |
| `disposition` | enum | follow-up · hold · blocked · provisional · deprioritized · promoted ([glossary](../glossary.md)) |
| `scores` | {efficacy, safety, bbb, manufacturing} | Each 0–5 or `null` |
| `weighted_score` | number \| null | Formula in [scoring contract](../../config/scoring-model.json); `null` if any rating is `null` |
| `score_status` | `"provisional"` | Required when total is `null` |
| `hard_blocks` | string[] | Non-empty ⇒ `blocked` |
| `gates` | six keys → pass/fail/unknown | Any `fail` ⇒ `blocked` |
| `human_approval` | boolean | `false` throughout the demonstration |
| `experiment_ids`, `literature_ids` | string[] | Experiment links must be reciprocal |
| `rating_evidence` | dimension → experiment IDs | Completed experiments that measured this candidate (validator-enforced for non-null ratings) |
| `score_history` | optional list | `{weighted_score, scores, basis, status, challenged_by, use}`; never ranked |

## Experiment (`experiments/EXP-NNN.md`)
| Field | Rule |
| --- | --- |
| `id`, `provenance: "synthetic"` | As above |
| `status` | completed · invalid · proposed (proposed body contains `No results.`) |
| `campaign_period` | 1–12, fictional |
| `candidate_ids` | Linked candidates (reciprocal) |
| `measured_candidate_ids` | Subset with a usable observation |
| `literature_ids` | Background only |
| `raw_data_available` | `false` |

## Literature (`literature/paper-NNN.md`)
`id`, `provenance: "published"`, `pmid` (digits, unique), `doi`, `year`, `evidence_type`, `review_scope: "indexed metadata and abstract only"`, `verified_on` (ISO date), `tags`. Body shows **PUBLISHED EVIDENCE** with PubMed and DOI links matching the frontmatter.

## Campaign period (`memory/month-NN.md`) and ADR (`adr/ADR-NNN.md`)
Period: `id`, `provenance: "synthetic"`, `campaign_period`, `calendar_mapping: null`. ADR: `id`, `title`, `status` (proposed · accepted · rejected · deprecated · superseded), `decision_type`, `recorded_on`; `reviewed_on` required once not proposed; six standard sections.

## Semantics
- **Current vs historical:** current fields hold only evidence accepted for current comparison. When a material conflict appears, set the rating to `null` and preserve the old value in `score_history` with its basis and challenger (candidate N).
- **Gates:** `pass` = criterion met within the declared scenario; `fail` = material failure supported; `unknown` = missing, invalid, or ambiguous. Passing an in-scenario gate is not proof of real identity or clinical readiness.
- **Unknown vs zero:** `null` means not known; `0` means evidence of the worst anchor (e.g. C’s efficacy artifact).

## Proposed application records
| Record | Fields |
| --- | --- |
| Run | `run_id`, question, scope, record IDs + versions, step transitions, tool calls, model and prompt versions, token usage, budget state, final status |
| Human decision | `decision_id`, packet version, evidence versions, disposition, accountable actor (authenticated), timestamp, reason |

A model must never generate the actor or timestamp of a human decision. Run, checkpoint, and decision records live in SQLite (ADR-016); authentication is decided with the deployment model.

## Change control
Keep primary observations intact when interpretation changes. Distinguish source date, verification date, fictional period, and real review date. Never backdate studies or treat an archive entry as proof that work occurred.

## Implementation models (Pydantic v2, strict typing — ADR-013)
Each contract above becomes one Pydantic model; the validator’s rules become model validators so the CLI, graph, and checks share one definition.

| Model | Key types and validators |
| --- | --- |
| `Candidate` | `Rating = Annotated[int, Field(ge=0, le=5)] \| None`; `GateState = Literal["pass","fail","unknown"]`; `Disposition` literal; validators: total matches formula, any `fail`/hard block ⇒ `blocked`, null rating ⇒ provisional |
| `Experiment` | `Status` literal; validator: `proposed` has no measurements; `measured_candidate_ids ⊆ candidate_ids` |
| `Paper` | `pmid: str` (digits), `doi` pattern, `verified_on: date` |
| `CampaignPeriod`, `ADR` | `calendar_mapping: None`; `status` literal |
| `ScoringModel` | Weights sum to 100; six required gates; loaded from `config/scoring-model.json` |
| `Handoff`, `ToolResult` | As in [agent design](agent-design.md) and [tools](tools-and-integrations.md) |
| `RunRecord`, `HumanDecision` | Token and cost usage from provider data; actor from authentication only |
| `Settings` (pydantic-settings) | API keys as `SecretStr`; model IDs per tier; budget values |

Conventions: models are `frozen=True` where records are read-only; `extra="forbid"` on LLM output models so unexpected fields fail validation; IDs use distinct `NewType`s (`CandidateId`, `ExperimentId`, `PaperId`); all code passes `mypy --strict`.
