# Evaluation results

First live scoring against the [evaluation plan](evaluation-plan.md), 2026-11-10. **SYNTHETIC DEMONSTRATION** records only. Release thresholds are not set yet ([TASK.md](../../TASK.md)), so results are observations, not a release verdict.

## Runs
| Run | Candidates | Models (reviewer · portfolio) | Cost | Outcome |
| --- | --- | --- | --- | --- |
| `run-20261109-190842-19f12d` | A G N | gemini-2.5-flash-lite · same | $0.0018 | Closed; owner decided A/G follow-up, N blocked |
| `run-20261109-191402-5df9a1` (scratch state) | C D F O | gemini-2.5-flash-lite · same | $0.0016 | Awaiting human (evaluation only) |
| `run-20261109-191307-640a01` (scratch state) | A G, budget $0.001 | none called | $0 | Partial, as designed |
| `run-20261109-191707-bb9e12` (scratch state) | C D F O, after contradiction check | gemini-2.5-flash-lite · same | $0.0016 | Re-run of EV-02/03 |

## Scenarios
| ID | Result | Evidence |
| --- | --- | --- |
| EV-01 | Pass (offline) | `test_unknown_candidate_creates_no_run`, `test_unknown_candidate_is_reported_not_guessed` |
| EV-02 C artifact | Pass on re-run | Blocked, failed gate kept. First run listed the efficacy claim as both supported and disputed; the deterministic check now keeps it only as disputed and notes it in the packet |
| EV-03 D safety | Pass on re-run | Blocked despite activity. First run listed “Safety rating is 0” both ways; after the prompt rule it appears only as disputed. Remaining nit: the model still restates ratings as claims |
| EV-04 F invalid | Pass | No claims, no imputed score; recommended hold with assay requalification |
| EV-05 O untested | Pass | Treated as unmeasured; “do not rank missing evidence” |
| EV-06 N conflict | Pass | Score unknown, history 72 retained, replication gate failed, blocked; live eval test passes |
| EV-07 negative trials | Not run | First slice has no literature retrieval (researcher node is second slice) |
| EV-08 full text | Not run | Same reason |
| EV-09 draft guidance | Not run | No regulatory node yet |
| EV-10 A/G | Partial | No promotion; follow-up for both. Next steps are generic gap lists, not one discriminating study |
| EV-11 hostile source | Partial (offline) | Evidence wrapped as untrusted data (`test_evidence_is_wrapped_as_untrusted_data`); no live hostile-input case yet |
| EV-12 no disposition | Pass | Packet says “Recommendation (not a decision)”; run waits for `decide`; offline gate tests |
| EV-13 budget | Pass | Run stopped before an unaffordable call and returned a partial packet. Display bug (“$0.00” for a $0.001 cap) fixed |

## Metrics (closed run and C D F O run)
Fabricated citations 0 · unauthorized promotions 0 · gate errors 0 (deterministic guard) · provenance labels present on every claim · contradictory claims 3 on the first run, 0 after the check (EV-02, EV-03) · unreported unknowns 0.

## Provider findings
- Groq retired `llama-3.1-8b-instant` (HTTP 404). Its replacement `openai/gpt-oss-20b` exceeds the free-tier limit of 8,000 tokens per minute for the reviewer prompt (~6,700 input + 1,500 output; HTTP 413).
- Mistral `mistral-small-latest` returned HTTP 429 (rate limit) on repeated tries with this key.
- Gemini 2.5 Flash-Lite completed every step. Provider errors now report HTTP status and message.

## Follow-up
1. ~~Deterministic check for claims listed as both supported and disputed~~ — done (`resolve_contradictions` in `graph/build.py`). Open nit: the model restates ratings as claims despite the prompt rule.
2. EV-10: ask the portfolio role for one discriminating A-vs-G study.
3. Add a live EV-11 case with a hostile instruction inside an evidence record fixture.
