# Documentation review log

Dated record of documentation passes. Newest first. Scientific content is not re-verified by these passes unless stated.

## 2026-11-09 — Pass 2: layered context restructure and consolidation
**Goal:** apply Claude Code context layering, cut repeated context, improve content depth, without application code or changes to Python tooling.

### Structural changes
| Change | Reason |
| --- | --- |
| Root reduced to the control plane (CLAUDE, README, PROJECT, TASK, STATUS, GOALS, DECISIONS, MEMORY) | Clear entry point; design docs out of the default path |
| `PRODUCT_VISION`, `BRD`, `ROADMAP`, `RISKS`, `requirements` → `docs/product/` | Group by concern |
| `ARCHITECTURE`, `TECH_STACK`, agent/data/tool/security/cost docs → `docs/architecture/` | Group by concern |
| `PLAN` → `docs/delivery/review-plan.md`; implementation and evaluation plans → `docs/delivery/` | Group by concern |
| `RESEARCH_STRATEGY` → `knowledge/research-strategy.md` | Domain knowledge layer |
| `agents/` → `roles/` | Avoid confusion with native `.claude/agents/` subagents |
| New `molecules/`, `experiments/`, `literature/` `CLAUDE.md` | Record rules load only with those records |
| New [glossary](glossary.md) | Define terms once instead of in every record |
| `repository-audit.md` → this log; `file-review.json` (43 KB) removed | Stale per-file notes from pass 1; superseded |
| [Inventory](original-file-inventory.json) updated with current paths and a `relocations` map | Keeps the 108 original files traceable |

### Content changes
- Phase and disclaimer text now appears once, in [STATUS.md](../STATUS.md), instead of in most files.
- Candidate records: summary table, per-dimension rating-evidence table, visible gate line, and context-only experiment list. Data unchanged.
- Experiment records: measured vs linked candidates shown; repeated boilerplate removed. Data unchanged.
- Literature, history, and ADR records: boilerplate removed; identifiers and findings unchanged.
- Role contracts: role-specific checks added; shared rules and handoff schema moved to [roles/README.md](../roles/README.md); model-tier suggestions added.
- New depth: field-level [data contracts](architecture/data-contracts.md), FR→ADR→evaluation traceability, evaluation IDs EV-01–13, risk IDs R-01–12 including citation fabrication and prompt injection, prompt-injection controls, ranked cost levers, model tiering and caching order, owner decision checklist in [TASK.md](../TASK.md).
- ADR-003 updated to describe the layered structure; ADR-004 title aligned with the register.

### Measured effect
All Markdown: ~62.8k → ~59k estimated tokens, plus the 43 KB JSON removed. Session start ≈ 1,570 tokens. A/G/N review bundle ≈ 7,200 → ≈ 6,700 tokens while also loading the new rule files. Detail: [context guide](context-guide.md).

### Unchanged by design
Python validator, tests, Stop hook, `.claude/settings.json`, CI workflow, config JSON, `.env.example`, `.gitignore`, all record IDs and data values. Tooling changes needed for growth are listed in the [implementation plan](delivery/implementation-plan.md).

## 2026-11-09 — Pass 1: documentation audit
Separated project phase from the fictional campaign; rewrote the ten ADRs with specific context, alternatives, and revisit triggers (all proposed); added BRD, requirements, technology options, agent/data/tool contracts, evaluation, governance, cost, and implementation plans; moved N’s disputed 72 into `score_history`; added `rating_evidence` and `measured_candidate_ids`; marked M’s orthogonal gate unknown; clarified that `manufacturing` is a developability proxy. No code changed.
