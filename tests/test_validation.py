"""Failure scenarios for the offline repository validator."""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator', ROOT / 'scripts/validate_repository.py')
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

IGNORED = shutil.ignore_patterns('.env', '.git', '.venv', '__pycache__', '.cache', '.validation-cache', 'var')


class RepositoryTestCase(unittest.TestCase):
    """Copies the repository into a temp dir so each test can break one thing."""

    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory(prefix='neuroquest-validation-')
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name) / 'repo'
        shutil.copytree(ROOT, self.root, ignore=IGNORED)

    def update_record(self, relative: str, change: Callable[[dict[str, Any]], None]) -> None:
        path = self.root / relative
        text = path.read_text()
        match = validator.RECORD_PATTERN.match(text)
        meta = validator.parse_record(text)
        change(meta)
        path.write_text('---\n' + json.dumps(meta, indent=2) + '\n---\n' + text[match.end():])

    def update_json(self, relative: str, change: Callable[[dict[str, Any]], None]) -> None:
        path = self.root / relative
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def assert_error(self, fragment: str) -> None:
        errors = validator.validate(self.root)
        self.assertTrue(any(fragment in error for error in errors), errors)


class StructureTests(RepositoryTestCase):
    def test_clean_checkout_without_env_passes(self) -> None:
        self.assertFalse((self.root / '.env').exists())
        self.assertEqual([], validator.validate(self.root))

    def test_missing_original_file_reports_path(self) -> None:
        (self.root / 'GOALS.md').unlink()
        self.assert_error('GOALS.md: original skeleton file is missing')

    def test_absolute_inventory_path_is_rejected(self) -> None:
        self.update_json('docs/original-file-inventory.json',
                         lambda d: d['paths'].__setitem__(0, str(ROOT / 'GOALS.md')))
        self.assert_error('inventory paths must be relative and stay within repository')

    def test_broken_link_reports_target(self) -> None:
        with (self.root / 'TASK.md').open('a') as handle:
            handle.write('\n[Evidence](experiments/EXP-999.md)\n')
        self.assert_error('broken local link: experiments/EXP-999.md')

    def test_link_inside_code_fence_is_ignored(self) -> None:
        with (self.root / 'TASK.md').open('a') as handle:
            handle.write('\n```text\n[example](not/a/file.md)\n```\n')
        self.assertEqual([], validator.validate(self.root))

    def test_root_budget_reports_excessive_context(self) -> None:
        with (self.root / 'CLAUDE.md').open('a') as handle:
            handle.write('Extra context. ' * 300)
        self.assert_error('context budget exceeded')

    def test_record_count_below_minimum_fails(self) -> None:
        (self.root / 'memory/month-12.md').unlink()
        self.assert_error('memory: expected at least 12 records, found 11')

    def test_malformed_workflow_reports_parse_error(self) -> None:
        (self.root / 'workflows/preclinical-promotion.yaml').write_text('{ invalid')
        self.assert_error('invalid JSON-compatible configuration')


class EvidenceTests(RepositoryTestCase):
    def test_fabricated_reference_rejects_unknown_id(self) -> None:
        self.update_record('molecules/candidate-A.md', lambda m: m['experiment_ids'].append('EXP-999'))
        self.assert_error('unknown experiment_ids reference EXP-999')

    def test_nonreciprocal_candidate_experiment_reference_fails(self) -> None:
        self.update_record('experiments/EXP-014.md', lambda m: m['candidate_ids'].remove('candidate-A'))
        self.assert_error('non-reciprocal reference to EXP-014')

    def test_missing_synthetic_label_rejects_record(self) -> None:
        path = self.root / 'molecules/candidate-A.md'
        path.write_text(path.read_text().replace('SYNTHETIC DEMONSTRATION', 'Portfolio data'))
        self.assert_error('synthetic provenance and visible label are required')

    def test_proposed_experiment_cannot_claim_results(self) -> None:
        path = self.root / 'experiments/EXP-016.md'
        path.write_text(path.read_text().replace('No results.', 'Successful study.'))
        self.assert_error('proposed studies must state No results.')

    def test_proposed_experiment_cannot_list_measured_candidates(self) -> None:
        self.update_record('experiments/EXP-016.md', lambda m: m.update(measured_candidate_ids=['candidate-A']))
        self.assert_error('proposed experiments cannot supply measured candidates')

    def test_duplicate_publication_rejects_reused_pmid(self) -> None:
        self.update_record('literature/paper-002.md', lambda m: m.update(pmid='1759558'))
        self.assert_error('publications must have unique PMIDs')

    def test_calendar_history_cannot_be_presented_as_real(self) -> None:
        self.update_record('memory/month-01.md', lambda m: m.update(calendar_mapping='2026-01'))
        self.assert_error('fictional periods must not imply actual calendar dates')


