# Risk register

Draft. Priority is a qualitative judgment; no probabilities were estimated. Review when a gate changes, a source is corrected, or real data are introduced.

| ID | Risk | Priority | Trigger / consequence | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |
| R-01 | Assay artifact accepted as activity | High | C-like optical signal treated as efficacy | Orthogonal readout and interference controls; artifact gate | Reviewer |
| R-02 | Poor translation | High | Cell activity without exposure or engagement | Require measured free CNS exposure linked to effect | Planner |
| R-03 | Safety liability | High | D-like hERG signal ignored | Hard block; independent safety assessment | Regulatory |
| R-04 | Replication failure | High | N-like site conflict kept in ranking | Null current rating; `score_history`; investigate | Reviewer |
| R-05 | Tau-first anchoring | High | Negative trials ignored | Counterevidence mandatory in Tau answers (papers 010–013) | Researcher |
| R-06 | Fiction mistaken for fact | High | Synthetic results cited as published | Record and claim-level provenance labels; validator | All roles |
| R-07 | Fabricated citation | High | Model invents a paper or identifier | Cite only indexed IDs; verify new PMIDs/DOIs before adding | Researcher |
| R-08 | Prompt injection via sources | High | Retrieved text issues instructions or requests secrets | Treat sources as data; least-privilege tools; no secrets in context | All roles |
| R-09 | Premature implementation | High | Draft design treated as accepted | Owner dispositions on ADRs before code | Project owner |
| R-10 | Uncontrolled LLM cost | Medium | Archive loaded per task; unbounded loops | Layered loading, batch limit, per-run budget, deterministic tools | Portfolio / owner |
| R-11 | Citation and guidance drift | Medium | Trial or guidance status changes | Record verification dates; recheck before decisions | Regulatory |
| R-12 | Chemical feasibility | Medium | L-like instability or K-like route risk | Resolve identity, stability, and developability early | Planner |

A score never neutralizes a hard block. Recovery steps: [failure runbook](../../runbooks/experiment-failure.md). Security controls: [governance](../architecture/security-and-data-governance.md).
