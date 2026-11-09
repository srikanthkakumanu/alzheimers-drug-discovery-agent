# Implementation plan

Planning only. Nothing here is authorized until the owner completes the [review](review-plan.md) and explicitly requests implementation.

## Phases
| Phase | Deliverable | Exit criterion |
| --- | --- | --- |
| 1 Product review | BRD, goals, personas, scope | Owner confirms users and capabilities |
| 2 Design review | Requirements, architecture, contracts, ADRs | Contradictions and assumptions resolved |
| 3 Technology review | Interface, language, coordinator, provider/model tiers, storage | **Stack selected 2026-11-09** ([TD-01–TD-10](../architecture/tech-stack.md)); budget and model IDs still open |
| 4 Evaluation set-up | Fixed scenarios, human rubric, deterministic checks | Acceptance thresholds and owners agreed |
| 5 First slice | Minimum path below, with tests | Passes agreed scenarios |
| 6 Release review | Measured quality, cost, traceability, residual risks | Owner reviews actual results before expansion |

## First slice (proposed)
Synthetic question → decision packet, end to end:
1. Project skeleton: Python 3.12, uv, ruff, `mypy --strict`, pytest, Dockerfile, CI job.
2. Typed Pydantic models for records, scoring model, handoff, and settings ([data contracts](../architecture/data-contracts.md)); loader that parses the existing records.
3. Deterministic scoring and gate evaluation as plain functions, tested against all 15 candidates.
4. LangGraph graph: `scope` → `load_evidence` → `score_and_gate` → `reviewer` (OpenAI, Structured Outputs into `Handoff`) → `portfolio` → `human_decision` interrupt; SQLite checkpointer.
5. Typer CLI `neuroquest review <ids>` printing a Markdown decision packet.
6. LangSmith tracing; token and cost logging from OpenAI usage; per-run budget stop.
7. Evaluation over EV-02–EV-06 and EV-10–EV-13 as pytest tests and a LangSmith dataset.

Out of the first slice: parallel agents, vector search, live connectors, deployment infrastructure, real lab data.

## Tooling changes deferred (need explicit approval)
The current validator was designed for the fixed demonstration corpus. Before the corpus grows:
- Replace fixed record counts (15/20/20/12/10) and the 108-path inventory check with schema-based validation.
- Allow descriptive slugs alongside stable IDs.
- Enforce `rating_evidence` ⇒ completed experiment with the candidate in `measured_candidate_ids`.
- Check `score_history` structure and ADR status values.
- Update GitHub Actions versions and add ruff, mypy, and pytest jobs.
- Raise the ADR count limit so TD-01–TD-10 can become ADR-011 onward.

## Decisions required first
Listed in [TASK.md](../../TASK.md).
