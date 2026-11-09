"""Shared fixtures. Tests never touch the network, the real `.env`, or the repo's `var/`."""

from __future__ import annotations

import os
import socket
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from neuroquest.llm.base import LLMRequest
from neuroquest.llm.fake import FakeLLM
from neuroquest.models.handoff import CandidateReview, Claim, PortfolioPacket, Recommendation, ReviewHandoff
from neuroquest.repository import Repository
from neuroquest.service import ReviewService
from neuroquest.settings import ModelPrice, Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
FAKE_PRICE = ModelPrice(input=1.0, cached_input=0.5, output=4.0)
FAKE_PRICES = {f"fake-{tier}": FAKE_PRICE for tier in ("economical", "capable", "escalation")}


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith(
            ("NEUROQUEST_", "OPENAI_", "LANGSMITH_", "TAVILY_", "GROQ_", "GEMINI_", "GOOGLE_", "MISTRAL_")
        ):
            monkeypatch.delenv(key)

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("network access is blocked in tests")

    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.fixture(scope="session")
def repo() -> Repository:
    return Repository(REPO_ROOT)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(_env_file=None, repo_root=REPO_ROOT, state_dir=tmp_path / "var", model_prices=FAKE_PRICES)


def make_fake(recommend: dict[str, str] | None = None) -> FakeLLM:
    """Fake reviewer/portfolio that echoes the requested candidates. `recommend` overrides dispositions."""
    recommend = recommend or {}

    def ids(request: LLMRequest) -> list[str]:
        marker = "Use exactly these candidate IDs: "
        return request.user.split(marker, 1)[1].strip().rstrip(".").split(", ")

    def review(request: LLMRequest) -> ReviewHandoff:
        return ReviewHandoff(
            question="q",
            reviews=[
                CandidateReview(
                    candidate_id=c,
                    supported_claims=[
                        Claim(statement="Orthogonal activity", provenance="synthetic", record_ids=["EXP-005"])
                    ],
                    disputed_claims=[],
                    missing_evidence=["measured free CNS exposure"],
                    next_action="Plan exposure study",
                )
                for c in ids(request)
            ],
            uncertainty=["synthetic data only"],
            next_action="portfolio comparison",
        )

    def portfolio(request: LLMRequest) -> PortfolioPacket:
        return PortfolioPacket(
            summary="Follow up the strongest unblocked candidates.",
            recommendations=[
                Recommendation(
                    candidate_id=c,
                    recommended_disposition=recommend.get(c, "hold"),  # type: ignore[arg-type]
                    rationale="test",
                    information_value="medium",
                    next_step="exposure study",
                )
                for c in ids(request)
            ],
            human_decision_required="Choose dispositions.",
        )

    return FakeLLM(responders={ReviewHandoff: review, PortfolioPacket: portfolio})


@pytest.fixture
def fake_factory() -> Callable[..., FakeLLM]:
    return make_fake


@pytest.fixture
def service_with(settings: Settings, repo: Repository) -> Iterator[Callable[[FakeLLM], ReviewService]]:
    created: list[ReviewService] = []

    def build(llm: FakeLLM) -> ReviewService:
        service = ReviewService(settings, lambda: llm, repo)
        created.append(service)
        return service

    yield build
    for service in created:
        service.close()
