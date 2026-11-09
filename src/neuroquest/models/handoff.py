"""Structured LLM outputs (agent-design.md). Strict: every field required, no extras.

Their JSON Schema (with field descriptions) is sent to the model, and every reply is re-validated.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Provenance = Literal["synthetic", "published", "inference", "proposal", "unknown"]
RecommendedDisposition = Literal["follow-up", "hold", "blocked", "deprioritized"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Claim(StrictModel):
    statement: str = Field(
        description="What the cited experiment observed for this candidate (assay and result), "
        "e.g. 'Reduced Tau seeding in the cellular assay'. Never 'has safety' or 'has efficacy'."
    )
    provenance: Provenance
    record_ids: list[str] = Field(description="Experiment or paper IDs exactly as given in the evidence.")


class CandidateReview(StrictModel):
    candidate_id: str
    supported_claims: list[Claim] = Field(
        description="Observations backed by a completed, valid experiment. Must not assert that a gate passes."
    )
    disputed_claims: list[Claim] = Field(
        description="Observations contradicted by replication, controls, or disputed history."
    )
    missing_evidence: list[str] = Field(
        description="Each gate the assessment marks unknown, with what evidence would resolve it. "
        "A topic listed here must not also appear as a supported claim."
    )
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
