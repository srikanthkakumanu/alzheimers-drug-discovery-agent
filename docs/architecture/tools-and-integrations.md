# Tools and integration boundaries

Design proposal. [config/mcp.json](../../config/mcp.json) is a disabled inventory; no connector or server is selected. Decision: [ADR-008](../../adr/ADR-008.md).

| Capability | Input → output | Boundary and failure behavior | Deterministic? |
| --- | --- | --- | --- |
| Repository lookup | IDs or query → matching records and versions | Exact ID resolution; never substitute a similar candidate | Yes |
| Candidate arithmetic and gates | Ratings, weights, gates → total or `null`, eligibility | No model-generated imputation | Yes |
| Handoff validation | Step output → valid / errors | Blocks the transition on schema failure | Yes |
| Literature lookup | Bounded question or IDs → metadata, abstract, access scope, links | Public sources first; report rate limits, missing content, retractions | No (external) |
| Evidence search | Query → ranked record references | Optional future index; results are pointers, not new truth | — |
| Lab-data access | Authorized study IDs → qualified read-only evidence | Deferred; requires governance decision | — |
| Decision recording | Packet + authenticated human action → disposition | Separate from model output; never automatic | Yes |

## Tool-result envelope (proposed)
`capability`, `run_id`, `source_id`, `retrieved_at`, `access_scope`, `evidence_refs`, `result` or typed `error`, `complete` (bool). Never include credentials, provider tokens, or unrestricted transcripts.

## Connector policy
- A public API (e.g. PubMed E-utilities) is not an MCP server; select a real implementation and review its capabilities before configuring it. Never invent launch commands or endpoints.
- Add one connector at a time, with its own evaluation cases and access review.
- A vector index must beat the indexed-file baseline on retrieval quality; chunks keep source ID, version, and access scope.

## Reliability and cost
Cache reusable source metadata with provenance and freshness. Bound transport retries and respect source rate limits. An unavailable paper yields an access gap. Repeated negative findings are evidence, not recoverable errors. Security conditions: [data governance](security-and-data-governance.md).
