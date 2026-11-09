#!/usr/bin/env python3
"""Validate NeuroQuest repository contracts offline.

Standard library only; never reads `.env`, never uses the network. Checks are
schema-based so the corpus can grow: minimum record counts come from
config/settings.json (`validation.minimum_records`).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import unquote

# --- Vocabulary -------------------------------------------------------------
EXCLUDED_PARTS = frozenset({'.git', '.venv', 'venv', '__pycache__', '.cache',
                            '.validation-cache', 'node_modules', 'var'})
DIMENSIONS = frozenset({'efficacy', 'safety', 'bbb', 'manufacturing'})
GATES = frozenset({'identity', 'orthogonal_activity', 'replication',
                   'cns_exposure_engagement', 'safety', 'manufacturing'})
GATE_STATES = frozenset({'pass', 'fail', 'unknown'})
DISPOSITIONS = frozenset({'follow-up', 'hold', 'blocked', 'provisional',
                          'deprioritized', 'promoted'})
EXPERIMENT_STATES = frozenset({'completed', 'proposed', 'invalid'})
HISTORY_STATES = frozenset({'disputed', 'superseded'})
ADR_STATES = frozenset({'proposed', 'accepted', 'rejected', 'deprecated', 'superseded'})
ADR_SECTIONS = ('## Context', '## Decision', '## Alternatives',
                '## Consequences', '## Validation', '## Revisit')
REQUIRED_SKILLS = frozenset({'neuroquest-review', 'neuroquest-evidence', 'neuroquest-plan'})
REQUIRED_COMMANDS = frozenset({'research-status', 'validate-research'})
OPTIONAL_WORKFLOW_FIELDS = frozenset({'argument-hint'})
STOP_HOOK_COMMAND = 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/validate_on_stop.py"'
REQUIRED_DENY_RULES = frozenset({'Read(./.env)', 'Edit(./.env)'})
REQUIRED_IGNORES = ('.env', '!.env.example', 'CLAUDE.local.md',
                    '.claude/settings.local.json', '*.sqlite3', 'var/')
SECRET_SUFFIXES = ('_KEY', '_URL', '_TOKEN', '_SECRET', '_EMAIL')
PLACEHOLDERS = ('Role definition.', 'Summary and findings.', 'Result: Recorded.',
                'Research learnings accumulated.', 'Decision record.')
DEFAULT_BUDGETS = {'root_instruction_max_bytes': 3200, 'role_instruction_max_bytes': 2400,
                   'index_max_bytes': 6000, 'leaf_max_bytes': 8000}
DEFAULT_WEIGHTS = {'efficacy': 40, 'safety': 30, 'bbb': 20, 'manufacturing': 10}

RECORD_PATTERN = re.compile(r'\A---\n(.*?)\n---\n', re.S)
LINK_PATTERN = re.compile(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)')
FENCE_PATTERN = re.compile(r'```.*?```', re.S)


@dataclass(frozen=True)
class RecordGroup:
    folder: str
    pattern: str
    id_regex: str
    default_minimum: int
    provenance: str | None


GROUPS = (
    RecordGroup('molecules', 'candidate-*.md', r'candidate-[A-Z]+', 15, 'synthetic'),
    RecordGroup('experiments', 'EXP-*.md', r'EXP-\d{3}', 20, 'synthetic'),
    RecordGroup('literature', 'paper-*.md', r'paper-\d{3}', 20, 'published'),
    RecordGroup('memory', 'month-*.md', r'month-\d{2}', 12, 'synthetic'),
    RecordGroup('adr', 'ADR-*.md', r'ADR-\d{3}', 10, None),
)


@dataclass(frozen=True)
class Record:
    meta: dict[str, Any]
    path: Path
    text: str
    group: str


@dataclass
class Report:
    root: Path
    errors: list[str] = field(default_factory=list)

    def fail(self, where: Path | str, message: str) -> None:
        name = where.relative_to(self.root).as_posix() if isinstance(where, Path) else where
        self.errors.append(f'{name}: {message}')


# --- Pure helpers (also used by tests) --------------------------------------
def parse_record(text: str) -> dict[str, Any]:
    """Parse JSON frontmatter (a YAML subset) between leading `---` fences."""
    match = RECORD_PATTERN.match(text)
    if not match:
        raise ValueError('missing JSON-compatible YAML frontmatter')
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        raise ValueError('frontmatter must be an object')
    return value


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def weighted_score(scores: dict[str, Any], weights: dict[str, Any]) -> float | None:
    """Return the 0–100 weighted score, or None when any rating is unknown."""
    if set(scores) != DIMENSIONS or set(weights) != DIMENSIONS:
        raise ValueError('score dimensions must be efficacy, safety, bbb, manufacturing')
    for value in scores.values():
        if value is not None and (not is_number(value) or not 0 <= value <= 5):
            raise ValueError('ratings must be null or finite numbers in 0..5')
    if any(value is None for value in scores.values()):
        return None
    return round(sum(weights[key] * scores[key] / 5 for key in weights), 1)


def promotion_eligible(candidate: dict[str, Any], policy: dict[str, Any]) -> bool:
    total = candidate.get('weighted_score')
    return (is_number(total) and total >= policy['minimum_total']
            and not candidate.get('hard_blocks')
            and all(candidate.get('gates', {}).get(gate) == 'pass'
                    for gate in policy['required_gates'])
            and candidate.get('human_approval') is True)


def is_iso_date(value: object) -> bool:
    try:
        date.fromisoformat(str(value))
        return isinstance(value, str)
    except ValueError:
        return False


def unique_str_list(value: object) -> bool:
    return (isinstance(value, list) and all(isinstance(v, str) for v in value)
            and len(value) == len(set(value)))


# --- Checks -----------------------------------------------------------------
def read_json(report: Report, relative: str) -> dict[str, Any]:
    path = report.root / relative
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError('expected object')
        return value
    except (OSError, ValueError) as exc:
        report.fail(relative, f'invalid JSON-compatible configuration: {exc}')
        return {}


def check_scoring(report: Report, scoring: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    weights = scoring.get('weights', {})
    if (not isinstance(weights, dict) or set(weights) != DIMENSIONS
            or not all(is_number(v) and v > 0 for v in weights.values())
            or sum(weights.values()) != 100):
        report.fail('config/scoring-model.json', 'weights must be positive and sum to 100 across four dimensions')
        weights = dict(DEFAULT_WEIGHTS)
    policy = scoring.get('promotion', {})
    if (set(policy.get('required_gates', [])) != GATES
            or policy.get('human_approval_required') is not True
            or policy.get('all_required_gates_must_pass') is not True
            or policy.get('hard_blocks_override_score') is not True
            or not is_number(policy.get('minimum_total'))
            or not 0 <= policy['minimum_total'] <= 100):
        report.fail('config/scoring-model.json', 'promotion policy must require all six gates, score, and human approval')
        policy = {'required_gates': sorted(GATES), 'minimum_total': 70}
    return weights, policy


def check_settings(report: Report, settings: dict[str, Any]) -> None:
    where = 'config/settings.json'
    if settings.get('data_mode') != 'synthetic-demonstration':
        report.fail(where, 'repository must remain in synthetic-demonstration mode')
    execution = settings.get('execution', {})
    if not isinstance(execution.get('agent_runtime'), bool):
        report.fail(where, 'agent_runtime must be an explicit boolean')
    for key in ('automatic_promotion', 'live_integrations'):
        if execution.get(key) is not False:
            report.fail(where, f'{key} must be false: promotion is human-only and research connectors are disabled')
    if (execution.get('native_claude_settings') is not True
            or execution.get('native_settings_path') != '.claude/settings.json'):
        report.fail(where, 'native Claude customization must point to .claude/settings.json')


def check_native_claude(report: Report) -> None:
    where = '.claude/settings.json'
    native = read_json(report, where)
    if not set(native) <= {'hooks', 'permissions', '$schema'} or 'hooks' not in native:
        report.fail(where, 'only hooks and permissions are expected in project settings')
    hooks = native.get('hooks') if isinstance(native.get('hooks'), dict) else {}
    stop_groups = hooks.get('Stop', [])
    registered = [hook for group in stop_groups if isinstance(stop_groups, list) and isinstance(group, dict)
                  for hook in (group.get('hooks') if isinstance(group.get('hooks'), list) else [])
                  if isinstance(hook, dict)]
    if not any(h.get('type') == 'command' and h.get('command') == STOP_HOOK_COMMAND
               and h.get('timeout') == 20 for h in registered):
        report.fail(where, 'Stop must use the quoted local Python hook with a 20-second timeout')
    permissions = native.get('permissions', {})
    deny = permissions.get('deny', []) if isinstance(permissions, dict) else []
    if not isinstance(deny, list) or not REQUIRED_DENY_RULES <= set(deny):
        report.fail(where, 'permissions.deny must block Claude from reading or editing .env')
    if isinstance(permissions, dict) and permissions.get('defaultMode') == 'bypassPermissions':
        report.fail(where, 'project settings must not bypass permission prompts')

    for relative in ('PROJECT.md', 'docs/claude-code.md', '.claude/hooks/validate_on_stop.py'):
        if not (report.root / relative).is_file():
            report.fail(relative, 'required project customization file is missing')

    for folder, required, pattern in (('.claude/skills', REQUIRED_SKILLS, '*/SKILL.md'),
                                      ('.claude/commands', REQUIRED_COMMANDS, '*.md')):
        files = sorted((report.root / folder).glob(pattern))
        found = {p.parent.name if p.name == 'SKILL.md' else p.stem for p in files}
        if not required <= found:
            report.fail(folder, 'expected project workflow entry points are missing: '
                        + ', '.join(sorted(required - found)))
        for path in files:
            check_workflow_file(report, path)


def check_workflow_file(report: Report, path: Path) -> None:
    try:
        meta = parse_record(path.read_text())
    except (ValueError, TypeError) as exc:
        report.fail(path, f'invalid workflow frontmatter: {exc}')
        return
    is_skill = path.name == 'SKILL.md'
    required = {'name', 'description'} if is_skill else {'description'}
    if not required <= set(meta) or not set(meta) <= required | OPTIONAL_WORKFLOW_FIELDS:
        report.fail(path, 'workflow metadata must stay minimal; no model override or implicit delegation')
    if is_skill and meta.get('name') != path.parent.name:
        report.fail(path, 'skill name must match its folder')
    description = meta.get('description')
    if not isinstance(description, str) or not description.strip() or len(description) > 300:
        report.fail(path, 'workflow description must be concise and nonempty')
    if path.stat().st_size > 2400:
        report.fail(path, 'workflow entry point exceeds 2400-byte context budget')


def check_contracts(report: Report) -> None:
    mcp = read_json(report, 'config/mcp.json')
    servers = mcp.get('servers', [])
    if mcp.get('native_mcp_configuration') is not False or not isinstance(servers, list):
        report.fail('config/mcp.json', 'inventory must not be native MCP configuration')
        servers = []
    for server in servers:
        if not isinstance(server, dict) or server.get('enabled') is not False or server.get('transport') is not None:
            report.fail('config/mcp.json', 'integration entries must remain disabled without transports')
    workflow = read_json(report, 'workflows/preclinical-promotion.yaml')
    if workflow.get('executable') is not False or workflow.get('scoring_model') != 'config/scoring-model.json':
        report.fail('workflows/preclinical-promotion.yaml', 'workflow must be descriptive and reference scoring model')
    if workflow.get('decision', {}).get('source') != 'config/scoring-model.json#/promotion':
        report.fail('workflows/preclinical-promotion.yaml', 'promotion policy must reference authoritative scoring rules')
    ci = read_json(report, '.github/workflows/research-review.yml')
    if not {'push', 'pull_request'} <= set(ci.get('on', {})) or not ci.get('jobs'):
        report.fail('.github/workflows/research-review.yml', 'CI must run on pushes and pull requests with jobs')


def check_inventory(report: Report) -> int:
    where = 'docs/original-file-inventory.json'
    paths = read_json(report, where).get('paths', [])
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        report.fail(where, 'inventory must be a nonempty list of unique paths')
        return 0
    for relative in paths:
        if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
            report.fail(where, 'inventory paths must be relative and stay within repository')
            continue
        path = report.root / relative
        if not path.is_file():
            report.fail(relative, 'original skeleton file is missing')
        elif path.stat().st_size < 180:
            report.fail(path, 'original file has not received substantive content')
    return len(paths)


def markdown_files(root: Path) -> Iterable[Path]:
    return sorted(p for p in root.rglob('*.md') if not EXCLUDED_PARTS.intersection(p.relative_to(root).parts))


def check_markdown(report: Report, budgets: dict[str, Any]) -> None:
    limits = {**DEFAULT_BUDGETS, **{k: v for k, v in budgets.items() if k in DEFAULT_BUDGETS}}
    for path in markdown_files(report.root):
        text = path.read_text()
        relative = path.relative_to(report.root)
        if relative == Path('CLAUDE.md'):
            limit = limits['root_instruction_max_bytes']
        elif path.name == 'CLAUDE.md':
            limit = limits['role_instruction_max_bytes']
        elif path.name == 'README.md' and relative != Path('README.md'):
            limit = limits['index_max_bytes']
        else:
            limit = limits['leaf_max_bytes']
        size = len(text.encode())
        if size > limit:
            report.fail(path, f'context budget exceeded ({size} > {limit} bytes)')
        if any(placeholder in text for placeholder in PLACEHOLDERS):
            report.fail(path, 'unreplaced skeleton placeholder')
        if path.name == 'CLAUDE.md' and re.search(r'(?m)^\s*@\S+', text):
            report.fail(path, 'bulk @ imports are prohibited; use navigation links')
        for target in LINK_PATTERN.findall(FENCE_PATTERN.sub('', text)):
            target = target.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            resolved = (path.parent / unquote(target.split('#', 1)[0])).resolve()
            if not resolved.is_relative_to(report.root):
                report.fail(path, f'link escapes repository: {target}')
            elif not resolved.exists():
                report.fail(path, f'broken local link: {target}')


def load_records(report: Report, minimums: dict[str, Any]) -> dict[str, Record]:
    records: dict[str, Record] = {}
    for group in GROUPS:
        found = sorted((report.root / group.folder).glob(group.pattern))
        minimum = minimums.get(group.folder, group.default_minimum)
        if len(found) < minimum:
            report.fail(group.folder, f'expected at least {minimum} records, found {len(found)}')
        for path in found:
            text = path.read_text()
            try:
                meta = parse_record(text)
            except (ValueError, TypeError) as exc:
                report.fail(path, str(exc))
                continue
            key = meta.get('id')
            if key != path.stem or not isinstance(key, str) or not re.fullmatch(group.id_regex, key):
                report.fail(path, 'record ID must match filename')
                continue
            if key in records:
                report.fail(path, f'duplicate record ID {key}')
                continue
            records[key] = Record(meta, path, text, group.folder)
    return records


def check_record(report: Report, record: Record) -> None:
    meta, path, text = record.meta, record.path, record.text
    if record.group in {'molecules', 'experiments', 'memory'}:
        if meta.get('provenance') != 'synthetic' or 'SYNTHETIC DEMONSTRATION' not in text:
            report.fail(path, 'synthetic provenance and visible label are required')
    if record.group == 'literature':
        check_paper(report, record)
    elif record.group == 'experiments':
        status = meta.get('status')
        if status not in EXPERIMENT_STATES:
            report.fail(path, 'unknown experiment state')
        measured = meta.get('measured_candidate_ids', [])
        if not unique_str_list(measured) or not set(measured) <= set(meta.get('candidate_ids', [])):
            report.fail(path, 'measured_candidate_ids must be a unique subset of candidate_ids')
        if status == 'proposed' and 'No results.' not in text:
            report.fail(path, 'proposed studies must state No results.')
        if status in {'proposed', 'invalid'} and measured:
            report.fail(path, f'{status} experiments cannot supply measured candidates')
    elif record.group == 'memory':
        if meta.get('calendar_mapping', 'missing') is not None:
            report.fail(path, 'fictional periods must not imply actual calendar dates')
    elif record.group == 'adr':
        check_adr(report, record)


def check_paper(report: Report, record: Record) -> None:
    meta, path, text = record.meta, record.path, record.text
    if meta.get('provenance') != 'published' or 'PUBLISHED EVIDENCE' not in text:
        report.fail(path, 'published evidence label and provenance required')
    if not re.fullmatch(r'\d+', str(meta.get('pmid', ''))):
        report.fail(path, 'valid PMID required')
    if not re.fullmatch(r'10\.\d{4,9}/\S+', str(meta.get('doi', ''))):
        report.fail(path, 'valid DOI required')
    for token in (f'https://pubmed.ncbi.nlm.nih.gov/{meta.get("pmid")}/', f'https://doi.org/{meta.get("doi")}'):
        if token not in text:
            report.fail(path, 'metadata identifier must match its source link')
    if not is_iso_date(meta.get('verified_on')):
        report.fail(path, 'ISO verification date required')
    if meta.get('review_scope') != 'indexed metadata and abstract only':
        report.fail(path, 'declare the actual abstract-level review scope')


def check_adr(report: Report, record: Record) -> None:
    meta, path, text = record.meta, record.path, record.text
    status = meta.get('status')
    if status not in ADR_STATES:
        report.fail(path, f'ADR status must be one of {sorted(ADR_STATES)}')
    for key in ('title', 'decision_type'):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            report.fail(path, f'ADR {key} is required')
    if not is_iso_date(meta.get('recorded_on')):
        report.fail(path, 'ADR recorded_on must be an ISO date')
    if status in {'accepted', 'rejected', 'superseded', 'deprecated'} and not is_iso_date(meta.get('reviewed_on')):
        report.fail(path, f'{status} ADR needs an ISO reviewed_on date')
    missing = [section for section in ADR_SECTIONS if section not in text]
    if missing:
        report.fail(path, 'ADR missing sections: ' + ', '.join(missing))


def check_references(report: Report, records: dict[str, Record]) -> None:
    targets = {'experiment_ids': 'experiments', 'candidate_ids': 'molecules', 'literature_ids': 'literature'}
    reciprocal = {'experiment_ids': 'candidate_ids', 'candidate_ids': 'experiment_ids'}
    pmids: dict[str, str] = {}
    for key, record in records.items():
        if record.group == 'literature':
            pmid = str(record.meta.get('pmid'))
            if pmid in pmids:
                report.fail('literature', f'publications must have unique PMIDs ({key}, {pmids[pmid]})')
            pmids[pmid] = key
        for fieldname, folder in targets.items():
            refs = record.meta.get(fieldname, [])
            if not unique_str_list(refs):
                report.fail(record.path, f'{fieldname} must be a unique list')
                continue
            for ref in refs:
                other = records.get(ref)
                if other is None or other.group != folder:
                    report.fail(record.path, f'unknown {fieldname} reference {ref}')
                elif fieldname in reciprocal and key not in other.meta.get(reciprocal[fieldname], []):
                    report.fail(record.path, f'non-reciprocal reference to {ref}')


def check_candidate(report: Report, record: Record, records: dict[str, Record],
                    weights: dict[str, Any], policy: dict[str, Any], demonstration: bool) -> None:
    meta, path = record.meta, record.path
    scores = meta.get('scores', {})
    try:
        calculated = weighted_score(scores, weights)
        if meta.get('weighted_score') != calculated:
            report.fail(path, f'weighted score mismatch: expected {calculated}')
    except (ValueError, TypeError) as exc:
        report.fail(path, str(exc))
        calculated, scores = None, {}
    gates = meta.get('gates', {})
    if not isinstance(gates, dict) or set(gates) != GATES or not set(gates.values()) <= GATE_STATES:
        report.fail(path, 'all six promotion gates need pass/fail/unknown states')
        gates = {}
    disposition = meta.get('disposition')
    if disposition not in DISPOSITIONS:
        report.fail(path, 'unknown candidate disposition')
    if (meta.get('hard_blocks') or 'fail' in gates.values()) and disposition != 'blocked':
        report.fail(path, 'hard block or failed gate requires blocked disposition')
    if not isinstance(meta.get('human_approval'), bool):
        report.fail(path, 'human approval must be explicit boolean')
    if disposition == 'promoted' and not promotion_eligible(meta, policy):
        report.fail(path, 'promotion denied: score, evidence gates, or human approval missing')
    if calculated is None and meta.get('score_status') != 'provisional':
        report.fail(path, 'missing ratings must leave score provisional')
    if demonstration and (meta.get('human_approval') is not False or disposition == 'promoted'):
        report.fail(path, 'baseline demonstration must have no approved/promoted candidates')
    check_rating_evidence(report, record, records, scores)
    check_score_history(report, record, records, weights)


def check_rating_evidence(report: Report, record: Record, records: dict[str, Record],
                          scores: dict[str, Any]) -> None:
    meta, path, key = record.meta, record.path, record.meta['id']
    evidence = meta.get('rating_evidence')
    if not isinstance(evidence, dict) or set(evidence) != DIMENSIONS:
        report.fail(path, 'rating_evidence must list experiment IDs for all four dimensions')
        return
    linked = set(meta.get('experiment_ids', []))
    for dimension, refs in evidence.items():
        if not unique_str_list(refs) or not set(refs) <= linked:
            report.fail(path, f'rating_evidence.{dimension} must reference linked experiments')
            continue
        if scores.get(dimension) is None:
            continue
        if not refs:
            report.fail(path, f'non-null {dimension} rating needs rating evidence')
        for ref in refs:
            experiment = records.get(ref)
            if experiment is None:
                continue
            if (experiment.meta.get('status') != 'completed'
                    or key not in experiment.meta.get('measured_candidate_ids', [])):
                report.fail(path, f'{dimension} rating cites {ref}, which did not measure this candidate')


def check_score_history(report: Report, record: Record, records: dict[str, Record],
                        weights: dict[str, Any]) -> None:
    history = record.meta.get('score_history', [])
    if not isinstance(history, list):
        report.fail(record.path, 'score_history must be a list')
        return
    for entry in history:
        if not isinstance(entry, dict):
            report.fail(record.path, 'score_history entries must be objects')
            continue
        try:
            expected = weighted_score(entry.get('scores', {}), weights)
        except (ValueError, TypeError) as exc:
            report.fail(record.path, f'score_history: {exc}')
            continue
        if entry.get('weighted_score') != expected:
            report.fail(record.path, f'score_history weighted score mismatch: expected {expected}')
        if entry.get('status') not in HISTORY_STATES:
            report.fail(record.path, f'score_history status must be one of {sorted(HISTORY_STATES)}')
        refs = list(entry.get('basis', [])) + [entry.get('challenged_by')]
        if any(not isinstance(ref, str) or ref not in records or records[ref].group != 'experiments' for ref in refs):
            report.fail(record.path, 'score_history basis and challenged_by must reference experiments')


def check_environment(report: Report) -> None:
    example = report.root / '.env.example'
    if not example.exists():
        report.fail('.env.example', 'environment template is required')
    else:
        for line in example.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                if key.strip().endswith(SECRET_SUFFIXES) and value.strip():
                    report.fail('.env.example', f'{key.strip()} must be blank')
    # Never read .env: it can contain secrets and is absent from a clean checkout.
    gitignore = report.root / '.gitignore'
    lines = set(gitignore.read_text().splitlines()) if gitignore.exists() else set()
    for pattern in REQUIRED_IGNORES:
        if pattern not in lines:
            report.fail('.gitignore', f'must contain {pattern!r}')


def validate(root: Path) -> list[str]:
    """Return a list of `path: message` errors; empty means the repository is consistent."""
    report = Report(root.resolve())
    settings = read_json(report, 'config/settings.json')
    weights, policy = check_scoring(report, read_json(report, 'config/scoring-model.json'))
    check_settings(report, settings)
    check_native_claude(report)
    check_contracts(report)
    check_inventory(report)
    check_markdown(report, settings.get('context', {}))
    minimums = settings.get('validation', {}).get('minimum_records', {})
    records = load_records(report, minimums if isinstance(minimums, dict) else {})
    for record in records.values():
        check_record(report, record)
    check_references(report, records)
    demonstration = settings.get('data_mode') == 'synthetic-demonstration'
    for record in records.values():
        if record.group == 'molecules':
            check_candidate(report, record, records, weights, policy, demonstration)
    check_environment(report)
    return report.errors


def summary(root: Path) -> str:
    counts = {g.folder: len(list((root / g.folder).glob(g.pattern))) for g in GROUPS}
    return (f"PASS: {counts['molecules']} candidates, {counts['experiments']} experiments, "
            f"{counts['literature']} publications, {counts['memory']} history periods, "
            f"{counts['adr']} ADRs; links, scores, gates, rating evidence, context budgets; "
            'Claude settings, hook, skills, and commands.')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        errors = validate(args.root)
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(f'Validation failed: malformed repository structure: {exc}', file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f'ERROR {error}', file=sys.stderr)
        return 1
    print(summary(args.root.resolve()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
