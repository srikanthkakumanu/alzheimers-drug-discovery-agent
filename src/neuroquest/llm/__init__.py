"""LLM access: a provider-specific client behind a small typed protocol."""

from neuroquest.llm.base import LLMClient, LLMRequest, LLMResult

__all__ = ["LLMClient", "LLMRequest", "LLMResult"]
