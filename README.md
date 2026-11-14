# NeuroQuest — Alzheimer’s research decision support

NeuroQuest turns Alzheimer’s research questions into traceable, human-reviewed decision packets: compare candidates, check evidence and gates, and recommend next steps.

> Candidate, experiment, and campaign-history records are **SYNTHETIC DEMONSTRATION** data. Literature summaries cite real publications. No candidate is approved or promoted.

**Stack:** Python 3.13 · Pydantic · Typer · LangGraph · SQLite · Groq / Gemini / Mistral / OpenAI. [Current status](STATUS.md) · [Project overview](PROJECT.md) · [Stack decisions](docs/architecture/tech-stack.md)

## Architecture

One process coordinates two sequential LLM roles and a human decision. Scores, gates, IDs, and allowed dispositions are computed in Python.

```mermaid
flowchart TB
    Owner(["Researcher / decision owner"])
    subgraph App["NEUROQUEST · CLI application"]
        CLI["Typer CLI"] --> Service["ReviewService<br/>Preflight · lifecycle · packets"]
        Service --> Graph["LangGraph workflow<br/>Tools → Reviewer → Portfolio → Human"]
        Guard["Checks: schemas · citations · gates"] -.-> Graph
    end
    subgraph Data["EVIDENCE & STATE"]
        Records[("Git records<br/>Markdown + JSON")]
        Runs[("neuroquest.sqlite3<br/>Runs · steps · decisions")]
        State[("checkpoints.sqlite3<br/>Resumable graph state")]
    end
    Models["External model providers<br/>Groq · Gemini · Mistral · OpenAI"]
    Owner --> CLI
    Records --> Graph
    Graph <-->|"LLM adapter"| Models
    Service --> Runs
    Graph <--> State
    classDef dark fill:#0f172a,color:#fff,stroke:#0f172a
    classDef blue fill:#e0f2fe,color:#0c4a6e,stroke:#0284c7
    classDef violet fill:#ede9fe,color:#4c1d95,stroke:#8b5cf6
    classDef green fill:#dcfce7,color:#14532d,stroke:#16a34a
    class Owner,CLI,Service dark
    class Graph,Guard blue
    class Models violet
    class Records,Runs,State green
    style App fill:#f8fafc,stroke:#94a3b8
    style Data fill:#f0fdf4,stroke:#86efac
```

| Component | Responsibility |
| --- | --- |
| [CLI](src/neuroquest/cli.py) | Commands and output. |
| [Service](src/neuroquest/service.py) | Run lifecycle and decisions. |
| [Repository](src/neuroquest/repository/loader.py) | Validate records, resolve IDs, select evidence. |
| [Scoring](src/neuroquest/scoring.py) | Scores, gates, allowed dispositions. |
| [Graph](src/neuroquest/graph/build.py) | Workflow, checks, human pause. |
| [LLM adapters](src/neuroquest/llm/) | Providers, prompts, fake client. |
| [Storage](src/neuroquest/storage/db.py) / [renderer](src/neuroquest/packet.py) | History and Markdown packets. |

### From question to decision

```mermaid
flowchart LR
    A["Assess<br/>Scores + gates"] --> B["Select<br/>Experiments"]
    B --> C["Reviewer LLM<br/>Claims + gaps"]
    C --> D["Portfolio LLM<br/>Next steps + study"]
    D --> E["Enforce gates<br/>Render packet"]
    E --> F["Await human<br/>Save checkpoint"]
    F --> G["decide<br/>Record + close"]
    C -. "Failure / budget" .-> P["Partial packet"]
    D -. "Failure / budget" .-> P
    classDef tool fill:#e0f2fe,color:#0c4a6e,stroke:#0284c7
    classDef ai fill:#ede9fe,color:#4c1d95,stroke:#8b5cf6
    classDef human fill:#fef3c7,color:#78350f,stroke:#d97706
    classDef failure fill:#fff1f2,color:#881337,stroke:#e11d48
    class A,B,E tool
    class C,D ai
    class F,G human
    class P failure
```

The **reviewer** identifies supported observations, disputes, and gaps from selected candidate and experiment records. The **portfolio** role recommends dispositions and one informative next study.

