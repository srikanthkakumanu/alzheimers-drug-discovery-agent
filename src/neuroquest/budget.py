"""Per-run spend enforcement. Checked before every model call; charged from real usage."""

from __future__ import annotations

import math
from collections.abc import Callable

from neuroquest.errors import BudgetExceededError
from neuroquest.models.runs import Usage
from neuroquest.settings import ModelPrice

TOKENS_PER_PRICE_UNIT = 1_000_000
CHARS_PER_TOKEN_ESTIMATE = 4  # conservative heuristic for the pre-call check only


def cost_usd(price: ModelPrice, usage: Usage) -> float:
    uncached = max(usage.input_tokens - usage.cached_tokens, 0)
    return (
        uncached * price.input + usage.cached_tokens * price.cached_input + usage.output_tokens * price.output
    ) / TOKENS_PER_PRICE_UNIT


def usd(amount: float) -> str:
    """Cents for normal budgets, four decimals below a cent so small caps never read as $0.00."""
    return f"${amount:.2f}" if amount >= 0.01 else f"${amount:.4f}"


class Budget:
    def __init__(self, limit_usd: float, price_for: Callable[[str], ModelPrice]) -> None:
        self.limit_usd = limit_usd
        self.spent_usd = 0.0
        self.usage = Usage()
        self._price_for = price_for

    @property
    def remaining_usd(self) -> float:
        return max(self.limit_usd - self.spent_usd, 0.0)

    def worst_case_usd(self, model: str, prompt_chars: int, max_output_tokens: int) -> float:
        estimate = Usage(
            input_tokens=math.ceil(prompt_chars / CHARS_PER_TOKEN_ESTIMATE), output_tokens=max_output_tokens
        )
        return cost_usd(self._price_for(model), estimate)

    def ensure_affordable(self, model: str, prompt_chars: int, max_output_tokens: int) -> None:
        needed = self.worst_case_usd(model, prompt_chars, max_output_tokens)
        if self.spent_usd + needed > self.limit_usd:
            raise BudgetExceededError(
                f"Next call to {model} could cost up to ${needed:.4f}; "
                f"${self.remaining_usd:.4f} of {usd(self.limit_usd)} remains."
            )

    def charge(self, model: str, usage: Usage) -> float:
        cost = cost_usd(self._price_for(model), usage)
        self.spent_usd += cost
        self.usage = self.usage + usage
        return cost
