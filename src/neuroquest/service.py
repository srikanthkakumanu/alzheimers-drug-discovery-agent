"""Application service: starts reviews, records human decisions, lists runs."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from pydantic import BaseModel

from neuroquest.budget import Budget
from neuroquest.errors import DecisionError, LLMError
from neuroquest.graph.build import GraphDeps, build_graph
from neuroquest.graph.state import RunState, assessments_of, decisions_of, portfolio_of, review_of
from neuroquest.llm.base import LLMClient, LLMRequest, LLMResult
from neuroquest.models.records import CandidateId
from neuroquest.models.runs import HumanDecision, HumanDisposition, RunRecord, RunStatus
from neuroquest.packet import render_packet
from neuroquest.repository import Repository
from neuroquest.scoring import allowed_dispositions
from neuroquest.settings import Settings, Tier
from neuroquest.storage import Store

PIPELINE_TIERS: tuple[Tier, ...] = ("economical", "capable")  # escalation is not used in the first slice


@dataclass(frozen=True, slots=True)
class RunOutcome:
    run_id: str
    status: RunStatus
    packet_markdown: str
    cost_usd: float


class _NoModel:
    """Used when resuming a run: decisions never need a model."""

    def model_for(self, tier: Tier) -> str:
        return "none"

    def complete[T: BaseModel](self, request: LLMRequest, output_model: type[T]) -> LLMResult[T]:
        raise LLMError("No model is available while recording a human decision.")


class ReviewService:
    def __init__(
        self, settings: Settings, llm_factory: Callable[[], LLMClient], repo: Repository | None = None
    ) -> None:
        self.settings = settings
        self.repo = repo or Repository(settings.resolved_repo_root())
        state_dir = settings.resolved_state_dir()
        self.store = Store(state_dir / "neuroquest.sqlite3")
        self._checkpoints = sqlite3.connect(state_dir / "checkpoints.sqlite3", check_same_thread=False)
        self._saver = SqliteSaver(self._checkpoints)
        self._llm_factory = llm_factory

    def close(self) -> None:
        self.store.close()
        self._checkpoints.close()

    def _graph(self, llm: LLMClient, budget: Budget) -> Any:
        deps = GraphDeps(
            repo=self.repo,
            llm=llm,
            budget=budget,
            store=self.store,
            max_evidence_records=self.settings.max_evidence_records,
            max_output_tokens=self.settings.max_output_tokens,
        )
        return build_graph(deps, self._saver)

    @staticmethod
    def _config(run_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": run_id}}

    def review(self, refs: Sequence[str], question: str | None = None, budget_usd: float | None = None) -> RunOutcome:
        candidate_ids = list(dict.fromkeys(self.repo.resolve_candidate(r) for r in refs))
        limit = budget_usd if budget_usd is not None else self.settings.run_budget_usd
        question = question or (
            "Compare candidates "
            + ", ".join(c.removeprefix("candidate-") for c in candidate_ids)
            + " and recommend the most informative next evidence step."
        )
        llm = self._preflight()
        run_id = f"run-{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
        self.store.create_run(run_id, question, candidate_ids, limit)
        budget = Budget(limit, self.settings.price_for)
        graph = self._graph(llm, budget)
        try:
            return self._run(graph, run_id, question, candidate_ids, budget, limit)
        except Exception:
            self.store.finish_run(run_id, "failed", None, None, budget.usage, budget.spent_usd)
            raise

    def _preflight(self) -> LLMClient:
        """Fail on missing key, model IDs, or prices before any run is recorded or money is spent."""
        llm = self._llm_factory()
        for tier in PIPELINE_TIERS:
            self.settings.price_for(llm.model_for(tier))
        return llm

    def _run(
        self, graph: Any, run_id: str, question: str, candidate_ids: list[CandidateId], budget: Budget, limit: float
    ) -> RunOutcome:
        initial: RunState = {
            "run_id": run_id,
            "question": question,
            "candidate_ids": list(candidate_ids),
            "notes": [],
            "prompt_versions": [],
        }
        graph.invoke(initial, self._config(run_id))
        state: RunState = graph.get_state(self._config(run_id)).values
        status: RunStatus = "awaiting_human" if state.get("status") == "awaiting_human" else "partial"
        packet = self._render(state, status, budget.spent_usd, limit)
        self.store.finish_run(
            run_id, status, packet, ",".join(state.get("prompt_versions", [])) or None, budget.usage, budget.spent_usd
        )
        return RunOutcome(run_id, status, packet, budget.spent_usd)

    def decide(self, run_id: str, dispositions: Mapping[str, HumanDisposition], reason: str, actor: str) -> RunOutcome:
        run = self.store.get_run(run_id)
        if run.status != "awaiting_human":
            raise DecisionError(f"Run {run_id} is {run.status!r}, not awaiting a human decision.")
        graph = self._graph(_NoModel(), Budget(run.budget_usd, self.settings.price_for))
        state: RunState = graph.get_state(self._config(run_id)).values
        assessments = {a.candidate_id: a for a in assessments_of(state)}
        decided_at = datetime.now(UTC)
        decisions: list[HumanDecision] = []
        for ref, disposition in dispositions.items():
            cid = self.repo.resolve_candidate(ref)
            if cid not in assessments:
                raise DecisionError(f"{cid} is not part of run {run_id}.")
            allowed = allowed_dispositions(assessments[cid])
            if disposition not in allowed:
                raise DecisionError(f"{cid} cannot be {disposition!r}: gates allow only {sorted(allowed)}.")
            decisions.append(
                HumanDecision(
                    candidate_id=CandidateId(cid),
                    disposition=disposition,
                    actor=actor,
                    reason=reason,
                    decided_at=decided_at,
                )
            )
        if not decisions:
            raise DecisionError("Provide at least one candidate disposition.")
        packet_hash = hashlib.sha256((run.packet_markdown or "").encode()).hexdigest()
        graph.invoke(Command(resume=[d.model_dump(mode="json") for d in decisions]), self._config(run_id))
        for decision in decisions:
            self.store.add_decision(run_id, decision, packet_hash)
        final: RunState = graph.get_state(self._config(run_id)).values
        packet = self._render(final, "closed", run.cost_usd, run.budget_usd)
        self.store.finish_run(run_id, "closed", packet, None, run.usage, run.cost_usd)
        return RunOutcome(run_id, "closed", packet, run.cost_usd)

    def runs(self, status: RunStatus | None = None, limit: int = 20) -> list[RunRecord]:
        return self.store.list_runs(status, limit)

    def run(self, run_id: str) -> RunRecord:
        return self.store.get_run(run_id)

    @staticmethod
    def _render(state: RunState, status: str, cost: float, budget: float) -> str:
        return render_packet(
            state["run_id"],
            state["question"],
            assessments_of(state),
            review_of(state),
            portfolio_of(state),
            state.get("notes", []),
            status,
            cost,
            budget,
            decisions_of(state),
        )
