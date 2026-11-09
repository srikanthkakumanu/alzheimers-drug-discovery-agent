# NeuroQuest — project overview

On-demand overview; it is not auto-loaded. Phase: [STATUS.md](STATUS.md).

## Problem
Alzheimer’s research decisions draw on heterogeneous evidence: published trials and mechanism studies, internal assay results, safety screens, and regulatory references. Composite rankings tend to hide artifacts, failed replications, and missing exposure data. Reviewers need a compact, traceable packet that shows what the evidence supports, what conflicts with it, and which next study would change the decision.

## Intended product
A decision-support assistant that turns a bounded research question into a **human-reviewed decision packet**: sourced claims with counterevidence, candidate ratings with explicit unknowns, independent evidence gates, a proposed next study, and the human decision still required. It does not run experiments, approve candidates, or give clinical advice.

| Users | Primary need |
| --- | --- |
| Research scientist / reviewer | Defensible, source-linked assessment of a claim or candidate |
| Program decision owner | Clear options, uncertainty, and accountability for the next action |

## Repository contents
| Layer | Contents |
| --- | --- |
| Control plane | [CLAUDE.md](CLAUDE.md), [TASK.md](TASK.md), [STATUS.md](STATUS.md), [GOALS.md](GOALS.md), [DECISIONS.md](DECISIONS.md), [MEMORY.md](MEMORY.md) |
| Procedures | [roles](roles/README.md), Claude skills/commands ([setup](docs/claude-code.md)), [runbooks](runbooks/README.md), [workflow contract](workflows/README.md) |
| Evidence | [candidates](molecules/README.md), [experiments](experiments/README.md), [literature](literature/README.md), [knowledge](knowledge/README.md), [regulatory](regulatory/README.md), [campaign history](memory/README.md) |
| Design | [docs](docs/README.md): product, architecture, delivery, context engineering |
| Contracts and checks | [config](config/README.md), `scripts/`, `tests/`, `.claude/` |

Candidate, experiment, and history records are **SYNTHETIC DEMONSTRATION** data used as acceptance scenarios. Publications are real and summarized at abstract level. No compound, study, clinical benefit, or regulatory status is asserted.

## Not yet built
Application coordinator, LLM integration, live literature connectors, persistent run and approval records, enforced budgets, and model-behavior evaluation. See the [implementation plan](docs/delivery/implementation-plan.md).
