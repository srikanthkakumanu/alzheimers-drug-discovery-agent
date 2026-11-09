# Testing strategy

How the repository and the future application are tested without spending API budget by default. Decisions: [ADR-018](../../adr/ADR-018.md), [ADR-020](../../adr/ADR-020.md). Scenarios: [evaluation plan](evaluation-plan.md).

## Test layers
| Layer | Tool | Network / cost | Runs |
| --- | --- | --- | --- |
| Repository contracts | `scripts/validate_repository.py` + stdlib `unittest` in `tests/` | None | Every push, Stop hook |
| Unit (models, scoring, loader, packet) | pytest in `tests/app/unit` | None | Every push |
| Scoring parity | pytest: application scoring equals the validator for all candidates | None | Every push |
| Graph | pytest with a fake LLM returning fixture `Handoff`s | None | Every push |
| Recorded replies | Real OpenAI replies captured once, redacted, stored in `tests/app/fixtures/llm/` | None at test time | Every push |
| Evaluation EV-01–13 | pytest `-m eval` + LangSmith dataset | Live OpenAI, capped budget | Manual dispatch |
| Static quality | ruff, `mypy --strict` | None | Every push |

## Rules
- Default CI never calls OpenAI, LangSmith, or Tavily: `NEUROQUEST_OFFLINE=1` makes the LLM client raise if used, and tests block outbound sockets.
- The fake LLM is a typed object implementing the same interface as the real client; graph tests assert edges (skip, reviewer→researcher once, block, partial, interrupt/resume), not wording.
- Recorded fixtures are refreshed deliberately, reviewed for secrets, and tagged with model snapshot and prompt version.
- Live evaluation uses GitHub repository secrets `OPENAI_API_KEY` and `LANGSMITH_API_KEY`, a per-run budget cap, and `workflow_dispatch` only.
- Assert on structure and critical errors (fabricated citation, unlabeled synthetic claim, unauthorized promotion), not exact text. Critical errors must be zero.
- Keep held-out evaluation cases out of prompt development.

## Coverage targets (proposed)
Deterministic modules (scoring, models, loader, storage) ≥90% line coverage; graph routing: every edge exercised at least once.
