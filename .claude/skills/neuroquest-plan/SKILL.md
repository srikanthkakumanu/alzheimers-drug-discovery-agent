---
{
  "name": "neuroquest-plan",
  "description": "Propose the next informative study concept for a NeuroQuest candidate's unresolved evidence gate. Use after evidence review; it does not execute experiments or authorize advancement."
}
---

# Plan the next evidence question

Candidate and unresolved gate: $ARGUMENTS. If missing, ask for the candidate and the decision the study should inform.

1. Read the [planner role](../../../roles/planner/CLAUDE.md), resolve the ID in the [candidate index](../../../molecules/README.md), and open that candidate.
2. Open only experiments needed to understand the gate; existing proposed records (EXP-016, EXP-019, EXP-020) are starting concepts. If a relied-on claim is disputed, flag it before planning around it.
3. For development-stage questions, read the [FDA reference](../../../regulatory/fda-guidance.md) and name the expert input required.

Propose the smallest study concept that could change the decision: hypothesis · required inputs (and which are missing) · endpoint and control concepts · replication and design uncertainties · outcome branches (supports / weakens / unresolved) · stop conditions. No operational protocol, dosing, invented sample sizes, or results.

Return an evidence-linked proposal and a ≤400-token handoff. Everything stays **proposed**; invoking this skill changes no promotion or approval field.
