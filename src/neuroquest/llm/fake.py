"""Deterministic stand-in for tests and offline demos. Makes no network calls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel

from neuroquest.errors import LLMError
from neuroquest.llm.base import LLMRequest, LLMResult
from neuroquest.models.runs import Usage
from neuroquest.settings import Tier

Responder = Callable[[LLMRequest], BaseModel]


@dataclass
class FakeLLM:
    responders: dict[type[BaseModel], Responder]
    usage_per_call: Usage = field(default_factory=lambda: Usage(input_tokens=1000, output_tokens=200))
    calls: list[tuple[LLMRequest, type[BaseModel]]] = field(default_factory=list)

    def model_for(self, tier: Tier) -> str:
        return f"fake-{tier}"

    def complete[T: BaseModel](self, request: LLMRequest, output_model: type[T]) -> LLMResult[T]:
        self.calls.append((request, output_model))
        responder = self.responders.get(output_model)
        if responder is None:
            raise LLMError(f"FakeLLM has no responder for {output_model.__name__}")
        output = output_model.model_validate(responder(request).model_dump())
        return LLMResult(output=output, model=self.model_for(request.tier), usage=self.usage_per_call)
