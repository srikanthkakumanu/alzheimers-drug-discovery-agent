# Observability and LLM cost controls

Design proposal. No telemetry, billing collection, or enforced budget exists today. Requirements: NFR-04, NFR-05, NFR-09. Selected tools: LangSmith tracing and datasets, OpenAI usage data, pytest (ADR-015, ADR-018).

## Signals to capture (future runtime)
| Signal | Purpose | Exclude |
| --- | --- | --- |
| Run and step transitions, final status | Explain work done, gaps, stop reasons | Unrestricted transcripts |
| Tool request/result metadata | Trace sources, failures, retries, freshness | Credentials, unnecessary raw source text |
| Model, prompt-template, and tool versions | Reproducibility | Private prompt content by default |
| Input / output / cached-input tokens, latency (from OpenAI `usage`) | Real cost and speed | Estimated or assumed values |
| Evidence and gate changes | Audit current vs historical interpretation | Generated approval identities |

## Cost levers, in order of expected impact
| Lever | How | Where defined |
| --- | --- | --- |
| Layered loading | Load L0–L1 always, then one role, one index, ≤3 records | [context guide](../context-guide.md) |
| Deterministic tools | IDs, arithmetic, gates, schema checks outside the model | [architecture](architecture.md) |
| Skip unneeded roles | Coordinator runs only steps the question requires | [agent design](agent-design.md) |
| Model tiering | Economical model for routing/extraction/formatting; capable model for conflicting evidence and synthesis | [roles](../../roles/README.md) |
| Prompt caching | OpenAI caches long repeated prompt prefixes automatically: put stable content first (rules → role → index), the question last; measure `cached_tokens` | Context guide |
| Bounded outputs | Structured handoffs ≤400 tokens; links instead of pasted records | Agent design |
| Reuse reviewed summaries | Literature summaries before full text; full text only for unresolved, high-impact claims | Researcher role |
| Batch offline work | Run large evaluation suites through OpenAI’s Batch API where turnaround allows | [evaluation plan](../delivery/evaluation-plan.md) |

## Budget policy (to be set by owner)
Before implementation, agree: maximum tokens or cost per run and per month, pricing source and date, allowed retrieval batches and role iterations, retry limits, and exhausted-budget behavior (partial result with open questions). A blank `NEUROQUEST_MONTHLY_BUDGET_USD` means unset, not unlimited.

Compute cost only from provider-reported usage and the prices in force at the time. Track model, tool, and infrastructure costs separately. Byte-based token estimates are for file discipline only.

## Today
[config/settings.json](../../config/settings.json) holds file-size budgets (validator-enforced) and manual LLM policy. Nothing enforces run-level tokens, latency, or spend. Compare any added complexity (parallel agents, vector search, frameworks) against the sequential baseline on both quality and cost.
