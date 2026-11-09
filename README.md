# NeuroQuest — Alzheimer’s research decision support

NeuroQuest is an assistant that turns an Alzheimer’s research question into a traceable, human-reviewed decision packet. This repository holds the application (`src/neuroquest`, first slice), its **design documentation**, and a **synthetic demonstration corpus**. Stack: Python 3.13, Pydantic, LangGraph, OpenAI ([tech-stack](docs/architecture/tech-stack.md)). Current phase: [STATUS.md](STATUS.md). Overview: [PROJECT.md](PROJECT.md).

## Repository layout
```text
CLAUDE.md  TASK.md  STATUS.md  GOALS.md  DECISIONS.md  MEMORY.md  PROJECT.md   control plane
roles/          role contracts (researcher, reviewer, planner, regulatory, portfolio)
molecules/      15 SYNTHETIC candidate profiles          ┐
experiments/    20 SYNTHETIC experiment records          │ evidence layer
literature/     23 real publications (abstract-level)    │ (index README + small
knowledge/      pathways, research strategy, landscape   │  CLAUDE.md rules per folder)
regulatory/     dated FDA references and gap assessment  │
memory/         12 fictional campaign periods            ┘
adr/            decision records (all accepted; 012 superseded by 021)
src/neuroquest/ application: models, scoring, LangGraph run, OpenAI client, CLI
tests/app/      offline application tests (pytest)   · pyproject.toml, uv.lock, Dockerfile
docs/           product/, architecture/, delivery/, context guide, glossary
runbooks/  workflows/  config/   procedures and descriptive contracts
.claude/        Claude Code skills, commands, Stop hook
scripts/  tests/  offline repository validator and its tests (stdlib)
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

## Run the application
Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.13) or Docker. Fill `.env` from [.env.example](.env.example): `OPENAI_API_KEY`, model IDs, and `NEUROQUEST_MODEL_PRICES`.
```sh
uv sync
uv run neuroquest review A G N                      # packet + run_id; pauses for your decision
uv run neuroquest decide <run_id> -d A=follow-up -d G=hold -d N=blocked --reason "Exposure first"
uv run neuroquest runs                              # history; `show <run_id>` reprints a packet
uv run pytest                                       # offline tests (no network, no .env)
```
Docker: `docker build -t neuroquest . && docker run --rm -it --env-file .env -v "$PWD":/repo:ro -v neuroquest-var:/var/lib/neuroquest neuroquest review A G N`. Each run is capped at $0.10 (`--budget-usd` to override); a run that would exceed it stops with a partial packet. Design: [application design](docs/architecture/application-design.md).

## Local checks
Repository checks: Python 3.10+, standard library only; no credentials or network needed.
```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
```
They check links, labels, record IDs, score arithmetic, gates, rating evidence, ADR structure, Claude settings (including `.env` deny rules), and file-size budgets; record counts may grow above the minimums in `config/settings.json`. They do not establish scientific truth, source currency, or design approval.

## Configuration
[.env.example](.env.example) lists placeholders (OpenAI, LangSmith, Tavily, model tiers); copy with `cp -n .env.example .env`. Nothing reads `.env` today, and it is git-ignored. [config/](config/README.md) holds descriptive contracts (scoring, context budgets, disabled integrations); native Claude settings live in `.claude/settings.json`.

## Data and licensing
Candidate, experiment, and history records are **SYNTHETIC DEMONSTRATION** data. Literature summaries cite real publications, which keep their own terms. No repository license is specified yet.
