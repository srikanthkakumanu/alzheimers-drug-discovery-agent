"""Evidence record contracts (docs/architecture/data-contracts.md).

Records are read-only views of the Markdown files; invariants mirror the
repository validator so malformed data fails at load time.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, NewType

from pydantic import BaseModel, ConfigDict, Field, model_validator

CandidateId = NewType("CandidateId", str)
ExperimentId = NewType("ExperimentId", str)
PaperId = NewType("PaperId", str)

Dimension = Literal["efficacy", "safety", "bbb", "manufacturing"]
DIMENSIONS: tuple[Dimension, ...] = ("efficacy", "safety", "bbb", "manufacturing")

GateName = Literal[
    "identity", "orthogonal_activity", "replication", "cns_exposure_engagement", "safety", "manufacturing"
]
GATE_NAMES: tuple[GateName, ...] = (
    "identity",
    "orthogonal_activity",
    "replication",
    "cns_exposure_engagement",
    "safety",
    "manufacturing",
)
GateState = Literal["pass", "fail", "unknown"]
Disposition = Literal["follow-up", "hold", "blocked", "provisional", "deprioritized", "promoted"]
ExperimentStatus = Literal["completed", "proposed", "invalid"]

Rating = Annotated[float, Field(ge=0, le=5)] | None


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Scores(FrozenModel):
    efficacy: Rating
    safety: Rating
    bbb: Rating
    manufacturing: Rating

    def get(self, dimension: Dimension) -> float | None:
        value: float | None = getattr(self, dimension)
        return value

    @property
    def missing(self) -> list[Dimension]:
        return [d for d in DIMENSIONS if self.get(d) is None]


class Gates(FrozenModel):
    identity: GateState
    orthogonal_activity: GateState
    replication: GateState
    cns_exposure_engagement: GateState
    safety: GateState
    manufacturing: GateState

    def state(self, gate: GateName) -> GateState:
        value: GateState = getattr(self, gate)
        return value

    def with_state(self, state: GateState) -> list[GateName]:
        return [g for g in GATE_NAMES if self.state(g) == state]


class RatingEvidence(FrozenModel):
    efficacy: list[ExperimentId]
    safety: list[ExperimentId]
    bbb: list[ExperimentId]
    manufacturing: list[ExperimentId]

    def for_dimension(self, dimension: Dimension) -> list[ExperimentId]:
        value: list[ExperimentId] = getattr(self, dimension)
        return value


class ScoreHistoryEntry(FrozenModel):
    weighted_score: float
    scores: Scores
    basis: list[ExperimentId]
    status: Literal["disputed", "superseded"]
    challenged_by: ExperimentId
    use: str


class Candidate(FrozenModel):
    id: CandidateId
    provenance: Literal["synthetic"]
    target: str
    modality: str
    disposition: Disposition
    scores: Scores
    weighted_score: float | None
    score_status: str
    hard_blocks: list[str]
    gates: Gates
    human_approval: bool
    experiment_ids: list[ExperimentId]
    literature_ids: list[PaperId]
    rating_evidence: RatingEvidence
    score_history: list[ScoreHistoryEntry] = Field(default_factory=list)
    title: str = ""
    body: str = ""

    @property
    def letter(self) -> str:
        return self.id.removeprefix("candidate-")

    @model_validator(mode="after")
    def _check_invariants(self) -> Candidate:
        if (self.hard_blocks or self.gates.with_state("fail")) and self.disposition != "blocked":
            raise ValueError(f"{self.id}: hard block or failed gate requires disposition 'blocked'")
        if self.scores.missing and (self.weighted_score is not None or self.score_status != "provisional"):
            raise ValueError(f"{self.id}: missing ratings require a null, provisional score")
        return self


class Experiment(FrozenModel):
    id: ExperimentId
    provenance: Literal["synthetic"]
    status: ExperimentStatus
    campaign_period: int = Field(ge=1)
    candidate_ids: list[CandidateId]
    literature_ids: list[PaperId]
    measured_candidate_ids: list[CandidateId]
    raw_data_available: bool
    title: str = ""
    body: str = ""

    @model_validator(mode="after")
    def _check_invariants(self) -> Experiment:
        if not set(self.measured_candidate_ids) <= set(self.candidate_ids):
            raise ValueError(f"{self.id}: measured candidates must be a subset of candidate_ids")
        if self.status != "completed" and self.measured_candidate_ids:
            raise ValueError(f"{self.id}: {self.status} experiments cannot have measured candidates")
        return self


class Paper(FrozenModel):
    id: PaperId
    provenance: Literal["published"]
    pmid: Annotated[str, Field(pattern=r"^\d+$")]
    doi: Annotated[str, Field(pattern=r"^10\.\d{4,9}/\S+$")]
    year: int
    evidence_type: str
    review_scope: Literal["indexed metadata and abstract only"]
    verified_on: date
    tags: list[str]
    title: str = ""
    body: str = ""
