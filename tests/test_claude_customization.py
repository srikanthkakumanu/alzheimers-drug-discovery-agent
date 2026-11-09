"""Verify native customization contracts and real offline hook behavior."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = module_from(ROOT / '.claude/hooks/validate_on_stop.py', 'stop_hook')
validator = module_from(ROOT / 'scripts/validate_repository.py', 'native_validator')


class ClaudeCustomizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='neuroquest-hook-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project with spaces'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            '.env', '.git', '.venv', '__pycache__', '.cache', '.validation-cache'))

    def errors(self):
        return validator.validate(self.root)

    def test_hook_valid_checkout_is_silent_from_nested_directory(self):
        result = subprocess.run(
            [sys.executable, str(self.root / '.claude/hooks/validate_on_stop.py')],
            cwd=self.root / 'molecules', input=json.dumps({'hook_event_name': 'Stop', 'stop_hook_active': False}),
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stdout)
        self.assertEqual('', result.stderr)

    def test_hook_invalid_repository_returns_documented_block_decision(self):
        (self.root / 'GOALS.md').unlink()
        result = hook.evaluate({'hook_event_name': 'Stop'}, self.root)
        self.assertEqual('block', result['decision'])
        self.assertIn('GOALS.md', result['reason'])
        self.assertNotIn('hookSpecificOutput', result)

    def test_hook_repeated_continuation_skips_validation(self):
        with patch.object(hook.subprocess, 'run') as run:
            self.assertIsNone(hook.evaluate({'hook_event_name': 'Stop', 'stop_hook_active': True}, self.root))
        run.assert_not_called()

    def test_hook_validation_timeout_returns_bounded_feedback(self):
        with patch.object(hook.subprocess, 'run', side_effect=subprocess.TimeoutExpired('validator', 15)):
            output = hook.evaluate({'hook_event_name': 'Stop'}, self.root)
        self.assertEqual('block', output['decision'])
        self.assertIn('could not run', output['reason'])

    def test_hook_malformed_input_does_not_echo_payload(self):
        marker = 'private-transcript-marker'
        result = subprocess.run(
            [sys.executable, str(self.root / '.claude/hooks/validate_on_stop.py')],
            input='invalid ' + marker, text=True, capture_output=True, check=False,
        )
        self.assertEqual(1, result.returncode)
        self.assertNotIn(marker, result.stdout + result.stderr)

    def test_hook_wrong_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Stop hook event'):
            hook.evaluate({'hook_event_name': 'SessionStart'}, self.root)

    def test_hook_output_limits_failure_feedback(self):
        failure = subprocess.CompletedProcess([], 1, '', 'ERROR ' + 'x' * 10000)
        with patch.object(hook.subprocess, 'run', return_value=failure):
            output = hook.evaluate({'hook_event_name': 'Stop'}, self.root)
        self.assertLess(len(output['reason']), 2000)

    def test_hook_missing_python_runner_reports_execution_problem(self):
        with patch.object(hook.subprocess, 'run', side_effect=OSError('runner unavailable')):
            output = hook.evaluate({'hook_event_name': 'Stop'}, self.root)
        self.assertEqual('block', output['decision'])
        self.assertIn('could not run', output['reason'])

    def test_validator_detects_missing_project_overview(self):
        (self.root / 'PROJECT.md').unlink()
        self.assertTrue(any('PROJECT.md: required project customization file is missing' in error
                            for error in self.errors()))

    def test_validator_detects_misregistered_hook_command(self):
        path = self.root / '.claude/settings.json'
        settings = json.loads(path.read_text())
        settings['hooks']['Stop'][0]['hooks'][0]['command'] = 'unrelated-command'
        path.write_text(json.dumps(settings))
        self.assertTrue(any('Stop must use the quoted local Python hook' in error for error in self.errors()))

    def test_validator_detects_missing_skill(self):
        (self.root / '.claude/skills/neuroquest-review/SKILL.md').unlink()
        self.assertTrue(any('.claude/skills: expected project workflow entry points' in error
                            for error in self.errors()))

    def test_validator_malformed_hook_structure_reports_error_without_crashing(self):
        path = self.root / '.claude/settings.json'
        for config in ({'hooks': None}, {'hooks': {'Stop': [None]}},
                       {'hooks': {'Stop': [{'hooks': [None]}]}}):
            with self.subTest(config=config):
                path.write_text(json.dumps(config))
                self.assertTrue(any('.claude/settings.json:' in error for error in self.errors()))

    def test_validator_detects_mismatched_skill_discovery_name(self):
        path = self.root / '.claude/skills/neuroquest-review/SKILL.md'
        text = path.read_text().replace('"name": "neuroquest-review"', '"name": "wrong-name"')
        path.write_text(text)
        self.assertTrue(any('skill name must match its folder' in error for error in self.errors()))

    def test_validator_detects_unexpected_model_override(self):
        path = self.root / '.claude/skills/neuroquest-plan/SKILL.md'
        text = path.read_text()
        match = validator.RECORD_PATTERN.match(text)
        metadata = validator.parse_record(text)
        metadata['model'] = 'unrequested-model'
        path.write_text('---\n' + json.dumps(metadata) + '\n---\n' + text[match.end():])
        self.assertTrue(any('no model override or implicit delegation' in error for error in self.errors()))


if __name__ == '__main__':
    unittest.main()
