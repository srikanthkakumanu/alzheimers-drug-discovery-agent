# Technology options — pending owner selection

No application stack is selected. The repository’s Python validator and Claude Code customization are tooling for this design package; they do not fix the application language or LLM provider.

| Layer | Options to evaluate | Decision criteria |
| --- | --- | --- |
| User interface | Operator CLI · internal web app · existing chat surface (e.g. Claude Code skills) | Real user workflow, access needs |
| Application language | Chosen per runtime and integration needs | Team skills, libraries, testing, deployment |
| Coordination | Explicit state machine · agent framework · provider-managed agent runtime | Checkpointing, inspectability, bounded transitions, overhead |
| LLM access | Direct provider SDK · reviewed abstraction layer | Capability, structured output, prompt caching, usage reporting, terms |
| Model tiers | Economical model for routing/extraction; capable model for synthesis | Quality on evaluation set per unit cost |
| Evidence persistence | Versioned files (current) · transactional store | Concurrency, audit history, query needs, retention |
| Retrieval | Index files + full-text search · optional vector layer | Corpus size, attribution, measured relevance gain |
| External tools | Verified API adapters · real MCP servers | Capability boundaries, reliability, maintenance |
| Deployment | Local/internal · managed service | Users, data classification, availability |

## Baseline to beat
A small deterministic coordinator, file-based evidence, index-first retrieval, and one LLM provider with two model tiers. Add a framework, vector search, database, or parallel agents only when an accepted requirement and an evaluation result justify it.

## How to record a selection
For each layer the owner decides, write a new ADR (ADR-011 onward) with: choice, alternatives, version/support evidence, licensing and data implications, cost estimate source, and acceptance checks. Then update the [implementation plan](../delivery/implementation-plan.md) and [STATUS.md](../../STATUS.md).
