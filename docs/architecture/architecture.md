# Architecture — current repository and proposed target

Design proposal for owner review. Related decisions: [ADR-003](../../adr/ADR-003.md), [ADR-004](../../adr/ADR-004.md), [ADR-006](../../adr/ADR-006.md).

## Current state
Versioned Markdown records with JSON frontmatter, descriptive JSON contracts, role contracts, Claude Code skills/commands, and an offline validator wired to a Stop hook and CI. No application server, coordinator, LLM client, vector index, live connector, or persistent run state exists.

## Context architecture (in use today)
The repository is itself a layered context system for an LLM agent. Each layer is loaded only when the layer above routes to it.

```mermaid
flowchart TD
    L0["L0 · CLAUDE.md — rules + router (always loaded)"] --> L1["L1 · TASK.md, STATUS.md — current question and phase"]
    L1 --> L2["L2 · one role contract (roles/*/CLAUDE.md) or a skill"]
    L2 --> L3["L3 · directory index (README.md) — choose IDs"]
    L3 --> L4["L4 · ≤3 records per batch + that directory's CLAUDE.md rules"]
    L1 -. design questions .-> REF["Ref · docs/ (product, architecture, delivery)"]
```

Measured sizes and budgets: [context guide](../context-guide.md).

## Proposed application architecture
```mermaid
flowchart LR
    Q[Research question] --> C[Coordinator · deterministic state machine]
    C --> T[Deterministic tools · ID lookup, scoring, gate check]
    C --> R[Researcher step]
    R --> V[Reviewer step]
    V -->|specific evidence gap| R
    V --> P[Planner step]
    P --> G[Regulatory step]
    G --> F[Portfolio step]
    F --> H[Human disposition]
    E[(Versioned evidence records)] --> T
    T --> R & V
    C --> B[Budget + run trace]
    H --> D[(Decision records)]
```

| Component | Responsibility | LLM? |
| --- | --- | --- |
| Coordinator (LangGraph) | Scope the question, select needed steps, enforce budget and transition rules, stop on block or exhaustion | No |
| Deterministic tools | Resolve IDs, load records, compute scores, evaluate gates, validate handoff schema | No |
| Role steps | Evidence synthesis, critique, study concepts, gap assessment, recommendation | Yes — OpenAI, tiered by role |
| Evidence store | Markdown/JSON records in git; SQLite FTS5 index; SQLite checkpoints and decisions | No |
| Decision recorder | Attributable human disposition tied to a packet version | No (human action) |

Roles are logical steps, not services or mandatory calls. The coordinator skips roles the question does not need. Arithmetic, IDs, and gates never go through model generation.

## Data ownership
Candidate records own current ratings and gates; experiments own observations; literature owns source summaries; ADRs own design rationale; [STATUS.md](../../STATUS.md) owns project phase. Indexes summarize and must be reconciled after primary changes. Schemas: [data contracts](data-contracts.md).

## Failure handling
| Condition | Behavior |
| --- | --- |
| Invalid evidence | Return to reviewer; gate `unknown` or `fail` |
| Missing evidence | Incomplete recommendation listing the gap |
| Hard block | Advancement stops; block shown in the packet |
| Tool or source unavailable | Typed failure with access limit; no invented content |
| Budget exhausted | Explicit partial result with unresolved questions |

Selected stack (TD-01–TD-10): Python 3.12, Pydantic v2 with strict typing, Typer CLI, LangGraph, OpenAI SDK, SQLite, LangSmith, Docker ([tech-stack](tech-stack.md)). No HTTP API or queue in the first version. Cross-cutting: [security](security-and-data-governance.md), [cost](observability-and-cost.md), [evaluation](../delivery/evaluation-plan.md).
