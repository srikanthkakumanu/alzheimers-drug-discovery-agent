"""Meaningful failure scenarios for evidence and context validation."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator', ROOT / 'scripts/validate_repository.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix='neuroquest-validation-')
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name) / 'repo'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            '.env', '.git', '.venv', '__pycache__', '.cache', '.validation-cache'))

    def update_record(self, relative, change):
        path = self.root / relative
        text = path.read_text()
        match = validator.RECORD_PATTERN.match(text)
        meta = validator.parse_record(text)
        change(meta)
        path.write_text('---\n' + json.dumps(meta, indent=2) + '\n---\n' + text[match.end():])

    def assert_error(self, fragment):
        errors = validator.validate(self.root)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_validate_clean_checkout_without_env_passes(self):
        self.assertFalse((self.root / '.env').exists())
        self.assertEqual([], validator.validate(self.root))

    def test_validate_missing_original_file_reports_path(self):
        (self.root / 'GOALS.md').unlink()
        self.assert_error('GOALS.md: original skeleton file is missing')

    def test_validate_absolute_inventory_path_rejects_nonportable_manifest(self):
        path = self.root / 'docs/original-file-inventory.json'
        meta = json.loads(path.read_text())
        meta['paths'][0] = str(ROOT / 'GOALS.md')
        path.write_text(json.dumps(meta))
        self.assert_error('inventory paths must be relative and stay within repository')

    def test_validate_broken_evidence_link_reports_target(self):
        with (self.root / 'TASK.md').open('a') as handle:
            handle.write('\n[Evidence](experiments/EXP-999.md)\n')
        self.assert_error('broken local link: experiments/EXP-999.md')

    def test_validate_fabricated_reference_rejects_unknown_id(self):
        self.update_record('molecules/candidate-A.md',
                           lambda m: m['experiment_ids'].append('EXP-999'))
        self.assert_error('unknown experiment_ids reference EXP-999')

    def test_validate_nonreciprocal_candidate_experiment_reference_fails(self):
        self.update_record('experiments/EXP-014.md',
                           lambda m: m['candidate_ids'].remove('candidate-A'))
        self.assert_error('non-reciprocal reference to EXP-014')

    def test_validate_missing_synthetic_label_rejects_record(self):
        path = self.root / 'molecules/candidate-A.md'
        path.write_text(path.read_text().replace('SYNTHETIC DEMONSTRATION', 'Portfolio data'))
        self.assert_error('synthetic provenance and visible label are required')

    def test_validate_incorrect_score_rejects_arithmetic(self):
        self.update_record('molecules/candidate-A.md', lambda m: m.update(weighted_score=99))
        self.assert_error('weighted score mismatch: expected 72.0')

    def test_validate_missing_rating_cannot_receive_imputed_total(self):
        self.update_record('molecules/candidate-O.md', lambda m: m.update(weighted_score=50))
        self.assert_error('weighted score mismatch: expected None')

    def test_validate_rating_outside_scale_fails(self):
        self.update_record('molecules/candidate-A.md', lambda m: m['scores'].update(efficacy=6))
        self.assert_error('ratings must be null or finite numbers in 0..5')

    def test_validate_replication_failure_blocks_high_score(self):
        self.update_record('molecules/candidate-N.md', lambda m: m.update(disposition='follow-up'))
        self.assert_error('hard block or failed gate requires blocked disposition')

    def test_validate_unapproved_candidate_cannot_be_promoted(self):
        self.update_record('molecules/candidate-A.md', lambda m: m.update(disposition='promoted'))
        self.assert_error('promotion denied: score, evidence gates, or human approval missing')

    def test_validate_proposed_experiment_cannot_claim_results(self):
        path = self.root / 'experiments/EXP-016.md'
        path.write_text(path.read_text().replace('No results.', 'Successful study.'))
        self.assert_error('proposed studies must state No results.')

    def test_validate_duplicate_publication_rejects_reused_pmid(self):
        self.update_record('literature/paper-002.md', lambda m: m.update(pmid='1759558'))
        self.assert_error('publications must have unique PMIDs')

    def test_validate_calendar_history_cannot_be_presented_as_real(self):
        self.update_record('memory/month-01.md', lambda m: m.update(calendar_mapping='2026-01'))
        self.assert_error('fictional periods must not imply actual calendar dates')

    def test_validate_malformed_workflow_reports_parse_error(self):
        (self.root / 'workflows/preclinical-promotion.yaml').write_text('{ invalid')
        self.assert_error('invalid JSON-compatible configuration')

    def test_validate_root_budget_reports_excessive_context(self):
        with (self.root / 'CLAUDE.md').open('a') as handle:
            handle.write('Extra context. ' * 300)
        self.assert_error('context budget exceeded')

    def test_validate_template_must_not_include_credentials(self):
        path = self.root / '.env.example'
        path.write_text(path.read_text().replace('ANTHROPIC_API_KEY=', 'ANTHROPIC_API_KEY=example-secret'))
        self.assert_error('ANTHROPIC_API_KEY must be blank')

    def test_validate_enabled_integration_requires_separate_scope(self):
        path = self.root / 'config/mcp.json'
        meta = json.loads(path.read_text())
        meta['servers'][0]['enabled'] = True
        path.write_text(json.dumps(meta))
        self.assert_error('integration entries must remain disabled')


class PromotionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'config/scoring-model.json').read_text())['promotion']
        self.candidate = {'weighted_score': 80, 'hard_blocks': [], 'human_approval': True,
                          'gates': {key: 'pass' for key in self.policy['required_gates']}}

    def test_eligibility_complete_evidence_and_human_approval_is_true(self):
        self.assertTrue(validator.promotion_eligible(self.candidate, self.policy))

    def test_eligibility_each_missing_or_failed_gate_is_false(self):
        for gate in self.policy['required_gates']:
            for state in ('unknown', 'fail'):
                with self.subTest(gate=gate, state=state):
                    candidate = copy.deepcopy(self.candidate)
                    candidate['gates'][gate] = state
                    self.assertFalse(validator.promotion_eligible(candidate, self.policy))

    def test_eligibility_human_approval_missing_is_false(self):
        self.candidate['human_approval'] = False
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))

    def test_eligibility_high_score_with_block_is_false(self):
        self.candidate.update(weighted_score=100, hard_blocks=['replication_failure'])
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))

    def test_eligibility_unknown_total_is_false(self):
        self.candidate['weighted_score'] = None
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))

    def test_eligibility_below_threshold_is_false(self):
        self.candidate['weighted_score'] = self.policy['minimum_total'] - 0.1
        self.assertFalse(validator.promotion_eligible(self.candidate, self.policy))


if __name__ == '__main__':
    unittest.main()
