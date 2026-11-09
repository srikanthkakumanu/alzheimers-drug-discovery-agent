# Implementation plan

Implementation authorized by the owner on 2026-11-09. Phase 5 (first slice) is **built**; status lives in [STATUS.md](../../STATUS.md).

## Phases
| Phase | Deliverable | Exit criterion |
| --- | --- | --- |
| 1 Product review | BRD, goals, personas, scope | Owner confirms users and capabilities |
| 2 Design review | Requirements, architecture, contracts, ADRs | Contradictions and assumptions resolved |
| 3 Technology review | Interface, language, coordinator, provider/model tiers, storage | **Stack selected 2026-11-09** ([ADR-011–ADR-020](../architecture/tech-stack.md)); budget and model IDs still open |
| 4 Evaluation set-up | Fixed scenarios, human rubric, deterministic checks | Acceptance thresholds and owners agreed |
| 5 First slice | Minimum path below, with tests | Passes agreed scenarios |
| 6 Release review | Measured quality, cost, traceability, residual risks | Owner reviews actual results before expansion |

## First slice (built 2026-11-09)
Synthetic question → decision packet, end to end:
1. Project skeleton: Python 3.13, uv, ruff, `mypy --strict`, pytest, Dockerfile, CI job.
2. Typed Pydantic models for records, scoring model, handoff, and settings ([data contracts](../architecture/data-contracts.md)); loader that parses the existing records.
3. Deterministic scoring and gate evaluation as plain functions, tested against all 15 candidates.
4. LangGraph graph: `scope` → `load_evidence` → `score_and_gate` → `reviewer` (OpenAI, Structured Outputs into `Handoff`) → `portfolio` → `human_decision` interrupt; SQLite checkpointer.
5. Typer CLI `neuroquest review <ids>` printing a Markdown decision packet.
6. LangSmith tracing; token and cost logging from OpenAI usage; per-run budget stop.
7. Evaluation over EV-02–EV-06 and EV-10–EV-13 as pytest tests and a LangSmith dataset.

Out of the first slice: researcher, planner, and regulatory nodes; FTS5 search; `evidence`/`plan` commands; parallel agents; vector search; live connectors; real lab data.

## Second slice (proposed)
Researcher node with literature evidence and counterevidence (papers 010–013, 021–022), FTS5 index and `neuroquest index`, `evidence` and `plan` commands, planner and regulatory nodes, LangSmith evaluation dataset for EV-01–EV-13.

## Repository tooling (done 2026-11-09)
Validator rewritten to schema-based checks: minimum record counts from `config/settings.json`, rating evidence must come from completed experiments that measured the candidate, `score_history` arithmetic, ADR status/sections/review dates, `.env` deny rules, runtime ignores, links outside code fences. Hook reports missing validator and truncated failures. 53 tests.

## Tooling still open
- Descriptive filename slugs alongside stable IDs (not needed yet).
- Add ruff, `mypy --strict`, and pytest CI jobs when application code exists ([testing strategy](testing-strategy.md)).

## Decisions required first
Listed in [TASK.md](../../TASK.md).