**Gates beat scores and model output.** Failed gates or hard blocks allow only `blocked`; unknown gates prevent advancement. The CLI never offers promotion. Pydantic validates outputs; reviewer citations to unseen records are removed, and identical supported/disputed claims stay disputed. These checks do not establish scientific truth.

### Evidence, persistence, and controls

- **Evidence:** Markdown + JSON frontmatter in Git. Selection uses record references. Papers are loaded but not automatically sent to the reviewer; search is deferred.
- **History:** `var/neuroquest.sqlite3` stores runs, validated handoffs, usage, costs, packets, and append-only decisions. Decisions include actor, reason, time, and the reviewed packet’s hash.
- **Resume:** `var/checkpoints.sqlite3` stores graph state. A later `decide` invocation resumes the human pause without a model call. Candidate files are not modified.
- **Prompts:** shared rules + `roles/<role>/CLAUDE.md` + output schemas. Evidence is delimited as untrusted data; prompt versions are hashed.
- **Cost:** [settings](src/neuroquest/settings.py) supply models, keys, prices, and the $0.10 default cap. Pre-call estimates and reported usage track spend; failures yield partial packets. LangSmith tracing is optional.
- **Deployment:** local CLI or non-root Docker, read-only repo mount, persistent state volume. No HTTP server or queue.

**Built:** reviewer → portfolio → human, scoring, checks, persistence, history. **Planned:** researcher/planner/regulatory nodes, FTS5, `evidence`/`plan`, research connectors. [STATUS.md](STATUS.md) tracks implementation; [application design](docs/architecture/application-design.md) includes future scope.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/neuroquest/`, `tests/app/` | Application and offline tests |
| `molecules/`, `experiments/`, `literature/` | Candidates, experiments, publications |
| `knowledge/`, `regulatory/`, `memory/` | Biology, gaps, fictional campaign history |
| `roles/`, `.claude/` | Role contracts and assistant customization |
| `docs/`, `adr/` | Design documentation and decisions |
| `config/`, `workflows/`, `runbooks/` | Contracts and procedures |
| `scripts/`, `tests/` | Repository validator, checks, Docker scripts |

## Run the application

Requires [uv](https://docs.astral.sh/uv/) (installs Python 3.13) or Docker. Copy [.env.example](.env.example) to `.env`; configure keys for your providers, model IDs, and `NEUROQUEST_MODEL_PRICES`.

```sh
uv sync
uv run neuroquest review A G N   # packet + run_id; pauses for a decision
uv run neuroquest decide <run_id> -d A=follow-up -d G=hold -d N=blocked --reason "Exposure first"
uv run neuroquest runs           # history; show <run_id> reprints a packet
uv run pytest                   # offline application tests
```

Docker: `scripts/start.sh` builds and starts the container; run `docker exec neuroquest neuroquest review A G N`. `scripts/stop.sh` keeps history in the `neuroquest-var` volume (`--purge` deletes it). Use the read-only `.env` mount: `docker --env-file` breaks quoted price JSON. Override the cap with `--budget-usd`.

## Working with Claude Code

[CLAUDE.md](CLAUDE.md) routes assistants through task/status → role → index → selected records. See [context guide](docs/context-guide.md) and [Claude setup](docs/claude-code.md).

| Invocation | Purpose |
| --- | --- |
| `/research-status` | Current task, status, next action |
| `/neuroquest-review A G N` | Compare candidates and check gates |
| `/neuroquest-evidence <claim>` | Sources and counterevidence |
| `/neuroquest-plan <candidate> <gap>` | Study concept |
| `/validate-research` | Offline checks |

Assistant commands are separate from the CLI. A Stop hook runs validation. [TASK.md](TASK.md) lists owner decisions; [docs](docs/README.md) indexes the design.

## Local checks

Python 3.10+, standard library only:

```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
```

Checks cover links, IDs, scores, gates, evidence, ADRs, settings, and context budgets. App tests use a fake LLM; live evaluations are opt-in.

## Configuration and licensing

The app reads git-ignored `.env`; assistants must not read it. [config/](config/README.md) holds contracts. Code and docs use the [MIT License](LICENSE); publications retain their own terms.
