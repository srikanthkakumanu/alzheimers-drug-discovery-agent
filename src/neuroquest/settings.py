"""Runtime configuration from environment variables and `.env` (pydantic-settings).

Secrets are `SecretStr` so they never appear in reprs, logs, or tracebacks.
Model IDs and prices are configuration, never code (ADR-015).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from neuroquest.errors import ConfigurationError

Tier = Literal["economical", "capable", "escalation"]


@dataclass(frozen=True, slots=True)
class Provider:
    label: str
    base_url: str
    key_env: tuple[str, ...]  # accepted environment variable names, preferred first


# OpenAI-compatible endpoints for the low-cost providers (ADR-022).
PROVIDERS: dict[str, Provider] = {
    "groq": Provider("Groq", "https://api.groq.com/openai/v1", ("GROQ_API_KEY",)),
    "google": Provider(
        "Google Gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    ),
    "mistral": Provider("Mistral", "https://api.mistral.ai/v1", ("MISTRAL_API_KEY",)),
    "openai": Provider("OpenAI", "https://api.openai.com/v1", ("OPENAI_API_KEY",)),
}


def split_model_id(model_id: str) -> tuple[str, str]:
    """`groq:llama-3.1-8b-instant` -> ("groq", "llama-3.1-8b-instant"); no known prefix -> ("openai", id)."""
    provider, sep, model = model_id.partition(":")
    if sep and provider in PROVIDERS:
        return provider, model
    return "openai", model_id


class ModelPrice(BaseModel):
    """USD per one million tokens, from the provider's published price list."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input: float = Field(ge=0)
    cached_input: float = Field(ge=0)
    output: float = Field(ge=0)


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from `start` (default: cwd) to the folder holding CLAUDE.md and config/."""
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        if (folder / "CLAUDE.md").is_file() and (folder / "config" / "scoring-model.json").is_file():
            return folder
    raise ConfigurationError("Cannot find the NeuroQuest repository root; set NEUROQUEST_REPO_ROOT.")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    groq_api_key: SecretStr | None = Field(default=None, validation_alias="GROQ_API_KEY")
    google_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY")
    )
    mistral_api_key: SecretStr | None = Field(default=None, validation_alias="MISTRAL_API_KEY")
    model_economical: str | None = Field(default=None, validation_alias="NEUROQUEST_MODEL_ECONOMICAL")
    model_capable: str | None = Field(default=None, validation_alias="NEUROQUEST_MODEL_CAPABLE")
    model_escalation: str | None = Field(default=None, validation_alias="NEUROQUEST_MODEL_ESCALATION")
    model_prices: dict[str, ModelPrice] = Field(default_factory=dict, validation_alias="NEUROQUEST_MODEL_PRICES")

    run_budget_usd: float = Field(default=0.10, gt=0, validation_alias="NEUROQUEST_RUN_BUDGET_USD")
    request_timeout_s: float = Field(default=60.0, gt=0, validation_alias="NEUROQUEST_REQUEST_TIMEOUT_S")
    max_retries: int = Field(default=2, ge=0, le=5, validation_alias="NEUROQUEST_MAX_RETRIES")
    max_evidence_records: int = Field(default=8, ge=1, le=20, validation_alias="NEUROQUEST_MAX_EVIDENCE_RECORDS")
    max_output_tokens: int = Field(default=1500, ge=200, le=8000, validation_alias="NEUROQUEST_MAX_OUTPUT_TOKENS")

    repo_root: Path | None = Field(default=None, validation_alias="NEUROQUEST_REPO_ROOT")
    state_dir: Path | None = Field(default=None, validation_alias="NEUROQUEST_STATE_DIR")
    offline: bool = Field(default=False, validation_alias="NEUROQUEST_OFFLINE")

    langsmith_tracing: bool = Field(default=False, validation_alias=AliasChoices("LANGSMITH_TRACING"))
    langsmith_api_key: SecretStr | None = Field(default=None, validation_alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="neuroquest", validation_alias="LANGSMITH_PROJECT")

    def resolved_repo_root(self) -> Path:
        return (self.repo_root or find_repo_root()).resolve()

    def resolved_state_dir(self) -> Path:
        path = (self.state_dir or self.resolved_repo_root() / "var").resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def model_for(self, tier: Tier) -> str:
        model = {
            "economical": self.model_economical,
            "capable": self.model_capable,
            "escalation": self.model_escalation,
        }[tier]
        if not model:
            raise ConfigurationError(f"Set NEUROQUEST_MODEL_{tier.upper()} to a model ID, e.g. groq:<model>.")
        return model

    def providers_in_use(self, tiers: tuple[Tier, ...]) -> set[str]:
        return {split_model_id(self.model_for(tier))[0] for tier in tiers}

    def api_key_for(self, provider: str) -> str:
        key = {
            "openai": self.openai_api_key,
            "groq": self.groq_api_key,
            "google": self.google_api_key,
            "mistral": self.mistral_api_key,
        }[provider]
        if key is None:
            names = " or ".join(PROVIDERS[provider].key_env)
            raise ConfigurationError(f"Set {names} to call {PROVIDERS[provider].label} models.")
        return key.get_secret_value()

    def price_for(self, model: str) -> ModelPrice:
        price = self.model_prices.get(model)
        if price is None:
            raise ConfigurationError(
                f"No price configured for model {model!r}; add it to NEUROQUEST_MODEL_PRICES "
                "so the run budget can be enforced."
            )
        return price

    def export_tracing_env(self) -> None:
        """LangSmith reads os.environ; export only when tracing is explicitly enabled."""
        if not self.langsmith_tracing:
            os.environ["LANGSMITH_TRACING"] = "false"
            return
        if self.langsmith_api_key is None:
            raise ConfigurationError("LANGSMITH_TRACING is true but LANGSMITH_API_KEY is not set.")
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key.get_secret_value()
        os.environ["LANGSMITH_PROJECT"] = self.langsmith_project
