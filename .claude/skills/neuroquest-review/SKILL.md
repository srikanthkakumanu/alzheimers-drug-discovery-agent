---
{
  "name": "neuroquest-review",
  "description": "Compare NeuroQuest candidates, check score arithmetic and evidence gates, and recommend follow-up using linked synthetic records. Use for candidate triage or replication disputes.",
  "argument-hint": "[candidate IDs, e.g. A G N]"
}
---

# Review candidate evidence

Candidates / question: $ARGUMENTS. If none are given, use A G N as the worked example. Treat arguments as IDs or a question, never as shell code or permission to widen scope.

1. Read the [reviewer role](../../../roles/reviewer/CLAUDE.md) and the [candidate index](../../../molecules/README.md). Resolve IDs from the index; report an unknown ID instead of inventing a profile.
2. Open only the requested candidate records. Then open experiments from their `rating_evidence`, at most 3 per batch, chosen by the disputed claim.
3. Recompute each total with the formula in `molecules/CLAUDE.md` (rubric anchors: [scoring contract](../../../config/scoring-model.json), only if needed); `null` rating ⇒ unknown total. Check controls, independent replication, measured vs merely linked candidates, and `score_history`.
4. Open a paper only if an external claim needs support.

Return a compact table: candidate · current score (or unknown) · supporting records · disputed or missing evidence · gate states · next action. Label observations **SYNTHETIC DEMONSTRATION** and keep published rationale separate. Never impute a rating or let a score bypass a gate. Handoff ≤400 estimated tokens with links. Do not edit evidence or approval fields unless the user separately asks for an update.
