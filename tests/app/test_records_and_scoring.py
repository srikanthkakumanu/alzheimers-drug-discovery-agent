"""Record loading, model invariants, and scoring parity with the repository validator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from neuroquest.errors import UnknownRecordError
from neuroquest.models.records import Candidate
from neuroquest.repository import Repository
from neuroquest.scoring import allowed_dispositions, assess

ROOT = Path(__file__).resolve().parents[2]


def _validator():
    spec = importlib.util.spec_from_file_location("repo_validator", ROOT / "scripts/validate_repository.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses need the module registered
    spec.loader.exec_module(module)
    return module


def test_loads_full_corpus(repo: Repository):
    assert len(repo.candidates) >= 15
    assert len(repo.experiments) >= 20
    assert len(repo.papers) >= 23


@pytest.mark.parametrize("ref", ["A", "a", "candidate-A", " A "])
def test_resolves_candidate_aliases(repo: Repository, ref: str):
    assert repo.resolve_candidate(ref) == "candidate-A"


def test_unknown_candidate_is_reported_not_guessed(repo: Repository):
    with pytest.raises(UnknownRecordError, match="Unknown candidate 'Z'"):
        repo.resolve_candidate("Z")


def test_failed_gate_requires_blocked_disposition(repo: Repository):
    data = repo.candidates["candidate-N"].model_dump()
    data["disposition"] = "follow-up"
    with pytest.raises(ValidationError, match="requires disposition 'blocked'"):
        Candidate.model_validate(data)


def test_scores_match_validator_for_every_candidate(repo: Repository):
    validator = _validator()
    weights = dict(repo.scoring.weights)
    for candidate in repo.candidates.values():
        expected = validator.weighted_score(candidate.scores.model_dump(), weights)
        assessment = assess(candidate, repo.scoring)
        assert assessment.computed_score == expected, candidate.id
        assert assessment.score_consistent, candidate.id


def test_replication_failure_blocks_and_keeps_history(repo: Repository):
    n = assess(repo.candidates["candidate-N"], repo.scoring)
    assert n.is_blocked
    assert n.computed_score is None
    assert n.disputed_history == [72.0]
    assert allowed_dispositions(n) == {"blocked"}


def test_no_candidate_is_eligible_for_promotion(repo: Repository):
    assert not any(assess(c, repo.scoring).eligible_for_promotion for c in repo.candidates.values())


def test_unblocked_candidate_never_offers_promotion(repo: Repository):
    a = assess(repo.candidates["candidate-A"], repo.scoring)
    assert "promoted" not in allowed_dispositions(a)
    assert any(b.startswith("unknown gate") for b in a.blockers)


def test_evidence_prioritizes_replication_challenger(repo: Repository):
    evidence = repo.evidence_for(["candidate-N"], limit=3)  # type: ignore[list-item]
    assert evidence[0].id == "EXP-014"
    assert len(evidence) <= 3
