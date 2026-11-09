"""Run, step, usage, and human-decision records persisted in SQLite."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from neuroquest.models.records import CandidateId

RunStatus = Literal["running", "awaiting_human", "closed", "partial", "invalid_input", "failed"]
HumanDisposition = Literal["follow-up", "hold", "blocked", "deprioritized"]


class Usage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    input_tokens: int = Field(default=0, ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )


class HumanDecision(BaseModel):
    """Recorded by a person through the CLI; a model can never create one."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_id: CandidateId
    disposition: HumanDisposition
    actor: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decided_at: datetime


class RunRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    question: str
    candidate_ids: list[CandidateId]
    status: RunStatus
    prompt_version: str | None
    usage: Usage
    cost_usd: float
    budget_usd: float
    packet_markdown: str | None
    created_at: datetime
    closed_at: datetime | None
