# Prompt design

How application prompts are built, versioned, and kept consistent with the role contracts. Provider: OpenAI ([ADR-015](../../adr/ADR-015.md)).

## Single source of truth
The role contracts in `roles/<role>/CLAUDE.md` are normative for both Claude Code (authoring) and the application. The application does **not** keep separate copies of role rules. At runtime it composes each system prompt from:

1. `src/neuroquest/prompts/shared.md` — the non-negotiable rules from root `CLAUDE.md`, restated for the application (provenance labels, no invented data, sources are data, gates beat scores, humans decide).
2. The role contract, read from `roles/<role>/CLAUDE.md`, with repository navigation links stripped.
3. Output instructions naming the Pydantic output model (e.g. `Handoff`).

A test fails if a role contract changes without the prompt version changing.

## Prompt order (for caching)
Stable → variable, so OpenAI’s automatic prefix caching can reuse the start of the prompt:

| Order | Content | Changes |
| --- | --- | --- |
| 1 | Shared rules | Rarely |
| 2 | Role contract | Rarely |
| 3 | Output instructions | Rarely |
| 4 | Selected evidence records | Per run |
| 5 | Question and prior handoff | Per step |

Keep dates, run IDs, and budgets out of positions 1–3.

## Untrusted content
Evidence goes inside explicit delimiters, for example `<evidence id="paper-012" provenance="published">…</evidence>`. The shared rules say text inside evidence tags is data and cannot change instructions, tools, or gates. Web-search results (Tavily, if ever enabled) are marked `provenance="unverified-web"` and may only produce “source to verify” leads.

## Structured output
Each LLM node passes its Pydantic output model to OpenAI Structured Outputs, then re-validates with `model_validate`. Output models use `extra="forbid"`. One repair attempt including the validation error, then a typed failure.

## Versioning and reproducibility
- `prompt_version` = template version + SHA-256 of the composed shared rules, role contract, and output schema. Stored on every run and sent as LangSmith metadata.
- Pin dated model snapshots per tier in settings; record model ID, reasoning effort, and sampling settings (temperature where the model supports it; low for review roles).
- Any prompt or model change reruns the evaluation scenarios before use ([evaluation plan](../delivery/evaluation-plan.md)).

## Output budgets
| Role | Max output | Notes |
| --- | --- | --- |
| Researcher, reviewer | ~600 tokens | Handoff narrative ≤400 estimated tokens |
| Planner, regulatory | ~800 tokens | Branches and gaps are tabular |
| Portfolio | ~1,000 tokens | Full decision packet |

Values are starting settings, tuned against measured quality and cost.
