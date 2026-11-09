# Project memory — durable lessons

Manually curated project record, separate from Claude’s machine-local auto memory. Keep one line per lesson with a link to its primary record. Never store secrets, transcripts, or full papers here.

## Owner direction
- 2026-11-09: Prepare and review documentation and design before any application code. Proposals are not accepted decisions until the owner records them.
- 2026-11-09: Owner requested implementation of the first slice; accepted ADR-001–010; per-run budget $0.10.
- 2026-11-09: Owner selected the stack: Python 3.13 (ADR-021), Pydantic v2 with strict typing, LangGraph, **OpenAI** (not Claude) for the application LLM, SQLite, LangSmith, Docker — [tech-stack](docs/architecture/tech-stack.md).
- 2026-11-09: Learning project (harness engineering, multi-agent orchestration, layered context); keep LLM cost minimal. Providers switched to Groq / Google Gemini / Mistral — [ADR-022](adr/ADR-022.md). License: MIT.

## Application lessons
- 2026-11-09: Without a definition of "claim", the reviewer turned gate names into claims ("has safety") that contradicted its own missing-evidence list. Fixed by claim rules in the [reviewer role](roles/reviewer/CLAUDE.md) and field descriptions in the reply schema; the fix, not a model change, resolved it (both steps already ran on Gemini Flash-Lite via conflict escalation).

## Scenario lessons (SYNTHETIC DEMONSTRATION)
- An optical artifact invalidates a primary efficacy signal (C) — [period 03](memory/month-03.md).
- A safety signal blocks advancement regardless of potency (D) — [period 05](memory/month-05.md).
- Potency does not fix a transport deficit (E) — [period 06](memory/month-06.md).
- Failed independent replication removes a rating from current ranking; the earlier score stays as disputed history (N) — [period 09](memory/month-09.md).
- An invalid assay is not evidence of inactivity (F) — [period 10](memory/month-10.md).
- Follow-up is not promotion; A/G still lack identity, exposure, and engagement evidence — [period 12](memory/month-12.md).

Period index: [memory/README.md](memory/README.md). Design rationale: [DECISIONS.md](DECISIONS.md). Project phase: [STATUS.md](STATUS.md).
