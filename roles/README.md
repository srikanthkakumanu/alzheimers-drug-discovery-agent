# Role index

Roles are written responsibility contracts used by an operator or a Claude skill. They are **not** registered Claude subagents (those would live in `.claude/agents/`) and not running services. Load one role per task; load its `MEMORY.md` only for historical questions.

| Role | Use when | Typical next role | Suggested model tier |
| --- | --- | --- | --- |
| [Researcher](researcher/CLAUDE.md) | Map a claim to supporting and conflicting sources | Reviewer | Economical; capable for conflicting trials |
| [Reviewer](reviewer/CLAUDE.md) | Check provenance, artifacts, replication, score arithmetic, gates | Planner or Researcher | Economical (arithmetic is deterministic) |
| [Planner](planner/CLAUDE.md) | Design the smallest study that could change a decision | Regulatory or Portfolio | Capable |
| [Regulatory](regulatory/CLAUDE.md) | Assess stage-specific evidence and guidance gaps | Portfolio | Capable |
| [Portfolio](portfolio/CLAUDE.md) | Compare options and prepare the human decision packet | Human owner | Capable |

Skip roles the question does not need. Tiers map to OpenAI models set in configuration ([tech-stack](../docs/architecture/tech-stack.md), ADR-015).

## Shared rules (apply to every role)
Root [CLAUDE.md](../CLAUDE.md) rules always apply. In addition:
- Open at most 3 new records per batch, then reassess.
- Keep scenario observations labeled **SYNTHETIC DEMONSTRATION**; published papers are background, never evidence about a synthetic candidate.
- Do not change evidence, gate, or approval fields unless the user asks for a repository update.

## Handoff schema (≤400 estimated tokens)
```text
question:     one sentence
records:      IDs consulted (e.g. candidate-A, EXP-014, paper-012)
finding:      supported conclusion, with provenance labels
uncertainty:  disputed or missing evidence; gate states
next_action:  one recommended step and its owner
```
Link records; do not paste them. Full contract: [agent design](../docs/architecture/agent-design.md).

## Role memory maintenance
Add a short dated lesson only after evidence review, link its primary record, keep counterevidence, and delete superseded lines. Observations belong in experiment records, not memory.
