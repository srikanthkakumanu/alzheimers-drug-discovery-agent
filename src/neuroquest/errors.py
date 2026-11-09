"""Typed errors shared across the application. Messages never contain secrets."""

from __future__ import annotations


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
    """A model call failed in a way that retries cannot fix."""


class DecisionError(NeuroQuestError):
    """A human decision violates a gate rule or targets an invalid run."""
