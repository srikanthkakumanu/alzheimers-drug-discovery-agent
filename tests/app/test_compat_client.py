"""Low-cost provider client (Groq, Google, Mistral) and model-ID routing, without network access."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from neuroquest import cli
from neuroquest.errors import ConfigurationError, LLMError
from neuroquest.llm.base import LLMRequest
from neuroquest.llm.compat_client import CompatClient
from neuroquest.llm.openai_client import OpenAIClient
from neuroquest.models.handoff import ReviewHandoff
from neuroquest.settings import Settings, split_model_id

from .conftest import REPO_ROOT

REQUEST = LLMRequest(tier="economical", system="s", user="u", max_output_tokens=300)
VALID = ReviewHandoff(question="q", reviews=[], uncertainty=[], next_action="n").model_dump_json()


def _settings(tmp_path: Path, **extra: object) -> Settings:
    base: dict[str, object] = {"model_economical": "groq:small", "model_capable": "google:flash"}
    base.update(extra)
    return Settings(_env_file=None, repo_root=REPO_ROOT, state_dir=tmp_path, **base)


def test_split_model_id():
    assert split_model_id("groq:llama-3.1-8b-instant") == ("groq", "llama-3.1-8b-instant")
    assert split_model_id("google:gemini-2.5-flash-lite") == ("google", "gemini-2.5-flash-lite")
    assert split_model_id("gpt-x") == ("openai", "gpt-x")
    assert split_model_id("unknown:model") == ("openai", "unknown:model")


def test_factory_routes_prefixed_ids_to_compat_client(tmp_path: Path):
    assert isinstance(cli.make_llm(_settings(tmp_path)), CompatClient)
    bare = _settings(tmp_path, model_economical="gpt-a", model_capable="gpt-b", openai_api_key="sk-x")
    assert isinstance(cli.make_llm(bare), OpenAIClient)


def test_missing_provider_key_names_the_variable(tmp_path: Path):
    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY or GOOGLE_API_KEY"):
        _settings(tmp_path).api_key_for("google")


def test_google_key_accepts_either_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "g-x")
    assert _settings(tmp_path).api_key_for("google") == "g-x"


class _Completions:
    def __init__(self, replies: list[str | None], finish: str = "stop") -> None:
        self.finish = finish
        self.replies = replies
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, prompt_tokens_details=None)
        message = SimpleNamespace(content=self.replies.pop(0))
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=self.finish)], usage=usage)


def _client_with(tmp_path: Path, replies: list[str | None], finish: str = "stop") -> tuple[CompatClient, _Completions]:
    client = CompatClient(_settings(tmp_path, groq_api_key="k"))
    completions = _Completions(replies, finish)
    client._clients["groq"] = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_client_parses_json_and_sends_schema(tmp_path: Path):
    client, completions = _client_with(tmp_path, [VALID])
    result = client.complete(REQUEST, ReviewHandoff)
    assert result.model == "groq:small"
    assert result.usage.input_tokens == 10
    call = completions.calls[0]
    assert call["model"] == "small"
    assert call["response_format"] == {"type": "json_object"}
    assert "JSON Schema" in str(call["messages"])


def test_client_strips_code_fences(tmp_path: Path):
    client, _ = _client_with(tmp_path, [f"```json\n{VALID}\n```"])
    assert client.complete(REQUEST, ReviewHandoff).output.next_action == "n"


def test_client_repairs_once_then_succeeds(tmp_path: Path):
    client, completions = _client_with(tmp_path, ['{"question": "q"}', VALID])
    result = client.complete(REQUEST, ReviewHandoff)
    assert result.usage.input_tokens == 20  # both attempts are counted against the budget
    assert "did not match the required schema" in str(completions.calls[1]["messages"])


def test_client_gives_up_after_repair(tmp_path: Path):
    client, _ = _client_with(tmp_path, [None, "not json"])
    with pytest.raises(LLMError, match="after repair") as info:
        client.complete(REQUEST, ReviewHandoff)
    assert info.value.usage is not None
    assert info.value.usage.input_tokens == 20  # both failed attempts are reported for charging


def test_client_refuses_offline_mode(tmp_path: Path):
    with pytest.raises(ConfigurationError, match="OFFLINE"):
        CompatClient(_settings(tmp_path, offline=True))


def test_truncated_reply_asks_for_a_shorter_answer(tmp_path: Path):
    client, completions = _client_with(tmp_path, [VALID[:20], VALID[:20]], finish="length")
    with pytest.raises(LLMError, match="cut off at 300 output tokens"):
        client.complete(REQUEST, ReviewHandoff)
    assert "Be more concise" in str(completions.calls[1]["messages"])
