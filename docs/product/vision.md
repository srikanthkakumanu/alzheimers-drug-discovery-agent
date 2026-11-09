# Product vision

Draft for owner review.

## Vision
Alzheimer’s research teams can see, in one compact packet, what the evidence supports, what contradicts it, what is unknown, and which next study would most change their decision, with every claim traceable to its source and every decision owned by a person.

## Problem
Evidence is scattered across trials, mechanism papers, internal assays, and guidance documents. Composite rankings hide decisive problems such as assay artifacts, safety signals, failed replication, and missing exposure. LLM assistants can help synthesize, but they can also fabricate citations, blur fiction and fact, and overstate certainty.

## Product principles
1. **Evidence first:** every material claim cites a record or publication and carries a provenance label.
2. **Unknown is a valid answer:** missing data stays null; it is never imputed.
3. **Gates over scores:** a single failed gate outranks any composite score.
4. **Humans decide:** the system recommends; accountable people approve.
5. **Small context, low cost:** load the minimum evidence needed, and do deterministic work (arithmetic, ID lookup, gate checks) outside the model.
6. **Simplest design that works:** add agents, frameworks, or vector search only when evaluation shows they help.

## Initial scope
Tau-focused small-molecule research (proposed in [ADR-001](../../adr/ADR-001.md)), exercised on a **SYNTHETIC DEMONSTRATION** portfolio that contains deliberate failure cases (artifact, safety, replication, invalid assay, untested slot) alongside 20 real publications.

## Non-goals
Autonomous experimentation, molecule design, patient or dosing advice, regulatory submissions, and guaranteed discovery outcomes. Agent count, framework choice, and model provider are means, not goals.

Use cases: [BRD](brd.md). Success criteria: [GOALS.md](../../GOALS.md).
