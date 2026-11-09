# NeuroQuest — Alzheimer’s research decision support (design package)

NeuroQuest is a proposed assistant that turns an Alzheimer’s research question into a traceable, human-reviewed decision packet. This repository holds its **design documentation** and a **synthetic demonstration corpus**. There is no application code yet. Current phase: [STATUS.md](STATUS.md). Overview: [PROJECT.md](PROJECT.md).

## Repository layout
```text
CLAUDE.md  TASK.md  STATUS.md  GOALS.md  DECISIONS.md  MEMORY.md  PROJECT.md   control plane
roles/          role contracts (researcher, reviewer, planner, regulatory, portfolio)
molecules/      15 SYNTHETIC candidate profiles          ┐
experiments/    20 SYNTHETIC experiment records          │ evidence layer
literature/     20 real publications (abstract-level)    │ (index README + small
knowledge/      pathways, research strategy, landscape   │  CLAUDE.md rules per folder)
regulatory/     dated FDA references and gap assessment  │
memory/         12 fictional campaign periods            ┘
adr/            proposed architecture decision records
docs/           product/, architecture/, delivery/, context guide, glossary
runbooks/  workflows/  config/   procedures and descriptive contracts
.claude/        Claude Code skills, commands, Stop hook
scripts/  tests/  offline repository validator and its tests
```

## Reviewing the design
Follow [TASK.md](TASK.md): it lists the owner decisions required and the review order. The [documentation index](docs/README.md) maps every design document.

## Working with Claude Code
[CLAUDE.md](CLAUDE.md) is the only auto-loaded instruction file at startup; everything else loads on demand through indexes ([context guide](docs/context-guide.md)).

| Invocation | Purpose |
| --- | --- |
| `/research-status` | Summarize task, status, and next action |
| `/neuroquest-review A G N` | Compare synthetic candidates and check gates |
| `/neuroquest-evidence <claim>` | Map a scientific claim to sources and counterevidence |
| `/neuroquest-plan <candidate> <gap>` | Propose a study concept (not execution) |
| `/validate-research` | Run the offline validator and tests |

A Stop hook runs the validator when Claude finishes a turn; details and limits: [Claude setup](docs/claude-code.md).

## Local checks
Python 3.10+, standard library only; no credentials or network needed.
```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
```
They check links, labels, record IDs, score arithmetic, gates, and file-size budgets. They do not establish scientific truth, source currency, or design approval.

## Configuration
[.env.example](.env.example) lists placeholders; copy with `cp -n .env.example .env`. Nothing reads `.env` today, and it is git-ignored. [config/](config/README.md) holds descriptive contracts (scoring, context budgets, disabled integrations); native Claude settings live in `.claude/settings.json`.

## Data and licensing
Candidate, experiment, and history records are **SYNTHETIC DEMONSTRATION** data. Literature summaries cite real publications, which keep their own terms. No repository license is specified yet.
