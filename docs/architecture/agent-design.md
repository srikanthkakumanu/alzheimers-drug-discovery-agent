# Agent design — roles, lifecycle, handoffs

Design only; no coordinator or native subagents exist. Role contracts: [roles/](../../roles/README.md). Decision: [ADR-004](../../adr/ADR-004.md).

## Role I/O
| Role | Input | Output | Must not infer |
| --- | --- | --- | --- |
| Researcher | Question, source scope, selected papers | Claim–source map, counterevidence, access limits | That an abstract is a full-methods review |
| Reviewer | Claims, candidate and experiment records, scoring contract | Supported/disputed claims, arithmetic, gate states | That a high score resolves failed evidence |
| Planner | Reviewed gap, intended decision | Study concept, prerequisites, outcome branches, stop conditions | That a proposed study has results or authorization |
| Regulatory | Intended stage, applicable evidence | Dated source, applicability, gap assessment | That guidance or model output is approval |
| Portfolio | Reviewed findings, proposals, gaps | Decision packet for the human owner | That a recommendation is a disposition |

## Run lifecycle (proposed)
```text
requested → scoped → evidence_reviewed → assessed → recommendation_ready → awaiting_human → closed
                ↑            │
                └── gap ─────┘          any state → partial | blocked  (budget, tool failure, hard block)
```
- Incomplete input returns to `scoped`; a specific evidence conflict returns to review once per conflict.
- Never loop to obtain a more favorable scientific conclusion.
- Iteration limits and retry counts are configuration values set during implementation planning.

## Handoff contract
Every step emits a structured object validated before the next transition:

| Field | Content |
| --- | --- |
| `run_id`, `step` | Run identifier and role |
| `question` | One sentence |
| `record_ids` | IDs consulted, with record versions in a future runtime |
| `finding` | Conclusion with provenance labels (published / synthetic / inference / proposal) |
| `uncertainty` | Disputed or missing evidence; gate states |
| `next_action` | One recommended step and its owner |
| `budget_remaining` | Tokens or cost left (future runtime) |

Narrative portion ≤400 estimated tokens; link records instead of pasting them.

## Coordination principles
- Sequential by default; a role is a responsibility, not necessarily a separate model call.
- Parallel fan-out only with a measured quality-per-cost benefit.
- The reviewer owns claim acceptance within a packet; the human owner owns consequential dispositions.
- Retry only recoverable transport failures within budget; a negative result is evidence, not an error.

Acceptance scenarios: [evaluation plan](../delivery/evaluation-plan.md).
