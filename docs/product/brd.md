# Business requirements — Alzheimer’s research decision support

Draft for owner review. Functional scope only (what and who). Synthetic examples illustrate behavior; no user research or market demand is claimed.

## Domain
Alzheimer’s research decision support. Modules: evidence review, candidate assessment, next-study planning, development-gap review, decision traceability.

## Personas
| ID | Persona | Main job | Main pain addressed |
| --- | --- | --- | --- |
| P-01 | Research scientist / reviewer | Find defensible evidence and assess a candidate claim | Unsupported conclusions, conflicting studies, missing provenance |
| P-02 | Program decision owner | Choose the next informative action and stay accountable | Rankings that hide uncertainty or imply approval |

Planner, regulatory, and portfolio are responsibilities that support these personas, not separate user types.

## Use cases

### UC-01 — Review a scientific claim
**Actor:** P-01. **Happy path:** state a question → inspect supporting and conflicting evidence → receive a sourced conclusion with limitations.
**Exception:** evidence unavailable or insufficient → state the gap and access limit; never invent support.
**Acceptance:** Given a Tau efficacy claim, when the evidence includes a negative trial, then the conclusion includes that trial and distinguishes biomarker change from clinical outcome.

### UC-02 — Assess candidate readiness
**Actor:** P-01. **Happy path:** select candidates → review observations, uncertainty, and gate states → compare justified next actions.
**Exception:** missing, invalid, or disputed evidence → show the limitation and prevent unsupported advancement.
**Acceptance:** Given failed independent replication, when the candidate is assessed, then its earlier score cannot override the failure and its current uncertainty is visible.

### UC-03 — Propose the next informative study
**Actor:** P-01, reviewed by P-02. **Happy path:** identify an unresolved question → compare study concepts and their possible outcomes → recommend the most informative next action.
**Exception:** essential inputs unknown → list prerequisites; never claim a study is ready or complete.
**Acceptance:** Given an exposure gap, when planning follow-up, then the proposal states the question, required inputs, interpretation branches, and the remaining human decision.

### UC-04 — Review development-stage gaps
**Actor:** P-02 with specialist input. **Happy path:** state the intended stage → inspect applicable evidence and dated references → receive a gap assessment.
**Exception:** source status or applicability uncertain → flag it and request expert review.
**Acceptance:** Given draft guidance, when assessing a program, then it is labeled draft and not presented as approval or a binding rule.

### UC-05 — Record and revisit a decision
**Actor:** P-02. **Happy path:** inspect the decision packet → record a disposition and its basis → retrieve the rationale when evidence changes.
**Exception:** evidence changes or a decision is disputed → keep prior rationale and show what needs reconsideration.
**Acceptance:** Given an earlier disputed score, when revisiting the candidate, then the history is available but not presented as current evidence.

## Scope
| Module | In scope (use case) | Out of scope | Reason |
| --- | --- | --- | --- |
| Evidence | Supported claims and counterevidence (UC-01) | Definitive truth or exhaustive coverage | Access and interpretation limits |
| Candidate assessment | Readiness, uncertainty, conflicts (UC-02) | Guaranteed treatment success | Qualitative assessment cannot establish efficacy |
| Planning | Study concepts and stage gaps (UC-03, UC-04) | Lab execution, dosing, clinical work | Requires separate qualified processes |
| Traceability | Human dispositions and prior rationale (UC-05) | Autonomous approvals | Accountability stays with the owner |

## Self-check
| Type | Finding | Ref |
| --- | --- | --- |
| Coverage | Every in-scope row maps to a use case | UC-01–05 |
| Framing | “Decision support” is supported; autonomous drug discovery is not claimed | All |
| Contradiction | None open; synthetic examples and future real inputs must stay distinct | UC-02, UC-05 |
| Assumptions | Personas, users, and Tau focus need owner validation; no interviews performed | P-01, P-02 |

Engineering requirements: [requirements](requirements.md).
