# Documentation index

Design reference layer. Read the one document your question needs. Phase: [STATUS.md](../STATUS.md). Owner review order: [review plan](delivery/review-plan.md).

| Area | Document | Answers |
| --- | --- | --- |
| Product | [vision](product/vision.md) | Why this exists, principles, non-goals |
| | [BRD](product/brd.md) | Personas, use cases UC-01–05, scope |
| | [requirements](product/requirements.md) | FR/NFR with traceability to use cases, ADRs, evaluation |
| | [roadmap](product/roadmap.md) | Evidence-gated milestones |
| | [risks](product/risks.md) | Risk register R-01–12 |
| Architecture | [architecture](architecture/architecture.md) | Current vs target system, context layers, failure handling |
| | [tech-stack](architecture/tech-stack.md) | Selected stack ADR-011–ADR-022 and engineering conventions |
| | [agent-design](architecture/agent-design.md) | Role I/O, run lifecycle, handoff schema |
| | [data-contracts](architecture/data-contracts.md) | Field-level record schemas and invariants |
| | [tools-and-integrations](architecture/tools-and-integrations.md) | Tool capabilities, result envelope, connector policy |
| | [security-and-data-governance](architecture/security-and-data-governance.md) | Data classes, trust boundaries, prompt-injection controls |
| | [observability-and-cost](architecture/observability-and-cost.md) | Telemetry and LLM cost levers |
| | [application-design](architecture/application-design.md) | Code layout, conventions, CLI, SQLite schema, OpenAI failures, Docker |
| | [prompt-design](architecture/prompt-design.md) | Prompt composition from role contracts, caching order, versioning |
| Delivery | [review-plan](delivery/review-plan.md) | Owner review sequence |
| | [implementation-plan](delivery/implementation-plan.md) | Phases, first slice, deferred tooling work |
| | [evaluation-plan](delivery/evaluation-plan.md) | Scenarios EV-01–13, metrics, thresholds |
| | [evaluation-results](delivery/evaluation-results.md) | First live scoring of EV-01–13 and provider findings |
| | [testing-strategy](delivery/testing-strategy.md) | Offline tests, fake LLM, recorded replies, live evaluation |
| Context engineering | [context-guide](context-guide.md) | Layers, budgets, retrieval, model tiering, caching |
| | [claude-code](claude-code.md) | Claude Code surfaces in this repo and how to verify them |
| Reference | [glossary](glossary.md) | Domain and scoring terms |
| History | [review-log](review-log.md) | Documentation passes and what changed |
| | [original-file-inventory.json](original-file-inventory.json) | The 108 originally supplied files and where they now live |
