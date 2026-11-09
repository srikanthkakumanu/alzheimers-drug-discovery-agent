"""CLI exit codes and OpenAI client error handling, without network access."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from neuroquest import cli
from neuroquest.errors import ConfigurationError, LLMError
from neuroquest.llm.base import LLMRequest
from neuroquest.llm.openai_client import OpenAIClient
from neuroquest.models.handoff import ReviewHandoff
from neuroquest.settings import Settings

from .conftest import FAKE_PRICES, REPO_ROOT, make_fake

runner = CliRunner()


@pytest.fixture
def cli_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)  # keep any real .env out of reach
    monkeypatch.setenv("NEUROQUEST_REPO_ROOT", str(REPO_ROOT))
    monkeypatch.setenv("NEUROQUEST_STATE_DIR", str(tmp_path / "var"))
    monkeypatch.setenv("NEUROQUEST_MODEL_PRICES", json.dumps({k: v.model_dump() for k, v in FAKE_PRICES.items()}))
    monkeypatch.setattr(cli, "make_llm", lambda _settings: make_fake())


def test_review_runs_and_decide_closes(cli_env: None):
    result = runner.invoke(cli.app, ["review", "A", "N"])
    assert result.exit_code == 0, result.output
    run_id = next(line.split()[1] for line in result.output.splitlines() if line.startswith("run_id:"))
    listed = runner.invoke(cli.app, ["runs"])
    assert run_id in listed.output
    decided = runner.invoke(cli.app, ["decide", run_id, "-d", "A=hold", "-d", "N=blocked", "--reason", "test"])
    assert decided.exit_code == 0, decided.output
    assert "Recorded human decisions" in decided.output


def test_unknown_candidate_exits_4(cli_env: None):
    result = runner.invoke(cli.app, ["review", "Z"])
    assert result.exit_code == 4
    assert "Unknown candidate" in result.output


def test_bad_disposition_syntax_exits_5(cli_env: None):
    result = runner.invoke(cli.app, ["decide", "run-x", "-d", "A=promoted", "--reason", "x"])
    assert result.exit_code == 5


def test_partial_run_exits_3(cli_env: None):
    result = runner.invoke(cli.app, ["review", "A", "--budget-usd", "0.001"])
    assert result.exit_code == 3


def test_validate_command_passes(cli_env: None):
    assert runner.invoke(cli.app, ["validate"]).exit_code == 0


def _settings(tmp_path: Path, **extra: object) -> Settings:
    return Settings(_env_file=None, repo_root=REPO_ROOT, state_dir=tmp_path, model_economical="m", **extra)


def test_client_refuses_offline_mode(tmp_path: Path):
    with pytest.raises(ConfigurationError, match="OFFLINE"):
        OpenAIClient(_settings(tmp_path, openai_api_key="sk-x", offline=True))


def test_client_requires_api_key(tmp_path: Path):
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        OpenAIClient(_settings(tmp_path))


def _validation_error() -> ValidationError:
    try:
        ReviewHandoff.model_validate({})
    except ValidationError as exc:
        return exc
    raise AssertionError("expected a validation error")


class _Responses:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.inputs: list[str] = []

    def parse(self, **kwargs: object) -> object:
        self.inputs.append(str(kwargs["input"]))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _client_with(tmp_path: Path, outcomes: list[object]) -> tuple[OpenAIClient, _Responses]:
    client = OpenAIClient(_settings(tmp_path, openai_api_key="sk-x"))
    responses = _Responses(outcomes)
    client._client = SimpleNamespace(responses=responses)
    return client, responses


def _ok() -> object:
    output = ReviewHandoff(question="q", reviews=[], uncertainty=[], next_action="n")
    usage = SimpleNamespace(input_tokens=10, output_tokens=5, input_tokens_details=SimpleNamespace(cached_tokens=4))
    return SimpleNamespace(output_parsed=output, usage=usage)


REQUEST = LLMRequest(tier="economical", system="s", user="u", max_output_tokens=300)


def test_client_repairs_once_after_schema_error(tmp_path: Path):
    client, responses = _client_with(tmp_path, [_validation_error(), _ok()])
    result = client.complete(REQUEST, ReviewHandoff)
    assert result.usage.cached_tokens == 4
    assert "did not match the required schema" in responses.inputs[1]


def test_client_gives_up_after_repeated_refusal(tmp_path: Path):
    refusal = SimpleNamespace(output_parsed=None, usage=None)
    client, _ = _client_with(tmp_path, [refusal, refusal])
    with pytest.raises(LLMError, match="after repair"):
        client.complete(REQUEST, ReviewHandoff)
