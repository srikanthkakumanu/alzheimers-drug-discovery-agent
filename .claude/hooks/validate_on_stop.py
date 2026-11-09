#!/usr/bin/env python3
"""Claude Stop hook: offline validation, bounded feedback, and a continuation guard."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MAX_FEEDBACK = 1600


def evaluate(payload: dict, root: Path = ROOT) -> dict | None:
    """Return Claude's documented JSON decision; never read transcripts or .env."""
    if payload.get('hook_event_name') != 'Stop':
        raise ValueError('expected a Stop hook event')
    if not isinstance(payload.get('stop_hook_active', False), bool):
        raise ValueError('stop_hook_active must be boolean')
    # The second Stop must not trigger an endless repair/continuation loop.
    if payload.get('stop_hook_active') is True:
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(root / 'scripts/validate_repository.py'), '--root', str(root)],
            cwd=root, capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {'decision': 'block', 'reason':
                'NeuroQuest validation could not run. Report the execution problem; '
                'do not claim checks passed. Run python3 scripts/validate_repository.py manually.'}
    if result.returncode == 0:
        return None
    # Do not forward arbitrary program output or stdin/transcript content to the model.
    failures = [line for line in result.stderr.splitlines()
                if line.startswith(('ERROR ', 'Validation failed:'))]
    detail = '\n'.join(failures[:8])[:MAX_FEEDBACK] or 'Repository validation returned a nonzero exit status.'
    return {'decision': 'block', 'reason':
            'NeuroQuest file validation failed. Resolve issues within the requested scope, '
            'or report remaining failures without claiming success. Do not rewrite scientific '
            'evidence merely to pass checks.\n' + detail}


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
