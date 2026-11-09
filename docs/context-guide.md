# Context engineering and LLM cost policy

How this repository keeps model context small, relevant, and cheap. Decision: [ADR-003](../adr/ADR-003.md). Authoritative budget values: [config/settings.json](../config/settings.json).

## Layers
Token figures are `ceil(bytes / 4)` estimates measured on 2026-11-09. This is a file-discipline heuristic, not a tokenizer or a billing figure.

| Layer | Content | Loaded | Measured | Budget (validator) |
| --- | --- | --- | --- | --- |
| L0 | Root `CLAUDE.md`: rules + router | Every turn, automatically | ~660 tok | ≤3,200 B |
| L1 | `TASK.md` + `STATUS.md` | Start of each task | ~910 tok | ≤8,000 B each |
| L2 | One role contract (+ shared role index if needed) | Research/review tasks | ~250–300 tok per role (+~550 index) | ≤2,400 B |
| L3 | One directory `README.md` | To pick IDs | ~590–630 tok | ≤6,000 B |
| L4 | Records, ≤3 per batch; directory `CLAUDE.md` rules auto-load once | Only what the claim needs | Candidate ~620, experiment ~390, paper ~270; rules ~190–250 | ≤8,000 B each; rules ≤2,400 B |
| Ref | `docs/` design documents | Design questions only | — | ≤8,000 B |

Skill descriptions (3) and command descriptions (2) are always visible to Claude; a skill body (~370 tokens) loads only when invoked.

**Measured bundles:** session start (L0 + L1) ≈ 1,570 tokens, under the 2,500 target. Full A/G/N review (L0–L4 with skill, role, index, 3 candidates, 3 experiments, rules) ≈ 6,700 tokens, slightly over the 6,000 working target; open the third experiment only if the first two leave the dispute unresolved.

## Retrieval protocol
1. Name the decision and the unresolved claim before reading evidence.
2. Pick IDs from an index; open up to 3 records; reassess before opening more.
3. Prefer a dated summary when its scope answers the question; open source methods only for unresolved, high-impact claims, and record access limits.
4. Stop when the question is answered or the missing evidence is identified. Do not spend tokens speculating past missing data.

## Model tiering (proposal; no provider selected)
| Work | Tier |
| --- | --- |
| Routing, ID lookup, extraction, formatting | Economical model, or no model (deterministic tool) |
| Score arithmetic, gate checks, schema validation | No model |
| Conflicting evidence, scientific or regulatory synthesis, study design | Capable model; record why it escalated |

## Prompt caching (future runtime)
Order prompts from most stable to least: L0 rules → role contract → index → selected records → question. Cache the stable prefix where the provider supports it, and measure cache reads; never assume savings. Keep volatile values (dates, run IDs) out of the cached prefix.

## Handoffs and memory
Handoff: question · record IDs · finding · uncertainty/gates · next action, ≤400 tokens, links instead of pasted records ([schema](../roles/README.md)). Durable accepted lessons go in [MEMORY.md](../MEMORY.md) or role `MEMORY.md` as one line with a link; details stay in primary records. Start a fresh session when the current one is no longer useful instead of carrying a long transcript.

Example: “Compare A/G follow-up. Synthetic EXP-014 reproduces both directionally; A stronger but preparation-sensitive (EXP-018). No identity-qualified material, measured free CNS exposure, or direct engagement. N blocked by failed replication. Next: propose minimum A/G exposure/engagement evidence; no promotion.”

## Anti-patterns
Recursive directory reads · `@` imports in `CLAUDE.md` · repeating phase or disclaimer text in every file (state it once, in `STATUS.md` or a directory `CLAUDE.md`) · pasting full records into handoffs · loading history or design docs for an evidence question · caching credentials, private data, or copyrighted full text.

## What is enforced
The validator enforces per-file byte budgets and forbids `@` imports in `CLAUDE.md`. Bundle sizes, batch limits, model choice, and spend are manual policy until a runtime enforces them ([cost design](architecture/observability-and-cost.md)).
