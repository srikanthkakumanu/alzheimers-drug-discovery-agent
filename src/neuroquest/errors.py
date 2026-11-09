"""Typed errors shared across the application. Messages never contain secrets."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neuroquest.models.runs import Usage


class NeuroQuestError(Exception):
    """Base class for expected, user-reportable failures."""


class ConfigurationError(NeuroQuestError):
    """A required setting is missing or invalid."""


class UnknownRecordError(NeuroQuestError):
    """A requested record ID does not exist in the repository."""


class RecordFormatError(NeuroQuestError):
    """A record file cannot be parsed into its contract."""


class BudgetExceededError(NeuroQuestError):
    """The next model call would exceed the run budget."""


class LLMError(NeuroQuestError):
    """A model call failed in a way that retries cannot fix.

    `usage` holds tokens already consumed by failed attempts, so the budget still charges them.
    """

    def __init__(self, message: str, usage: Usage | None = None) -> None:
        super().__init__(message)
        self.usage = usage


class DecisionError(NeuroQuestError):
    """A human decision violates a gate rule or targets an invalid run."""
