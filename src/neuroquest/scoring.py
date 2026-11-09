"""Deterministic scoring and gate evaluation. No model calls, ever."""

from __future__ import annotations

from collections.abc import Mapping

from neuroquest.models.records import DIMENSIONS, Candidate, Dimension, Scores
from neuroquest.models.runs import HumanDisposition
from neuroquest.models.scoring import Assessment, ScoringModel


def weighted_score(scores: Scores, weights: Mapping[Dimension, float]) -> float | None:
    """0-100 score, or None when any rating is unknown. Same arithmetic as the validator."""
    if scores.missing:
        return None
    return round(sum(weights[d] * (scores.get(d) or 0.0) / 5 for d in weights), 1)


def assess(candidate: Candidate, scoring: ScoringModel) -> Assessment:
    computed = weighted_score(candidate.scores, scoring.weights)
    failed = candidate.gates.with_state("fail")
    unknown = candidate.gates.with_state("unknown")
    blockers: list[str] = []
    if candidate.hard_blocks:
        blockers.append("hard block: " + ", ".join(candidate.hard_blocks))
    if failed:
        blockers.append("failed gate: " + ", ".join(failed))
    if unknown:
        blockers.append("unknown gate: " + ", ".join(unknown))
    if computed is None:
        blockers.append("score unknown: missing " + ", ".join(candidate.scores.missing))
    elif computed < scoring.promotion.minimum_total:
        blockers.append(f"score {computed} below {scoring.promotion.minimum_total}")
    if not candidate.human_approval:
        blockers.append("no human approval")
    eligible = (
        computed is not None
        and computed >= scoring.promotion.minimum_total
        and not candidate.hard_blocks
        and not failed
        and not unknown
        and candidate.human_approval
    )
    return Assessment(
        candidate_id=candidate.id,
        title=candidate.title,
        recorded_disposition=candidate.disposition,
        recorded_score=candidate.weighted_score,
        computed_score=computed,
        score_consistent=computed == candidate.weighted_score,
        missing_ratings=[d for d in DIMENSIONS if candidate.scores.get(d) is None],
        failed_gates=failed,
        unknown_gates=unknown,
        hard_blocks=list(candidate.hard_blocks),
        disputed_history=[h.weighted_score for h in candidate.score_history if h.status == "disputed"],
        eligible_for_promotion=eligible,
        blockers=blockers,
    )


def allowed_dispositions(assessment: Assessment) -> frozenset[HumanDisposition]:
    """Gates beat scores: a blocked candidate can only stay blocked. Promotion is never offered."""
    if assessment.is_blocked:
        return frozenset({"blocked"})
    return frozenset({"follow-up", "hold", "deprioritized", "blocked"})
