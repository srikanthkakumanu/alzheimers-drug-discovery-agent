# ADR conventions

Start at the [decision register](../DECISIONS.md) and load only the record you need.

## Format
JSON frontmatter (`id`, `title`, `status`, `decision_type`, `recorded_on`), then: Context · Decision · Alternatives · Consequences · Validation · Revisit · related links. Follows the intent of [Nygard’s ADR format](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

- **Filename:** `ADR-NNN.md`, stable and never reused; the ID must match the filename. Next free ID: ADR-022.
- **Validator rules:** status is one of the lifecycle values below; all six sections are present; non-proposed records carry `reviewed_on`.
- **Type:** distinguishes architecture (context, data, orchestration, integration, memory) from research scope, governance, and tooling. ADR-001 is a research-scope proposal, not an architectural fact.

## Status lifecycle
`proposed` → `accepted` | `rejected`; later `deprecated` or `superseded`. All current ADRs are **accepted** except ADR-012 (**superseded** by ADR-021) and ADR-015 (**superseded** by ADR-022). Superseding records carry `supersedes` / `superseded_by`.

When the owner decides: set the status, add `reviewed_on` and a one-line basis. To reverse an accepted decision, write a new ADR that links the old one and mark the old one `superseded`; never silently rewrite it. Never record a fictional approver or date. Accepting a repository design never implies scientific, ethical, or regulatory approval.