class ScoringTests(RepositoryTestCase):
    def test_incorrect_score_rejects_arithmetic(self) -> None:
        self.update_record('molecules/candidate-A.md', lambda m: m.update(weighted_score=99))
        self.assert_error('weighted score mismatch: expected 72.0')

    def test_missing_rating_cannot_receive_imputed_total(self) -> None:
        self.update_record('molecules/candidate-O.md', lambda m: m.update(weighted_score=50))
        self.assert_error('weighted score mismatch: expected None')

    def test_rating_outside_scale_fails(self) -> None:
        self.update_record('molecules/candidate-A.md', lambda m: m['scores'].update(efficacy=6))
        self.assert_error('ratings must be null or finite numbers in 0..5')

    def test_replication_failure_blocks_high_score(self) -> None:
        self.update_record('molecules/candidate-N.md', lambda m: m.update(disposition='follow-up'))
        self.assert_error('hard block or failed gate requires blocked disposition')

    def test_unapproved_candidate_cannot_be_promoted(self) -> None:
        self.update_record('molecules/candidate-A.md', lambda m: m.update(disposition='promoted'))
        self.assert_error('promotion denied: score, evidence gates, or human approval missing')

    def test_rating_cannot_cite_experiment_that_did_not_measure_candidate(self) -> None:
        # O is linked to EXP-003 but was never measured there.
        self.update_record('molecules/candidate-O.md', lambda m: (
            m['scores'].update(efficacy=2), m['rating_evidence'].update(efficacy=['EXP-003'])))
        self.assert_error('efficacy rating cites EXP-003, which did not measure this candidate')

    def test_non_null_rating_requires_evidence(self) -> None:
        self.update_record('molecules/candidate-A.md', lambda m: m['rating_evidence'].update(bbb=[]))
        self.assert_error('non-null bbb rating needs rating evidence')

    def test_score_history_arithmetic_is_checked(self) -> None:
        self.update_record('molecules/candidate-N.md', lambda m: m['score_history'][0].update(weighted_score=90))
        self.assert_error('score_history weighted score mismatch')


class DecisionRecordTests(RepositoryTestCase):
    def test_unknown_adr_status_fails(self) -> None:
        self.update_record('adr/ADR-001.md', lambda m: m.update(status='approved'))
        self.assert_error('ADR status must be one of')

    def test_accepted_adr_requires_review_date(self) -> None:
        self.update_record('adr/ADR-001.md', lambda m: m.update(status='accepted'))
        self.assert_error('accepted ADR needs an ISO reviewed_on date')

    def test_adr_requires_standard_sections(self) -> None:
        path = self.root / 'adr/ADR-002.md'
        path.write_text(path.read_text().replace('## Alternatives', '## Options'))
        self.assert_error('ADR missing sections: ## Alternatives')


class SecretAndSettingsTests(RepositoryTestCase):
    def test_template_must_not_include_credentials(self) -> None:
        path = self.root / '.env.example'
        path.write_text(path.read_text().replace('OPENAI_API_KEY=', 'OPENAI_API_KEY=example-secret'))
        self.assert_error('OPENAI_API_KEY must be blank')

    def test_gitignore_must_exclude_runtime_state(self) -> None:
        path = self.root / '.gitignore'
        path.write_text(path.read_text().replace('var/\n', ''))
        self.assert_error(".gitignore: must contain 'var/'")

    def test_env_deny_rule_is_required(self) -> None:
        self.update_json('.claude/settings.json', lambda s: s['permissions'].update(deny=[]))
        self.assert_error('permissions.deny must block Claude from reading or editing .env')

    def test_enabled_integration_is_rejected(self) -> None:
        self.update_json('config/mcp.json', lambda d: d['servers'][0].update(enabled=True))
        self.assert_error('integration entries must remain disabled')


class PromotionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads((ROOT / 'config/scoring-model.json').read_text())['promotion']
        self.candidate = {'weighted_score': 80, 'hard_blocks': [], 'human_approval': True,
                          'gates': {key: 'pass' for key in self.policy['required_gates']}}

    def test_complete_evidence_and_human_approval_is_eligible(self) -> None:
        self.assertTrue(validator.promotion_eligible(self.candidate, self.policy))

    def test_each_missing_or_failed_gate_is_ineligible(self) -> None:
        for gate in self.policy['required_gates']:
            for state in ('unknown', 'fail'):
                with self.subTest(gate=gate, state=state):
                    candidate = copy.deepcopy(self.candidate)
                    candidate['gates'][gate] = state
                    self.assertFalse(validator.promotion_eligible(candidate, self.policy))

    def test_missing_human_approval_is_ineligible(self) -> None:
        self.candidate['human_approval'] = False
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))

    def test_high_score_with_block_is_ineligible(self) -> None:
        self.candidate.update(weighted_score=100, hard_blocks=['replication_failure'])
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))

    def test_unknown_total_is_ineligible(self) -> None:
        self.candidate['weighted_score'] = None
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))

    def test_below_threshold_is_ineligible(self) -> None:
        self.candidate['weighted_score'] = self.policy['minimum_total'] - 0.1
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))


if __name__ == '__main__':
    unittest.main()
