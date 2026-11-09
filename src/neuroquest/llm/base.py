"""Provider-neutral request/result types and the client protocol graph nodes depend on."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from neuroquest.models.runs import Usage
from neuroquest.settings import Tier


@dataclass(frozen=True, slots=True)
class LLMRequest:
    tier: Tier
    system: str
    user: str
    max_output_tokens: int

    @property
    def prompt_chars(self) -> int:
        return len(self.system) + len(self.user)


@dataclass(frozen=True, slots=True)
class LLMResult[T: BaseModel]:
    output: T
    model: str
    usage: Usage


class LLMClient(Protocol):
    def model_for(self, tier: Tier) -> str: ...

    def complete[T: BaseModel](self, request: LLMRequest, output_model: type[T]) -> LLMResult[T]: ...
