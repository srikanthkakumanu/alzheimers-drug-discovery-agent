# Agent design — roles, graph, handoffs

Design only; nothing is implemented. Role contracts: [roles/](../../roles/README.md). Decision: [ADR-004](../../adr/ADR-004.md); technology: LangGraph (TD-04), OpenAI SDK (TD-05), Pydantic (TD-03) in [tech-stack](tech-stack.md).

## Role I/O
| Role | Input | Output | Must not infer |
| --- | --- | --- | --- |
| Researcher | Question, source scope, selected papers | Claim–source map, counterevidence, access limits | That an abstract is a full-methods review |
| Reviewer | Claims, candidate and experiment records, scoring contract | Supported/disputed claims, arithmetic, gate states | That a high score resolves failed evidence |
| Planner | Reviewed gap, intended decision | Study concept, prerequisites, outcome branches, stop conditions | That a proposed study has results or authorization |
| Regulatory | Intended stage, applicable evidence | Dated source, applicability, gap assessment | That guidance or model output is approval |
| Portfolio | Reviewed findings, proposals, gaps | Decision packet for the human owner | That a recommendation is a disposition |

## LangGraph design
| Node | Kind | Model tier |
| --- | --- | --- |
| `scope` | Deterministic: parse question, resolve IDs, pick needed roles | — |
| `load_evidence` | Deterministic: load records into Pydantic models; FTS5 search | — |
| `score_and_gate` | Deterministic: formula, gates, hard blocks | — |
| `researcher`, `reviewer` | LLM | Economical; capable when evidence conflicts |
| `planner`, `regulatory`, `portfolio` | LLM | Capable; escalation tier only on a flagged hard conflict |
| `budget_check` | Deterministic: stop with a partial result when exhausted | — |
| `human_decision` | `interrupt()` — waits for an authenticated person | — |

- **State:** a `TypedDict` (`RunState`) whose fields hold Pydantic models (`Handoff`, `Candidate`, `ToolResult`) plus a typed budget counter; each node is typed `(RunState) -> partial RunState`.
- **Edges:** conditional edges skip roles the question does not need; reviewer → researcher is allowed once per specific conflict; any hard block or budget stop routes to the end with status `blocked` or `partial`.
- **Checkpointing:** SQLite checkpointer, so a run pauses at `human_decision` and resumes later; LangSmith traces every node.

## Run lifecycle
```text
requested → scoped → evidence_reviewed → assessed → recommendation_ready → awaiting_human → closed
                ↑            │
                └── gap ─────┘          any state → partial | blocked  (budget, tool failure, hard block)
```
Never loop to obtain a more favorable scientific conclusion. Iteration and retry limits are configuration values.

## Handoff contract (`Handoff` Pydantic model)
| Field | Type / content |
| --- | --- |
| `run_id`, `step` | `str`, `Literal` role name |
| `question` | One sentence |
| `record_ids` | `list[RecordId]` with versions |
| `finding` | Conclusion with provenance labels (published / synthetic / inference / proposal) |
| `uncertainty` | Disputed or missing evidence; `dict[GateName, GateState]` |
| `next_action` | One step and its owner |
| `budget_remaining` | Tokens and cost left |

LLM nodes pass this model to OpenAI Structured Outputs and re-validate the reply; one retry, then a typed failure. Narrative ≤400 estimated tokens; link records instead of pasting them.

## Principles
Sequential by default; parallel branches only with measured quality-per-cost benefit. The reviewer owns claim acceptance within a packet; the human owns consequential dispositions. Retry only transport failures within budget. Acceptance scenarios: [evaluation plan](../delivery/evaluation-plan.md).
