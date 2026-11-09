"""OpenAI client using the Responses API with Structured Outputs (ADR-015).

Transport retries (429, 5xx, timeouts) are delegated to the SDK's built-in
exponential backoff, which honors Retry-After. Schema failures get one repair
attempt. Authentication and request errors are never retried.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from neuroquest.errors import ConfigurationError, LLMError
from neuroquest.llm.base import LLMRequest, LLMResult
from neuroquest.models.runs import Usage
from neuroquest.settings import Settings, Tier

REPAIR_ATTEMPTS = 1


class OpenAIClient:
    def __init__(self, settings: Settings) -> None:
        if settings.offline:
            raise ConfigurationError("NEUROQUEST_OFFLINE is set; live model calls are disabled.")
        if settings.openai_api_key is None:
            raise ConfigurationError("Set OPENAI_API_KEY to run reviews with a live model.")
        import openai  # deferred so offline use and tests never import network clients

        self._openai = openai
        client: Any = openai.OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.request_timeout_s,
            max_retries=settings.max_retries,
        )
        if settings.langsmith_tracing:
            from langsmith.wrappers import wrap_openai

            client = wrap_openai(client)
        self._client = client
        self._settings = settings

    def model_for(self, tier: Tier) -> str:
        return self._settings.model_for(tier)

    def complete[T: BaseModel](self, request: LLMRequest, output_model: type[T]) -> LLMResult[T]:
        model = self.model_for(request.tier)
        user = request.user
        total = Usage()
        for attempt in range(REPAIR_ATTEMPTS + 1):
            error: ValidationError | None = None
            parsed: BaseModel | None = None
            try:
                # The SDK validates against the schema while parsing, so errors surface here.
                response = self._call(model, request, user, output_model)
            except ValidationError as exc:
                error = exc
            else:
                total = total + self._usage(response)
                parsed = response.output_parsed
            if parsed is not None:
                return LLMResult(output=output_model.model_validate(parsed.model_dump()), model=model, usage=total)
            if attempt < REPAIR_ATTEMPTS:
                detail = f"Validation errors: {error}" if error else "The reply was empty or a refusal."
                user = (
                    f"{request.user}\n\nYour previous reply did not match the required schema. "
                    f"{detail}\nReturn only a valid object."
                )
        raise LLMError(f"{model} did not return a valid {output_model.__name__} after repair.")

    def _call(self, model: str, request: LLMRequest, user: str, output_model: type[BaseModel]) -> Any:
        try:
            return self._client.responses.parse(
                model=model,
                instructions=request.system,
                input=user,
                text_format=output_model,
                max_output_tokens=request.max_output_tokens,
            )
        except (self._openai.AuthenticationError, self._openai.PermissionDeniedError) as exc:
            raise LLMError("OpenAI rejected the API key or access; check OPENAI_API_KEY.") from exc
        except self._openai.BadRequestError as exc:
            raise LLMError(f"OpenAI rejected the request for {model}: {exc.message}") from exc
        except self._openai.APIError as exc:
            raise LLMError(f"OpenAI call failed after retries: {type(exc).__name__}") from exc

    @staticmethod
    def _usage(response: Any) -> Usage:
        usage = getattr(response, "usage", None)
        if usage is None:
            return Usage()
        details = getattr(usage, "input_tokens_details", None)
        return Usage(
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            cached_tokens=getattr(details, "cached_tokens", 0) or 0,
        )
