"""Budget arithmetic, price configuration, and prompt composition."""

from __future__ import annotations

from pathlib import Path

import pytest

from neuroquest.budget import Budget, cost_usd
from neuroquest.errors import BudgetExceededError, ConfigurationError
from neuroquest.llm.prompts import evidence_block, role_contract, system_prompt
from neuroquest.models.handoff import ReviewHandoff
from neuroquest.models.runs import Usage
from neuroquest.repository import Repository
from neuroquest.settings import ModelPrice, Settings

ROOT = Path(__file__).resolve().parents[2]
PRICE = ModelPrice(input=2.0, cached_input=0.5, output=8.0)


def test_cost_separates_cached_input():
    usage = Usage(input_tokens=1_000_000, cached_tokens=400_000, output_tokens=100_000)
    assert cost_usd(PRICE, usage) == pytest.approx(0.6 * 2.0 + 0.4 * 0.5 + 0.1 * 8.0)


def test_budget_blocks_call_that_could_exceed_limit():
    budget = Budget(0.01, lambda _model: PRICE)
    with pytest.raises(BudgetExceededError, match="could cost up to"):
        budget.ensure_affordable("m", prompt_chars=4_000, max_output_tokens=1500)


def test_budget_charges_actual_usage():
    budget = Budget(1.0, lambda _model: PRICE)
    budget.charge("m", Usage(input_tokens=1000, output_tokens=100))
    assert budget.spent_usd == pytest.approx((1000 * 2.0 + 100 * 8.0) / 1_000_000)
    assert budget.usage.output_tokens == 100


def test_missing_price_fails_before_any_call(tmp_path: Path):
    settings = Settings(_env_file=None, repo_root=ROOT, state_dir=tmp_path)
    with pytest.raises(ConfigurationError, match="NEUROQUEST_MODEL_PRICES"):
        settings.price_for("unpriced-model")


def test_missing_model_id_names_the_setting(tmp_path: Path):
    settings = Settings(_env_file=None, repo_root=ROOT, state_dir=tmp_path)
    with pytest.raises(ConfigurationError, match="NEUROQUEST_MODEL_CAPABLE"):
        settings.model_for("capable")


def test_secrets_never_appear_in_repr(tmp_path: Path):
    settings = Settings(_env_file=None, repo_root=ROOT, state_dir=tmp_path, openai_api_key="sk-test-secret")
    assert "sk-test-secret" not in repr(settings)


def test_system_prompt_uses_role_contract_as_single_source():
    prompt = system_prompt(ROOT, "reviewer", ReviewHandoff)
    assert "challenge the validity, provenance, and reproducibility" in prompt.text
    assert "](" not in role_contract(ROOT, "reviewer")
    assert prompt.version.startswith("reviewer-v1-")
    assert prompt.version == system_prompt(ROOT, "reviewer", ReviewHandoff).version


def test_evidence_is_wrapped_as_untrusted_data(repo: Repository):
    block = evidence_block([repo.candidates["candidate-C"]], [repo.experiments["EXP-006"]])
    assert block.count("<evidence ") == 2
    assert 'id="EXP-006" provenance="synthetic"' in block
