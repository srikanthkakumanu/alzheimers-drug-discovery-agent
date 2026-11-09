# Application code — conventions (auto-loaded in `src/`)

First implementation slice: reviewer → portfolio → human decision ([application design](../../docs/architecture/application-design.md)).

- **Typed boundaries:** every value crossing a boundary is a Pydantic v2 model (`models/`). LLM output models use `extra="forbid"` and no defaults. Code passes `uv run mypy` (strict) and `uv run ruff check`.
- **Deterministic first:** scoring, gates, ID resolution, and budget checks live in `scoring.py`, `budget.py`, `repository/`; never ask a model to compute them. `graph/build.py::enforce_gates` overrides any model recommendation a gate forbids, visibly.
- **Configuration:** model IDs, prices, and budgets come from `settings.py` (environment / `.env`); never hard-code a model ID or price. Secrets are `SecretStr`; never log, print, or put them in prompts.
- **Prompts:** composed from `prompts/shared.md` + `roles/<role>/CLAUDE.md`; evidence goes inside `<evidence>` tags as untrusted data.
- **Graph state** is JSON-compatible (checkpointed); convert with helpers in `graph/state.py`.
- **Tests:** `uv run pytest` is offline (fake LLM, sockets blocked, `.env` ignored). Live evaluation: `uv run pytest -m eval` (costs money).
- Human decisions are recorded only through `neuroquest decide`; nothing writes candidate record files.
