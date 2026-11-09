# Technology stack — selected

**Selected by the project owner on 2026-11-09** for the first implementation. Exact package versions are pinned in `uv.lock`. Each row is an accepted ADR (ADR-011 to ADR-020) with full context, alternatives, and revisit triggers.

## Decisions
| ADR | Layer | Choice | Why | Alternatives considered |
| --- | --- | --- | --- | --- |
| ADR-011 | Interface | Typer CLI that prints a Markdown decision packet, alongside the existing Claude Code skills | Fastest useful slice; no hosting or login for a small expert team | Internal web app; Slack/Teams chat |
| ADR-021 (supersedes 012) | Language and tooling | Python 3.13, uv (locked dependencies), ruff (lint + format) | Strongest LLM/agent ecosystem; reuses the validator’s parsing and scoring rules | Python + Java/Spring API; TypeScript |
| ADR-013 | Data models and typing | Pydantic v2 + pydantic-settings; full type hints checked by `mypy --strict` | One validated, typed definition per contract; secrets as `SecretStr` | Dataclasses; pyright instead of mypy |
| ADR-014 | Coordination | LangGraph `StateGraph` with deterministic and LLM nodes | Explicit, inspectable transitions; checkpointing; human-in-the-loop interrupts | Own state machine; Claude Agent SDK |
| ADR-015 | LLM | OpenAI Python SDK called directly in graph nodes. Three tiers set by configuration: economical (small, low-cost model), capable (flagship model), escalation (strongest reasoning model, flagged hard conflicts only). Exact model IDs chosen from OpenAI’s current model list at implementation | Structured Outputs from Pydantic models, automatic prompt caching, usage reporting; owner preference | Anthropic Claude; provider-agnostic layer |
| ADR-016 | Storage | Markdown/JSON records in git (source of truth) + SQLite for graph checkpoints, run logs, and human decisions | No servers; reviewable diffs of evidence | Files + PostgreSQL; all-PostgreSQL |
| ADR-017 | Retrieval | Exact ID lookup from indexes + SQLite FTS5 keyword search | Precise and attributable at current scale | Vector search; live PubMed lookup |
| ADR-018 | Observability and evaluation | LangSmith tracing, cost tracking, and datasets; pytest for unit and scenario tests | Native LangGraph tracing with little setup | Local logs only; self-hosted Langfuse |
| ADR-019 | Packaging and deployment | Docker image (`python:3.13-slim` + uv); secrets passed at runtime | Repeatable runs locally and in CI; path to a server later | Local install only; cloud service |
| ADR-020 | CI | GitHub Actions: ruff, `mypy --strict`, pytest, repository validator | Extends the existing workflow | — |

## Engineering conventions
- **Pydantic everywhere data crosses a boundary:** record headers, handoffs, LLM output, tool results, run and decision records, configuration. Models and validators: [data contracts](data-contracts.md).
- **Strict typing:** every function annotated; `Literal` types for enumerations (gate states, dispositions); `Annotated` constraints for ranges (ratings 0–5); distinct ID types; `py.typed` shipped; mypy `--strict` blocks merges.
- **LLM calls:** OpenAI SDK inside nodes, not a chat-model wrapper, so caching and structured output stay under direct control. Use Structured Outputs with the Pydantic model as the response format, re-validate the reply, allow one retry, then return a typed failure. Trace calls with LangSmith’s OpenAI client wrapper.
- **Model IDs are configuration,** never hard-coded: `NEUROQUEST_MODEL_ECONOMICAL`, `NEUROQUEST_MODEL_CAPABLE`, `NEUROQUEST_MODEL_ESCALATION`.
- **Deterministic first:** ID lookup, scoring, gate checks, budget checks, and schema validation are plain Python nodes, never model calls.
- **Configuration:** `pydantic-settings` reads environment variables (see [.env.example](../../.env.example)); nothing is baked into the image.

## Consequences
- LangSmith sends prompts and outputs to a third-party service. Acceptable for synthetic records and public literature; revisit (masking or self-hosting) before any private data ([governance](security-and-data-governance.md)).
- LangGraph realizes the bounded coordinator proposed in [ADR-004](../../adr/ADR-004.md); transitions stay explicit and deterministic nodes stay outside the model.
- Single-provider LLM choice; switching providers later means rewriting the thin node clients.
- OpenAI processes prompts under its API data terms; confirm retention settings before any non-public data.
- Claude Code remains the *authoring* assistant for this repository (skills, hook); it is separate from the application’s LLM provider.

## Still open
Exact OpenAI model IDs per tier, per-run and monthly budget values, latency targets, evaluation thresholds, and the escalation rule ([TASK.md](../../TASK.md)).
