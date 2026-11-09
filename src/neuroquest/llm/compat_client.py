"""Low-cost providers through their OpenAI-compatible Chat Completions endpoints (ADR-022).

Model IDs carry a provider prefix, e.g. `groq:llama-3.1-8b-instant`. JSON mode is the
portable common ground across Groq, Google Gemini, and Mistral, so the Pydantic schema
goes in the system prompt and every reply is validated here, with one repair attempt.
Transport retries (429, 5xx, timeouts) use the SDK's built-in backoff.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from neuroquest.errors import ConfigurationError, LLMError
from neuroquest.llm.base import LLMRequest, LLMResult
from neuroquest.models.runs import Usage
from neuroquest.settings import PROVIDERS, Settings, Tier, split_model_id

REPAIR_ATTEMPTS = 1


class CompatClient:
    def __init__(self, settings: Settings) -> None:
        if settings.offline:
            raise ConfigurationError("NEUROQUEST_OFFLINE is set; live model calls are disabled.")
        import openai  # deferred so offline use and tests never import network clients

        self._openai = openai
        self._settings = settings
        self._clients: dict[str, Any] = {}

    def model_for(self, tier: Tier) -> str:
        return self._settings.model_for(tier)

    def _client(self, provider: str) -> Any:
        if provider not in self._clients:
            key = self._settings.api_key_for(provider)
            client: Any = self._openai.OpenAI(
                api_key=key,
                base_url=PROVIDERS[provider].base_url,
                timeout=self._settings.request_timeout_s,
                max_retries=self._settings.max_retries,
            )
            if self._settings.langsmith_tracing:
                from langsmith.wrappers import wrap_openai

                client = wrap_openai(client)
            self._clients[provider] = client
        return self._clients[provider]

    def complete[T: BaseModel](self, request: LLMRequest, output_model: type[T]) -> LLMResult[T]:
        model_id = self.model_for(request.tier)
        provider, model = split_model_id(model_id)
        schema = json.dumps(output_model.model_json_schema(), separators=(",", ":"))
        system = (
            f"{request.system}\n\nReply with one JSON object only, no prose or code fences. "
            f"It must validate against this JSON Schema:\n{schema}"
        )
        user = request.user
        total = Usage()
        error = "The reply was empty."
        for attempt in range(REPAIR_ATTEMPTS + 1):
            response = self._call(provider, model, system, user, request.max_output_tokens)
            total = total + self._usage(response)
            text = response.choices[0].message.content if response.choices else None
            if text:
                try:
                    output = output_model.model_validate_json(_strip_fences(text))
                except ValidationError as exc:
                    error = f"Validation errors: {exc}"
                else:
                    return LLMResult(output=output, model=model_id, usage=total)
            if attempt < REPAIR_ATTEMPTS:
                user = (
                    f"{request.user}\n\nYour previous reply did not match the required schema. "
                    f"{error}\nReturn only a valid JSON object."
                )
        raise LLMError(f"{model_id} did not return a valid {output_model.__name__} after repair.")

    def _call(self, provider: str, model: str, system: str, user: str, max_tokens: int) -> Any:
        name = PROVIDERS[provider].label
        try:
            return self._client(provider).chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=0,
            )
        except (self._openai.AuthenticationError, self._openai.PermissionDeniedError) as exc:
            raise LLMError(f"{name} rejected the API key or access; check {PROVIDERS[provider].key_env[0]}.") from exc
        except self._openai.BadRequestError as exc:
            raise LLMError(f"{name} rejected the request for {model}: {exc.message}") from exc
        except self._openai.APIError as exc:
            raise LLMError(f"{name} call failed after retries: {type(exc).__name__}") from exc

    @staticmethod
    def _usage(response: Any) -> Usage:
        usage = getattr(response, "usage", None)
        if usage is None:
            return Usage()
        details = getattr(usage, "prompt_tokens_details", None)
        return Usage(
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            cached_tokens=getattr(details, "cached_tokens", 0) or 0,
        )


def _strip_fences(text: str) -> str:
    """Some models wrap JSON in ``` fences even in JSON mode."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else ""
        stripped = stripped.rsplit("```", 1)[0]
    return stripped.strip()
