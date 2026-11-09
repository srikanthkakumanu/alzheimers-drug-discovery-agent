"""Run graph: score_and_gate → load_evidence → reviewer → portfolio → human_decision.

Deterministic nodes never call a model. LLM nodes check the budget first, record
usage, and stop the run as `partial` on budget exhaustion or model failure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel

from neuroquest.budget import Budget
from neuroquest.errors import BudgetExceededError, LLMError
from neuroquest.graph.state import RunState, assessments_of, review_of
from neuroquest.llm.base import LLMClient, LLMRequest
from neuroquest.llm.prompts import Role, evidence_block, system_prompt
from neuroquest.models.handoff import CandidateReview, PortfolioPacket, Recommendation, ReviewHandoff
from neuroquest.models.records import CandidateId
from neuroquest.models.runs import HumanDecision, Usage
from neuroquest.models.scoring import Assessment
from neuroquest.repository import Repository
from neuroquest.scoring import allowed_dispositions, assess
from neuroquest.settings import Tier
from neuroquest.storage import Store


@dataclass(frozen=True, slots=True)
class GraphDeps:
    repo: Repository
    llm: LLMClient
    budget: Budget
    store: Store
    max_evidence_records: int
    max_output_tokens: int

    @property
    def repo_root(self) -> Path:
        return self.repo.root


def _assessment_json(assessments: list[Assessment]) -> str:
    return json.dumps([a.model_dump(mode="json") for a in assessments], indent=1)


def reviewer_tier(assessments: list[Assessment]) -> Tier:
    """Escalate to the capable tier when evidence conflicts (disputed history or failed replication)."""
    conflict = any(a.disputed_history or "replication" in a.failed_gates for a in assessments)
    return "capable" if conflict else "economical"


def enforce_gates(packet: PortfolioPacket, assessments: list[Assessment]) -> tuple[PortfolioPacket, list[str]]:
    """Gates beat scores and models: override any recommendation a gate forbids, visibly."""
    by_id = {a.candidate_id: a for a in assessments}
    notes: list[str] = []
    kept: list[Recommendation] = []
    for rec in packet.recommendations:
        assessment = by_id.get(CandidateId(rec.candidate_id))
        if assessment is None:
            notes.append(f"Dropped a recommendation for unrequested candidate {rec.candidate_id!r}.")
            continue
        allowed = allowed_dispositions(assessment)
        if rec.recommended_disposition not in allowed:
            notes.append(
                f"{rec.candidate_id}: model recommended {rec.recommended_disposition!r}; overridden "
                f"to 'blocked' by gate rule ({'; '.join(assessment.blockers[:2])})."
            )
            rec = rec.model_copy(update={"recommended_disposition": "blocked"})
        kept.append(rec)
    missing = sorted(set(by_id) - {CandidateId(r.candidate_id) for r in kept})
    if missing:
        notes.append("No model recommendation for: " + ", ".join(missing) + ".")
    return packet.model_copy(update={"recommendations": kept}), notes


def _claim_key(statement: str) -> str:
    return " ".join("".join(ch for ch in statement.lower() if ch.isalnum() or ch.isspace()).split())


def resolve_contradictions(review: ReviewHandoff) -> tuple[ReviewHandoff, list[str]]:
    """A claim listed as both supported and disputed stays only as disputed, visibly (EV-02, EV-03)."""
    notes: list[str] = []
    reviews: list[CandidateReview] = []
    for r in review.reviews:
        disputed = {_claim_key(c.statement) for c in r.disputed_claims}
        kept = []
        for claim in r.supported_claims:
            if _claim_key(claim.statement) in disputed:
                notes.append(
                    f"{r.candidate_id}: claim {claim.statement!r} was listed as both supported and disputed; "
                    "kept only as disputed."
                )
            else:
                kept.append(claim)
        reviews.append(r.model_copy(update={"supported_claims": kept}))
    return review.model_copy(update={"reviews": reviews}), notes


def build_graph(deps: GraphDeps, checkpointer: Any) -> Any:
    def call_llm[T: BaseModel](
        state: RunState, node: str, role: Role, tier: Tier, user: str, output_model: type[T]
    ) -> tuple[T | None, RunState]:
        prompt = system_prompt(deps.repo_root, role, output_model)
        request = LLMRequest(tier=tier, system=prompt.text, user=user, max_output_tokens=deps.max_output_tokens)
        model = deps.llm.model_for(tier)
        versions = [*state.get("prompt_versions", []), prompt.version]
        try:
            deps.budget.ensure_affordable(model, request.prompt_chars, request.max_output_tokens)
            result = deps.llm.complete(request, output_model)
        except (BudgetExceededError, LLMError) as exc:
            deps.store.add_step(state["run_id"], node, model, Usage(), 0.0, error=str(exc))
            failed: RunState = {
                "status": "partial",
                "notes": [*state.get("notes", []), f"{node}: {exc}"],
                "prompt_versions": versions,
            }
            return None, failed
        cost = deps.budget.charge(result.model, result.usage)
        deps.store.add_step(
            state["run_id"], node, result.model, result.usage, cost, handoff=result.output.model_dump_json()
        )
        ok: RunState = {"prompt_versions": versions}
        return result.output, ok

    def score_and_gate(state: RunState) -> RunState:
        assessments = [assess(deps.repo.candidate(CandidateId(c)), deps.repo.scoring) for c in state["candidate_ids"]]
        notes = [
            f"{a.candidate_id}: recorded score {a.recorded_score} differs from computed {a.computed_score}."
            for a in assessments
            if not a.score_consistent
        ]
        return {
            "assessments": [a.model_dump(mode="json") for a in assessments],
            "notes": [*state.get("notes", []), *notes],
            "status": "running",
        }

    def load_evidence(state: RunState) -> RunState:
        ids = [CandidateId(c) for c in state["candidate_ids"]]
        experiments = deps.repo.evidence_for(ids, deps.max_evidence_records)
        return {"evidence_ids": [e.id for e in experiments]}

    def reviewer(state: RunState) -> RunState:
        assessments = assessments_of(state)
        candidates = [deps.repo.candidate(a.candidate_id) for a in assessments]
        experiments = [deps.repo.experiments[e] for e in state.get("evidence_ids", [])]  # type: ignore[index]
        user = (
            f"Question: {state['question']}\n\n"
            f"Deterministic assessment (authoritative):\n{_assessment_json(assessments)}\n\n"
            f"Evidence:\n{evidence_block(candidates, experiments)}\n\n"
            "Review each candidate: supported and disputed claims with record IDs, missing evidence, "
            "and one next action. A claim states what a cited experiment observed; a screening result "
            "is not a passed gate, so never write that a candidate 'has safety' or 'has efficacy'. "
            "Every gate the assessment marks unknown goes in missing_evidence only. "
            "A claim is either supported or disputed, never both; do not restate ratings or scores as claims. "
            "Use exactly these candidate IDs: " + ", ".join(a.candidate_id for a in assessments) + "."
        )
        output, update = call_llm(state, "reviewer", "reviewer", reviewer_tier(assessments), user, ReviewHandoff)
        if output is None:
            return update
        requested = set(state["candidate_ids"])
        stray = [r.candidate_id for r in output.reviews if r.candidate_id not in requested]
        reviews = [r for r in output.reviews if r.candidate_id in requested]
        notes = [*state.get("notes", [])]
        if stray:
            notes.append("Dropped reviewer output for unrequested IDs: " + ", ".join(stray) + ".")
        clean, contradictions = resolve_contradictions(output.model_copy(update={"reviews": reviews}))
        notes.extend(contradictions)
        return {**update, "review": clean.model_dump(mode="json"), "notes": notes}

    def portfolio(state: RunState) -> RunState:
        assessments = assessments_of(state)
        review = review_of(state)
        allowed = {a.candidate_id: sorted(allowed_dispositions(a)) for a in assessments}
        user = (
            f"Question: {state['question']}\n\n"
            f"Deterministic assessment (authoritative):\n{_assessment_json(assessments)}\n\n"
            f"Reviewer handoff:\n{review.model_dump_json(indent=1) if review else 'none'}\n\n"
            f"Allowed recommendations per candidate: {json.dumps(allowed)}\n\n"
            "Recommend one disposition per candidate with rationale, information value, and next step, "
            "then state the human decision still required. Use exactly these candidate IDs: "
            + ", ".join(a.candidate_id for a in assessments)
            + "."
        )
        output, update = call_llm(state, "portfolio", "portfolio", "capable", user, PortfolioPacket)
        if output is None:
            return update
        packet, notes = enforce_gates(output, assessments)
        return {
            **update,
            "portfolio": packet.model_dump(mode="json"),
            "notes": [*state.get("notes", []), *notes],
            "status": "awaiting_human",
        }

    def human_decision(state: RunState) -> RunState:
        resumed = interrupt({"run_id": state["run_id"], "awaiting": "human decision"})
        decisions = [HumanDecision.model_validate(d) for d in resumed]
        return {"decisions": [d.model_dump(mode="json") for d in decisions], "status": "closed"}

    def continue_or_stop(state: RunState) -> Literal["continue", "stop"]:
        return "stop" if state.get("status") == "partial" else "continue"

    builder = StateGraph(RunState)
    builder.add_node("score_and_gate", score_and_gate)
    builder.add_node("load_evidence", load_evidence)
    builder.add_node("reviewer", reviewer)
    builder.add_node("portfolio", portfolio)
    builder.add_node("human_decision", human_decision)
    builder.add_edge(START, "score_and_gate")
    builder.add_edge("score_and_gate", "load_evidence")
    builder.add_edge("load_evidence", "reviewer")
    builder.add_conditional_edges("reviewer", continue_or_stop, {"continue": "portfolio", "stop": END})
    builder.add_conditional_edges("portfolio", continue_or_stop, {"continue": "human_decision", "stop": END})
    builder.add_edge("human_decision", END)
    return builder.compile(checkpointer=checkpointer)
