"""End-to-end graph runs with a fake LLM: pause, gate enforcement, decisions, budget stop."""

from __future__ import annotations

import sqlite3

import pytest

from neuroquest.errors import ConfigurationError, DecisionError, UnknownRecordError
from neuroquest.models.handoff import PortfolioPacket, ReviewHandoff


def test_review_pauses_for_human_with_packet(service_with, fake_factory):
    llm = fake_factory({"candidate-A": "follow-up", "candidate-G": "follow-up"})
    outcome = service_with(llm).review(["A", "G", "N"])
    assert outcome.status == "awaiting_human"
    assert "SYNTHETIC DEMONSTRATION" in outcome.packet_markdown
    assert "| candidate-N | unknown | **yes** | replication |" in outcome.packet_markdown
    assert [model for _, model in llm.calls] == [ReviewHandoff, PortfolioPacket]
    assert outcome.cost_usd > 0


def test_reviewer_escalates_when_replication_failed(service_with, fake_factory):
    llm = fake_factory()
    service_with(llm).review(["A", "N"])
    assert llm.calls[0][0].tier == "capable"


def test_reviewer_uses_economical_tier_without_conflict(service_with, fake_factory):
    llm = fake_factory()
    service_with(llm).review(["A", "G"])
    assert llm.calls[0][0].tier == "economical"


def test_model_cannot_unblock_a_gated_candidate(service_with, fake_factory):
    outcome = service_with(fake_factory({"candidate-N": "follow-up"})).review(["N"])
    assert "| candidate-N | blocked |" in outcome.packet_markdown
    assert "overridden to 'blocked' by gate rule" in outcome.packet_markdown


def test_decision_closes_run_and_is_append_only(service_with, fake_factory, settings):
    service = service_with(fake_factory())
    run = service.review(["A", "N"])
    closed = service.decide(run.run_id, {"A": "follow-up", "N": "blocked"}, "Exposure first", "tester")
    assert closed.status == "closed"
    assert "candidate-A: **follow-up** by tester" in closed.packet_markdown
    assert len(service.store.decisions_for(run.run_id)) == 2
    db = sqlite3.connect(settings.resolved_state_dir() / "neuroquest.sqlite3")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        db.execute("DELETE FROM decisions")


def test_gate_rule_rejects_unblocking_decision(service_with, fake_factory):
    service = service_with(fake_factory())
    run = service.review(["N"])
    with pytest.raises(DecisionError, match="gates allow only"):
        service.decide(run.run_id, {"N": "follow-up"}, "override", "tester")


def test_decision_requires_awaiting_run(service_with, fake_factory):
    service = service_with(fake_factory())
    run = service.review(["A"])
    service.decide(run.run_id, {"A": "hold"}, "wait", "tester")
    with pytest.raises(DecisionError, match="not awaiting"):
        service.decide(run.run_id, {"A": "hold"}, "again", "tester")


def test_decision_rejects_candidate_outside_run(service_with, fake_factory):
    service = service_with(fake_factory())
    run = service.review(["A"])
    with pytest.raises(DecisionError, match="not part of run"):
        service.decide(run.run_id, {"G": "hold"}, "wrong", "tester")


def test_budget_exhaustion_returns_partial_without_model_call(service_with, fake_factory):
    llm = fake_factory()
    outcome = service_with(llm).review(["A", "G", "N"], budget_usd=0.0001)
    assert outcome.status == "partial"
    assert llm.calls == []
    assert "reviewer: Next call" in outcome.packet_markdown


def test_unknown_candidate_creates_no_run(service_with, fake_factory):
    service = service_with(fake_factory())
    with pytest.raises(UnknownRecordError):
        service.review(["Z"])
    assert service.runs() == []


def test_missing_price_fails_before_run_is_recorded(service_with, fake_factory, settings):
    service = service_with(fake_factory())
    service.settings = settings.model_copy(update={"model_prices": {}})
    with pytest.raises(ConfigurationError, match="NEUROQUEST_MODEL_PRICES"):
        service.review(["A"])
    assert service.runs() == []


def test_claim_both_supported_and_disputed_stays_disputed():
    from neuroquest.graph.build import resolve_contradictions
    from neuroquest.models.handoff import CandidateReview, Claim, ReviewHandoff

    efficacy = Claim(
        statement="Reduced Tau seeding in the cellular assay.", provenance="synthetic", record_ids=["EXP-004"]
    )
    same = Claim(statement="reduced tau seeding in the cellular assay", provenance="synthetic", record_ids=["EXP-006"])
    other = Claim(statement="Solubility acceptable", provenance="synthetic", record_ids=["EXP-013"])
    review = ReviewHandoff(
        question="q",
        reviews=[
            CandidateReview(
                candidate_id="candidate-C",
                supported_claims=[efficacy, other],
                disputed_claims=[same],
                missing_evidence=[],
                next_action="n",
            )
        ],
        uncertainty=[],
        next_action="n",
    )
    clean, notes = resolve_contradictions(review)
    assert [c.statement for c in clean.reviews[0].supported_claims] == ["Solubility acceptable"]
    assert clean.reviews[0].disputed_claims == [same]
    assert len(notes) == 1
    assert "candidate-C" in notes[0]
    assert "kept only as disputed" in notes[0]
