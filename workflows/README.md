# Workflow index

| File | Kind | Runs? |
| --- | --- | --- |
| [preclinical-promotion.yaml](preclinical-promotion.yaml) | Descriptive human review process: evidence → score → review → plan → regulatory → portfolio → human decision | No (`executable: false`) |
| `.github/workflows/research-review.yml` | CI: runs the offline validator and tests on push and pull request | Yes |

The promotion workflow takes its rules from the [scoring contract](../config/scoring-model.json): missing evidence → hold, failed gate → blocked, no human approval → hold, all conditions met → eligible for a *human-recorded* decision, never automatic. Both files use JSON-compatible YAML so the dependency-free validator can parse them.
