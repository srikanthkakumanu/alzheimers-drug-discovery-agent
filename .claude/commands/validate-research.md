---
{
  "description": "Run offline NeuroQuest repository validation and its tests, then report actual results."
}
---

From the project root (the folder containing `CLAUDE.md` and `scripts/validate_repository.py`), run `python3 scripts/validate_repository.py`, then `python3 -m unittest discover -s tests -v`. Do not interpolate arguments into shell commands.

Report each exit status, then either the failing paths (concise) or the passing test count. If Python is missing or execution is blocked, say so. These checks need no credentials, network, model calls, or `.env`. Do not repair records, install packages, or change settings as part of validation, and do not describe a pass as scientific validity, source currency, or regulatory readiness.
