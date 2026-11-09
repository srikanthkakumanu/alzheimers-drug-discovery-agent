# Implementation plan

Planning only. Nothing here is authorized until the owner completes the [review](review-plan.md) and explicitly requests implementation.

## Phases
| Phase | Deliverable | Exit criterion |
| --- | --- | --- |
| 1 Product review | BRD, goals, personas, scope | Owner confirms users and capabilities |
| 2 Design review | Requirements, architecture, contracts, ADRs | Contradictions and assumptions resolved |
| 3 Technology review | Interface, language, coordinator, provider/model tiers, storage | Choices recorded as ADRs; budget agreed |
| 4 Evaluation set-up | Fixed scenarios, human rubric, deterministic checks | Acceptance thresholds and owners agreed |
| 5 First slice | Minimum path below, with tests | Passes agreed scenarios |
| 6 Release review | Measured quality, cost, traceability, residual risks | Owner reviews actual results before expansion |

## First slice (proposed)
Synthetic question → decision packet, end to end:
1. Deterministic loader for candidate, experiment, and literature records (reuse the validator’s parsing rules).
2. Deterministic scoring and gate evaluation from [scoring-model.json](../../config/scoring-model.json).
3. One reviewer-style LLM step producing the handoff schema in [agent design](../architecture/agent-design.md), with schema validation.
4. A portfolio-style packet rendered for a human; no decision recording yet.
5. Token and cost logging from provider usage data; per-run budget stop.
6. Evaluation run over EV-02 to EV-06 and EV-10 to EV-13.

Out of the first slice: parallel agents, vector search, live connectors, deployment infrastructure, real lab data.

## Tooling changes deferred (need explicit approval)
The current validator was designed for the fixed demonstration corpus. Before the corpus grows:
- Replace fixed record counts (15/20/20/12/10) and the 108-path inventory check with schema-based validation.
- Allow descriptive slugs alongside stable IDs.
- Enforce `rating_evidence` ⇒ completed experiment with the candidate in `measured_candidate_ids`.
- Check `score_history` structure and ADR status values.
- Update GitHub Actions versions as part of CI maintenance.

## Decisions required first
Listed in [TASK.md](../../TASK.md).
