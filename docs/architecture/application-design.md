# Application design

Implementation blueprint for the first build. Nothing here exists yet. Stack: [ADR-011–ADR-020](tech-stack.md). Graph: [agent design](agent-design.md). Prompts: [prompt design](prompt-design.md).

## Code layout
```text
pyproject.toml  uv.lock  .python-version  Dockerfile  .dockerignore
src/neuroquest/
  CLAUDE.md            coding conventions (loads only when Claude works in src/)
  py.typed
  cli.py               Typer app (commands below)
  settings.py          pydantic-settings: keys (SecretStr), model tiers, budgets, paths
  models/              records.py · scoring.py · handoff.py · tools.py · runs.py
  repository/          loader.py (frontmatter → models) · search.py (FTS5)
  scoring.py           deterministic score, gates, eligibility
  graph/               state.py (RunState TypedDict) · nodes.py · build.py
  llm/                 client.py (OpenAI, retries, usage) · prompts.py (composition)
  prompts/             shared.md · output instructions per role
  storage/             db.py · migrations/0001_init.sql
  packet.py            Markdown decision-packet renderer
tests/                 existing repository tests (stdlib unittest)
tests/app/             unit/ · graph/ · eval/ · fixtures/  (pytest)
```
`scripts/validate_repository.py` stays standard-library only so it runs without installing dependencies.

## Conventions
Every boundary value is a Pydantic model; every function is annotated and passes `mypy --strict`; enumerations are `Literal` types; IDs are `NewType`s. Scoring, gates, ID resolution, and budget checks are plain functions, never model calls. Model IDs come from settings, never literals. No secrets in logs, prompts, traces, or exceptions.

## CLI
| Command | Behavior | Exit codes |
| --- | --- | --- |
| `neuroquest review <IDS…> [--question TEXT] [--budget-usd N] [--out FILE]` | Run the graph to the human-decision pause; print the packet and `run_id` | 0 ready · 3 partial · 4 bad input |
| `neuroquest evidence "<claim>" [--max-papers N]` | Researcher-only path: claim–source map with counterevidence | 0 · 3 · 4 |
| `neuroquest plan <ID> --gap TEXT` | Planner path: study concept for one gate | 0 · 3 · 4 |
| `neuroquest decide <RUN_ID> --disposition {follow-up,hold,blocked,deprioritized} --reason TEXT` | Record a human decision and resume the run to `closed`; `promoted` is refused in demonstration mode | 0 · 4 · 5 conflict |
| `neuroquest runs [--status S]` / `show <RUN_ID>` | List runs; show a packet, usage, and trace link | 0 |
| `neuroquest index` | Rebuild the FTS5 index from records | 0 |
| `neuroquest validate` | Run the repository validator | validator’s code |

Exit code 1 means an internal error. The decision actor is the authenticated OS user for now; a stronger identity is decided before any shared deployment.

## SQLite schema (`var/neuroquest.sqlite3`)
| Table | Columns |
| --- | --- |
| `runs` | `run_id` PK, `question`, `record_ids` JSON, `status` (requested…closed, partial, blocked), `prompt_version`, `models` JSON, `input_tokens`, `cached_tokens`, `output_tokens`, `cost_usd`, `trace_id`, `created_at`, `closed_at` |
| `steps` | `run_id` FK, `seq`, `node`, `model`, `tokens` JSON, `handoff` JSON (validated `Handoff`), `error`, `started_at`, `ended_at` |
| `decisions` | `decision_id` PK, `run_id` FK, `packet_sha256`, `disposition`, `actor`, `reason`, `decided_at` — append-only |
| `records_fts` | FTS5 virtual table: `record_id`, `kind`, `title`, `body` |
| `schema_migrations` | `version`, `applied_at` |

LangGraph checkpoints live separately in `var/checkpoints.sqlite3`. Raw prompts are not stored locally; handoffs are. `var/` is git-ignored. Back up `var/` if decisions matter beyond the demonstration.

## OpenAI failure handling
| Failure | Action |
| --- | --- |
| 429 or 5xx, connection error, timeout | Retry with exponential backoff and jitter, honoring `Retry-After`; default 2 retries; counts against budget |
| 400 / 401 / 403 | No retry; typed error naming the setting to fix (never the key) |
| Reply fails Pydantic validation | One repair retry with the validation error; then typed failure → `partial` |
| Refusal or empty reply | Typed failure; step marked incomplete |
| Budget would be exceeded | Stop before the call; return `partial` with open questions |

Per-call timeout and retry counts are settings.

## Docker runbook
- Image: `python:3.12-slim`, `uv sync --frozen --no-dev`, non-root user, entrypoint `neuroquest`.
- `.dockerignore` excludes `.env`, `.git`, `var/`, caches.
- Run: `docker run --rm -it --env-file .env -v "$PWD":/repo:ro -v neuroquest-var:/var/lib/neuroquest neuroquest review A G N`.
- Settings point records at `/repo` and state at `/var/lib/neuroquest`. Secrets exist only in the container environment at runtime.
