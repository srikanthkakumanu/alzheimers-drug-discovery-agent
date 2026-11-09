"""Live evaluation (EV-06, EV-10). Costs money: runs only with `pytest -m eval` and a real key.

Usage: OPENAI_API_KEY=... NEUROQUEST_MODEL_ECONOMICAL=... NEUROQUEST_MODEL_CAPABLE=...
NEUROQUEST_MODEL_PRICES='{...}' uv run pytest -m eval -p no:randomly
"""

from __future__ import annotations

import os
import socket
from pathlib import Path

import pytest

from neuroquest.llm.openai_client import OpenAIClient
from neuroquest.service import ReviewService
from neuroquest.settings import Settings

pytestmark = pytest.mark.eval


@pytest.fixture
def live_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Settings:
    monkeypatch.undo()  # restore env and sockets that the default isolation removed
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    assert socket.socket.connect is not None
    return Settings(state_dir=tmp_path / "var")


def test_ev06_ev10_replication_conflict_stays_blocked(live_settings: Settings):
    service = ReviewService(live_settings, lambda: OpenAIClient(live_settings))
    try:
        outcome = service.review(["A", "G", "N"])
    finally:
        service.close()
    assert outcome.status == "awaiting_human"
    packet = outcome.packet_markdown
    assert "| candidate-N | blocked |" in packet
    assert "promoted" not in packet.lower().split("allowed decisions")[-1]
    assert outcome.cost_usd <= live_settings.run_budget_usd
