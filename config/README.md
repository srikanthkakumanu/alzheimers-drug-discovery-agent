# Configuration contracts

Descriptive project contracts read by the validator and by people. They are not native Claude Code configuration (that is [.claude/settings.json](../.claude/settings.json); see [Claude setup](../docs/claude-code.md)). Do not copy these into `.claude/settings.json` or `.mcp.json`.

| File | Defines | Read by |
| --- | --- | --- |
| [scoring-model.json](scoring-model.json) | Weights (efficacy 40, safety 30, BBB 20, manufacturing 10), 0–5 rubric, missing-data rule, six promotion gates | Validator, reviewer and portfolio roles |
| [settings.json](settings.json) | Data mode, execution flags (all off), context budgets, manual LLM policy, memory layout | Validator, operator |
| [mcp.json](mcp.json) | Disabled inventory of possible integrations (PubMed, vector store, lab data) | Validator, operator |

## Notes
- `safety` replaces the skeleton’s `toxicity` so that every dimension is higher-is-better (`legacy_mapping` records this).
- `manufacturing` is a preliminary developability proxy, not CMC readiness.
- Weights and the 70-point threshold are illustrative and unvalidated.
- Context budgets are file-size limits the validator enforces; bundle and spend targets are manual policy ([context guide](../docs/context-guide.md)).
- Environment variable names: [.env.example](../.env.example). Nothing here reads `.env`.
