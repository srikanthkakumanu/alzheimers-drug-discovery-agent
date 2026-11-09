"""Live evaluation (EV-06, EV-10). Costs money: runs only with `pytest -m eval` and a real key.

Usage: set the provider keys, NEUROQUEST_MODEL_ECONOMICAL, NEUROQUEST_MODEL_CAPABLE, and
NEUROQUEST_MODEL_PRICES (in `.env` or the environment), then: uv run pytest -m eval -p no:randomly
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from neuroquest.cli import make_llm
from neuroquest.errors import ConfigurationError
from neuroquest.service import PIPELINE_TIERS, ReviewService
from neuroquest.settings import Settings

pytestmark = pytest.mark.eval


@pytest.fixture
def live_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Settings:
    monkeypatch.undo()  # restore env and sockets that the default isolation removed
    assert socket.socket.connect is not None
    settings = Settings(state_dir=tmp_path / "var")
    try:
        for provider in settings.providers_in_use(PIPELINE_TIERS):
            settings.api_key_for(provider)
    except ConfigurationError as exc:
        pytest.skip(str(exc))
    return settings


def test_ev06_ev10_replication_conflict_stays_blocked(live_settings: Settings):
    service = ReviewService(live_settings, lambda: make_llm(live_settings))
    try:
        outcome = service.review(["A", "G", "N"])
    finally:
        service.close()
    assert outcome.status == "awaiting_human"
    packet = outcome.packet_markdown
    assert "| candidate-N | blocked |" in packet
    assert "promoted" not in packet.lower().split("allowed decisions")[-1]
    assert outcome.cost_usd <= live_settings.run_budget_usd
