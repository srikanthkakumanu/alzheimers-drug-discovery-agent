"""Scoring contract (config/scoring-model.json) and deterministic assessment output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from neuroquest.models.records import (
    DIMENSIONS,
    GATE_NAMES,
    CandidateId,
    Dimension,
    Disposition,
    GateName,
)


class PromotionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    minimum_total: float = Field(ge=0, le=100)
    required_gates: list[GateName]
    all_required_gates_must_pass: bool
    human_approval_required: bool
    hard_blocks_override_score: bool

    @model_validator(mode="after")
    def _all_gates_required(self) -> PromotionPolicy:
        if set(self.required_gates) != set(GATE_NAMES):
            raise ValueError("promotion policy must require all six gates")
        if not (self.all_required_gates_must_pass and self.human_approval_required and self.hard_blocks_override_score):
            raise ValueError("promotion policy must require gates, human approval, and block precedence")
        return self


class ScoringModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    weights: dict[Dimension, float]
    promotion: PromotionPolicy

    @model_validator(mode="after")
    def _weights_valid(self) -> ScoringModel:
        if set(self.weights) != set(DIMENSIONS) or any(w <= 0 for w in self.weights.values()):
            raise ValueError("weights must be positive for all four dimensions")
        if sum(self.weights.values()) != 100:
            raise ValueError("weights must sum to 100")
        return self


class Assessment(BaseModel):
    """Deterministic view of one candidate; produced by code, never by a model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_id: CandidateId
    title: str
    recorded_disposition: Disposition
    recorded_score: float | None
    computed_score: float | None
    score_consistent: bool
    missing_ratings: list[Dimension]
    failed_gates: list[GateName]
    unknown_gates: list[GateName]
    hard_blocks: list[str]
    disputed_history: list[float]
    eligible_for_promotion: bool
    promotion_blockers: list[str]  # reasons promotion is not allowed; distinct from a hard block

    @model_validator(mode="before")
    @classmethod
    def _accept_old_name(cls, data: Any) -> Any:
        """Checkpoints from before 2026-11-10 store this field as "blockers"."""
        if isinstance(data, dict) and "blockers" in data and "promotion_blockers" not in data:
            data = {**data, "promotion_blockers": data["blockers"]}
            del data["blockers"]
        return data

    @property
    def is_blocked(self) -> bool:
        return bool(self.hard_blocks or self.failed_gates)
