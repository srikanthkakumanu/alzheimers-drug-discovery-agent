"""Render the human decision packet as Markdown."""

from __future__ import annotations

from collections.abc import Sequence

from neuroquest.budget import usd
from neuroquest.models.handoff import PortfolioPacket, ReviewHandoff
from neuroquest.models.runs import HumanDecision
from neuroquest.models.scoring import Assessment
from neuroquest.scoring import allowed_dispositions

LABEL = "**SYNTHETIC DEMONSTRATION** — fictional candidates and experiments; no real compound or study."


def _score(a: Assessment) -> str:
    if a.computed_score is None:
        return "unknown"
    return f"{a.computed_score:g}"


def render_packet(
    run_id: str,
    question: str,
    assessments: Sequence[Assessment],
    review: ReviewHandoff | None,
    portfolio: PortfolioPacket | None,
    notes: Sequence[str],
    status: str,
    cost_usd: float,
    budget_usd: float,
    decisions: Sequence[HumanDecision] = (),
) -> str:
    lines = [
        f"# Decision packet `{run_id}`",
        "",
        LABEL,
        "",
        f"**Question:** {question}",
        f"**Status:** {status} · **Cost:** ${cost_usd:.4f} of {usd(budget_usd)}",
        "",
        "## Deterministic assessment (authoritative for scores and gates)",
        "",
        "| Candidate | Score | Blocked | Failed gates | Unknown gates | Disputed history | Allowed decisions |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for a in assessments:
        lines.append(
            f"| {a.candidate_id} | {_score(a)} | {'**yes**' if a.is_blocked else 'no'} | "
            f"{', '.join(a.failed_gates) or '—'} | {len(a.unknown_gates)} | "
            f"{', '.join(f'{s:g}' for s in a.disputed_history) or '—'} | "
            f"{', '.join(sorted(allowed_dispositions(a)))} |"
        )
    if review:
        lines += ["", "## Reviewer findings", ""]
        for r in review.reviews:
            lines.append(f"### {r.candidate_id}")
            lines += [
                f"- Supported ({c.provenance}): {c.statement} [{', '.join(c.record_ids)}]" for c in r.supported_claims
            ]
            lines += [
                f"- Disputed ({c.provenance}): {c.statement} [{', '.join(c.record_ids)}]" for c in r.disputed_claims
            ]
            lines += [f"- Missing: {m}" for m in r.missing_evidence]
            lines.append(f"- Next: {r.next_action}")
        if review.uncertainty:
            lines += ["", "**Uncertainty:** " + "; ".join(review.uncertainty)]
    if portfolio:
        lines += [
            "",
            "## Recommendation (not a decision)",
            "",
            portfolio.summary,
            "",
            "| Candidate | Recommended | Rationale | Next step |",
            "| --- | --- | --- | --- |",
        ]
        lines += [
            f"| {r.candidate_id} | {r.recommended_disposition} | {r.rationale} | {r.next_step} |"
            for r in portfolio.recommendations
        ]
        study = portfolio.next_study
        lines += [
            "",
            "## Most informative next study (proposal, no results)",
            "",
            f"- **Candidates:** {', '.join(study.candidate_ids) or 'none'}",
            f"- **Question:** {study.question}",
            f"- **Design:** {study.design}",
            f"- **Decision rule:** {study.decision_rule}",
            f"- **Leaves open:** {'; '.join(study.remaining_gaps) or 'none stated'}",
        ]
        lines += ["", f"**Human decision required:** {portfolio.human_decision_required}"]
    if notes:
        lines += ["", "## Notes", "", *[f"- {n}" for n in notes]]
    if decisions:
        lines += ["", "## Recorded human decisions", ""]
        lines += [
            f"- {d.candidate_id}: **{d.disposition}** by {d.actor} at {d.decided_at:%Y-%m-%d %H:%M} UTC — {d.reason}"
            for d in decisions
        ]
        lines += ["", "Update candidate records manually (molecules/CLAUDE.md); this run does not edit them."]
    return "\n".join(lines) + "\n"
