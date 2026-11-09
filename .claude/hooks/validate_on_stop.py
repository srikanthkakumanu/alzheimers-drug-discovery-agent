#!/usr/bin/env python3
"""Claude Code Stop hook: run the offline validator and return bounded feedback.

Contract (Claude Code hooks): read the Stop event JSON from stdin; print nothing
to allow the stop, or print {"decision": "block", "reason": ...} to ask Claude to
continue. Never reads `.env` or transcripts and never echoes the payload.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = Path('scripts/validate_repository.py')
MAX_FEEDBACK = 1600
MAX_LINES = 8
TIMEOUT_SECONDS = 15  # below the 20-second hook timeout in .claude/settings.json


def block(reason: str) -> dict[str, str]:
    return {'decision': 'block', 'reason': reason}


def evaluate(payload: dict[str, Any], root: Path = ROOT) -> dict[str, str] | None:
    """Return Claude's documented hook decision, or None to allow the stop."""
    if payload.get('hook_event_name') != 'Stop':
        raise ValueError('expected a Stop hook event')
    active = payload.get('stop_hook_active', False)
    if not isinstance(active, bool):
        raise ValueError('stop_hook_active must be boolean')
    if active:
        # Second stop after our feedback: allow it, so we never loop.
        return None
    script = root / VALIDATOR
    if not script.is_file():
        return block(f'NeuroQuest validator not found at {VALIDATOR}. Report this; do not claim checks passed.')
    try:
        result = subprocess.run([sys.executable, str(script), '--root', str(root)], cwd=root,
                                capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return block('NeuroQuest validation could not run. Report the execution problem; '
                     'do not claim checks passed. Run python3 scripts/validate_repository.py manually.')
    if result.returncode == 0:
        return None
    # Forward only validator error lines, never arbitrary output.
    failures = [line for line in result.stderr.splitlines()
                if line.startswith(('ERROR ', 'Validation failed:'))]
    detail = '\n'.join(failures[:MAX_LINES])[:MAX_FEEDBACK] or 'Repository validation returned a nonzero exit status.'
    extra = len(failures) - MAX_LINES
    if extra > 0:
        detail += f'\n…and {extra} more; run python3 scripts/validate_repository.py.'
    return block('NeuroQuest file validation failed. Resolve issues within the requested scope, '
                 'or report remaining failures without claiming success. Do not rewrite scientific '
                 'evidence merely to pass checks.\n' + detail)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError('expected a JSON object')
        output = evaluate(payload)
    except (ValueError, TypeError):
        print('NeuroQuest hook: invalid Stop event JSON; run validation manually.', file=sys.stderr)
        return 1
    if output is not None:
        print(json.dumps(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
