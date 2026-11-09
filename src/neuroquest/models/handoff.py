"""Structured LLM outputs (agent-design.md). Strict: every field required, no extras.

These models are passed to OpenAI Structured Outputs, then re-validated.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

Provenance = Literal["synthetic", "published", "inference", "proposal", "unknown"]
RecommendedDisposition = Literal["follow-up", "hold", "blocked", "deprioritized"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Claim(StrictModel):
    statement: str
    provenance: Provenance
    record_ids: list[str]


class CandidateReview(StrictModel):
    candidate_id: str
    supported_claims: list[Claim]
    disputed_claims: list[Claim]
    missing_evidence: list[str]
    next_action: str


class ReviewHandoff(StrictModel):
    """Reviewer output: evidence quality per candidate."""

    question: str
    reviews: list[CandidateReview]
    uncertainty: list[str]
    next_action: str


class Recommendation(StrictModel):
    candidate_id: str
    recommended_disposition: RecommendedDisposition
    rationale: str
    information_value: str
    next_step: str


class PortfolioPacket(StrictModel):
    """Portfolio output: the recommendation a human decides on."""

    summary: str
    recommendations: list[Recommendation]
    human_decision_required: str
