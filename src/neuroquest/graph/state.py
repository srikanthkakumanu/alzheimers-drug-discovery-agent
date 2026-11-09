"""Graph state. Values are JSON-compatible because the checkpointer persists them;
nodes convert to and from Pydantic models at the boundary.
"""

from __future__ import annotations

from typing import Any, TypedDict

from pydantic import TypeAdapter

from neuroquest.models.handoff import PortfolioPacket, ReviewHandoff
from neuroquest.models.runs import HumanDecision
from neuroquest.models.scoring import Assessment


class RunState(TypedDict, total=False):
    run_id: str
    question: str
    candidate_ids: list[str]
    assessments: list[dict[str, Any]]
    evidence_ids: list[str]
    review: dict[str, Any] | None
    portfolio: dict[str, Any] | None
    notes: list[str]
    prompt_versions: list[str]
    status: str
    decisions: list[dict[str, Any]]


_ASSESSMENTS = TypeAdapter(list[Assessment])
_DECISIONS = TypeAdapter(list[HumanDecision])


def assessments_of(state: RunState) -> list[Assessment]:
    return _ASSESSMENTS.validate_python(state.get("assessments", []))


def review_of(state: RunState) -> ReviewHandoff | None:
    data = state.get("review")
    return ReviewHandoff.model_validate(data) if data else None


def portfolio_of(state: RunState) -> PortfolioPacket | None:
    data = state.get("portfolio")
    return PortfolioPacket.model_validate(data) if data else None


def decisions_of(state: RunState) -> list[HumanDecision]:
    return _DECISIONS.validate_python(state.get("decisions", []))
