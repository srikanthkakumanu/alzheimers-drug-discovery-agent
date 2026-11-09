#!/usr/bin/env python3
"""Validate NeuroQuest's document contracts offline; no external packages or secrets."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote

EXCLUDED = {'.git', '.venv', '__pycache__', '.cache', '.validation-cache'}
DIMENSIONS = {'efficacy', 'safety', 'bbb', 'manufacturing'}
GATES = {'identity', 'orthogonal_activity', 'replication',
         'cns_exposure_engagement', 'safety', 'manufacturing'}
GROUPS = {'molecules': ('candidate-*.md', 15), 'experiments': ('EXP-*.md', 20),
          'literature': ('paper-*.md', 20), 'memory': ('month-*.md', 12),
          'adr': ('ADR-*.md', 10)}
RECORD_PATTERN = re.compile(r'\A---\n(.*?)\n---\n', re.S)
LINK_PATTERN = re.compile(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)')
PLACEHOLDERS = ('Role definition.', 'Summary and findings.', 'Result: Recorded.',
                'Research learnings accumulated.', 'Decision record.')


def parse_record(text: str) -> dict:
    """Frontmatter deliberately uses the JSON-compatible YAML subset."""
    match = RECORD_PATTERN.match(text)
    if not match:
        raise ValueError('missing JSON-compatible YAML frontmatter')
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        raise ValueError('frontmatter must be an object')
    return value


def weighted_score(scores: dict, weights: dict) -> float | None:
    if set(scores) != DIMENSIONS or set(weights) != DIMENSIONS:
        raise ValueError('score dimensions must be efficacy, safety, bbb, manufacturing')
    for value in scores.values():
        if value is not None and (isinstance(value, bool)
                                  or not isinstance(value, (int, float))
                                  or not math.isfinite(value) or not 0 <= value <= 5):
            raise ValueError('ratings must be null or finite numbers in 0..5')
    if any(value is None for value in scores.values()):
        return None
    return round(sum(weights[key] * scores[key] / 5 for key in weights), 1)


def promotion_eligible(candidate: dict, policy: dict) -> bool:
    total = candidate.get('weighted_score')
    return (isinstance(total, (int, float)) and not isinstance(total, bool)
            and total >= policy['minimum_total']
            and not candidate.get('hard_blocks')
            and all(candidate.get('gates', {}).get(gate) == 'pass'
                    for gate in policy['required_gates'])
            and candidate.get('human_approval') is True)


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    def fail(path: Path | str, message: str) -> None:
        name = str(path.relative_to(root)) if isinstance(path, Path) else path
        errors.append(f'{name}: {message}')

    def read_json(relative: str) -> dict:
        path = root / relative
        try:
            value = json.loads(path.read_text())
            if not isinstance(value, dict):
                raise ValueError('expected object')
            return value
        except (OSError, ValueError) as exc:
            fail(path, f'invalid JSON-compatible configuration: {exc}')
            return {}

    settings = read_json('config/settings.json')
    scoring = read_json('config/scoring-model.json')
    mcp = read_json('config/mcp.json')
    workflow = read_json('workflows/preclinical-promotion.yaml')
    ci = read_json('.github/workflows/research-review.yml')
    inventory = read_json('docs/original-file-inventory.json')
    weights = scoring.get('weights', {})
    valid_weights = (set(weights) == DIMENSIONS
                     and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                             and math.isfinite(v) and v > 0 for v in weights.values()))
    if not valid_weights or sum(weights.values()) != 100:
        fail('config/scoring-model.json', 'weights must be positive and sum to 100 across four dimensions')
        weights = {'efficacy': 40, 'safety': 30, 'bbb': 20, 'manufacturing': 10}
    policy = scoring.get('promotion', {})
    if (set(policy.get('required_gates', [])) != GATES
            or policy.get('human_approval_required') is not True
            or policy.get('all_required_gates_must_pass') is not True
            or policy.get('hard_blocks_override_score') is not True
            or not isinstance(policy.get('minimum_total'), (int, float))
            or isinstance(policy.get('minimum_total'), bool)
            or not 0 <= policy.get('minimum_total', -1) <= 100):
        fail('config/scoring-model.json', 'promotion policy must require all six gates, score, and human approval')
        policy = {'required_gates': sorted(GATES), 'minimum_total': 70}
    if settings.get('data_mode') != 'synthetic-demonstration':
        fail('config/settings.json', 'repository must remain in synthetic-demonstration mode')
    for key in ('agent_runtime', 'automatic_promotion', 'live_integrations'):
        if settings.get('execution', {}).get(key) is not False:
            fail('config/settings.json', f'{key} must be false for this context-only repository')
    if (settings.get('execution', {}).get('native_claude_settings') is not True
            or settings.get('execution', {}).get('native_settings_path') != '.claude/settings.json'):
        fail('config/settings.json', 'native Claude customization must point to .claude/settings.json')
    native = read_json('.claude/settings.json')
    hooks_config = native.get('hooks')
    if not isinstance(hooks_config, dict):
        hooks_config = {}
    if set(native) != {'hooks'} or set(hooks_config) != {'Stop'}:
        fail('.claude/settings.json', 'expected only the local Stop validation hook')
    stop_groups = hooks_config.get('Stop', [])
    expected_command = 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/validate_on_stop.py"'
    if (not isinstance(stop_groups, list) or len(stop_groups) != 1
            or not isinstance(stop_groups[0], dict)):
        fail('.claude/settings.json', 'register one Stop validation hook group')
    else:
        hooks = stop_groups[0].get('hooks', [])
        if (not isinstance(hooks, list) or len(hooks) != 1 or not isinstance(hooks[0], dict)
                or hooks[0].get('type') != 'command'
                or hooks[0].get('command') != expected_command
                or hooks[0].get('timeout') != 20):
            fail('.claude/settings.json', 'Stop must use the quoted local Python hook with a 20-second timeout')
    for relative in ('PROJECT.md', 'docs/claude-code.md', '.claude/hooks/validate_on_stop.py'):
        if not (root / relative).is_file():
            fail(relative, 'required project customization file is missing')
    skill_names = {'neuroquest-review', 'neuroquest-evidence', 'neuroquest-plan'}
    command_names = {'research-status', 'validate-research'}
    for folder, names, pattern in [('.claude/skills', skill_names, '*/SKILL.md'),
                                    ('.claude/commands', command_names, '*.md')]:
        files = sorted((root / folder).glob(pattern))
        discovered = {p.parent.name if p.name == 'SKILL.md' else p.stem for p in files}
        if discovered != names:
            fail(folder, 'expected project workflow entry points are missing or unexpectedly changed')
        for path in files:
            try:
                meta = parse_record(path.read_text())
            except (ValueError, TypeError) as exc:
                fail(path, f'invalid workflow frontmatter: {exc}')
                continue
            is_skill = path.name == 'SKILL.md'
            expected_fields = {'name', 'description'} if is_skill else {'description'}
            if set(meta) != expected_fields:
                fail(path, 'workflow metadata must stay minimal; no model override or implicit delegation')
            if is_skill and meta.get('name') != path.parent.name:
                fail(path, 'skill name must match its folder')
            description = meta.get('description')
            if not isinstance(description, str) or not description.strip() or len(description) > 300:
                fail(path, 'workflow description must be concise and nonempty')
            if path.stat().st_size > 2400:
                fail(path, 'workflow entry point exceeds 2400-byte context budget')
    servers = mcp.get('servers', [])
    if (mcp.get('native_mcp_configuration') is not False
            or {s.get('id') for s in servers if isinstance(s, dict)} != {'pubmed', 'vectorstore', 'labdata'}
            or len(servers) != 3):
        fail('config/mcp.json', 'expected three disabled inventory entries, not native MCP configuration')
    for server in servers:
        if not isinstance(server, dict) or server.get('enabled') is not False or server.get('transport') is not None:
            fail('config/mcp.json', 'integration entries must remain disabled without transports')
    if workflow.get('executable') is not False or workflow.get('scoring_model') != 'config/scoring-model.json':
        fail('workflows/preclinical-promotion.yaml', 'workflow must be descriptive and reference scoring model')
    if workflow.get('decision', {}).get('source') != 'config/scoring-model.json#/promotion':
        fail('workflows/preclinical-promotion.yaml', 'promotion policy must reference authoritative scoring rules')
    if not {'push', 'pull_request'}.issubset(ci.get('on', {})) or not ci.get('jobs'):
        fail('.github/workflows/research-review.yml', 'CI must run on pushes and pull requests with jobs')

    paths = inventory.get('paths', [])
    if len(paths) != 108 or len(set(paths)) != 108:
        fail('docs/original-file-inventory.json', 'expected 108 unique original skeleton paths')
    for relative in paths:
        if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
            fail('docs/original-file-inventory.json', 'inventory paths must be relative and stay within repository')
            continue
        path = root / relative
        if not path.is_file():
            fail(relative, 'original skeleton file is missing')
        elif path.stat().st_size < 180:
            fail(path, 'original file has not received substantive content')

    markdown = sorted(p for p in root.rglob('*.md') if not EXCLUDED.intersection(p.relative_to(root).parts))
    budgets = settings.get('context', {})
    for path in markdown:
        text = path.read_text()
        relative = path.relative_to(root)
        limit = budgets.get('leaf_max_bytes', 8000)
        if relative == Path('CLAUDE.md'):
            limit = budgets.get('root_instruction_max_bytes', 3200)
        elif path.name == 'CLAUDE.md':
            limit = budgets.get('role_instruction_max_bytes', 2400)
        elif path.name == 'README.md' and relative != Path('README.md'):
            limit = budgets.get('index_max_bytes', 6000)
        if len(text.encode()) > limit:
            fail(path, f'context budget exceeded ({len(text.encode())} > {limit} bytes)')
        if any(placeholder in text for placeholder in PLACEHOLDERS):
            fail(path, 'unreplaced skeleton placeholder')
        if path.name == 'CLAUDE.md' and re.search(r'(?m)^\s*@\S+', text):
            fail(path, 'bulk @ imports are prohibited; use navigation links')
        for target in LINK_PATTERN.findall(text):
            target = target.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            target_path = unquote(target.split('#', 1)[0])
            resolved = (path.parent / target_path).resolve()
            if not resolved.is_relative_to(root):
                fail(path, f'link escapes repository: {target}')
            elif not resolved.exists():
                fail(path, f'broken local link: {target}')

    records: dict[str, tuple[dict, Path]] = {}
    for folder, (pattern, count) in GROUPS.items():
        found = sorted((root / folder).glob(pattern))
        if len(found) != count:
            fail(folder, f'expected {count} records, found {len(found)}')
        for path in found:
            text = path.read_text()
            try:
                meta = parse_record(text)
            except (ValueError, TypeError) as exc:
                fail(path, str(exc))
                continue
            key = meta.get('id')
            if key != path.stem:
                fail(path, 'record ID must match filename')
            if not isinstance(key, str):
                continue
            if key in records:
                fail(path, f'duplicate record ID {key}')
            records[key] = (meta, path)
            if folder in {'molecules', 'experiments', 'memory'}:
                if meta.get('provenance') != 'synthetic' or 'SYNTHETIC DEMONSTRATION' not in text:
                    fail(path, 'synthetic provenance and visible label are required')
            if folder == 'literature':
                if meta.get('provenance') != 'published' or 'PUBLISHED EVIDENCE' not in text:
                    fail(path, 'published evidence label and provenance required')
                if not re.fullmatch(r'\d+', str(meta.get('pmid', ''))):
                    fail(path, 'valid PMID required')
                if not re.fullmatch(r'10\.\d{4,9}/\S+', str(meta.get('doi', ''))):
                    fail(path, 'valid DOI required')
                for token in (f'https://pubmed.ncbi.nlm.nih.gov/{meta.get("pmid")}/',
                              f'https://doi.org/{meta.get("doi")}'):
                    if token not in text:
                        fail(path, 'metadata identifier must match its source link')
                try:
                    date.fromisoformat(meta.get('verified_on', ''))
                except (ValueError, TypeError):
                    fail(path, 'ISO verification date required')
                if meta.get('review_scope') != 'indexed metadata and abstract only':
                    fail(path, 'declare the actual abstract-level review scope')
            if folder == 'experiments':
                if meta.get('status') not in {'completed', 'proposed', 'invalid'}:
                    fail(path, 'unknown experiment state')
                if meta.get('status') == 'proposed' and 'No results.' not in text:
                    fail(path, 'proposed studies must state No results.')
            if folder == 'memory' and meta.get('calendar_mapping', 'missing') is not None:
                fail(path, 'fictional periods must not imply actual calendar dates')

    pmids = [m.get('pmid') for m, p in records.values() if p.parent.name == 'literature']
    if len(set(pmids)) != len(pmids):
        fail('literature', 'publications must have unique PMIDs')
    for key, (meta, path) in records.items():
        for field, target_folder in [('experiment_ids', 'experiments'), ('candidate_ids', 'molecules'), ('literature_ids', 'literature')]:
            refs = meta.get(field, [])
            if not isinstance(refs, list) or len(refs) != len(set(refs)):
                fail(path, f'{field} must be a unique list'); continue
            for ref in refs:
                if ref not in records or records[ref][1].parent.name != target_folder:
                    fail(path, f'unknown {field} reference {ref}')
                    continue
                other = records[ref][0]
                reciprocal = {'experiment_ids': 'candidate_ids', 'candidate_ids': 'experiment_ids'}.get(field)
                if reciprocal and key not in other.get(reciprocal, []):
                    fail(path, f'non-reciprocal reference to {ref}')
        if path.parent.name != 'molecules':
            continue
        try:
            calculated = weighted_score(meta.get('scores', {}), weights)
            if meta.get('weighted_score') != calculated:
                fail(path, f'weighted score mismatch: expected {calculated}')
        except (ValueError, TypeError) as exc:
            fail(path, str(exc))
            calculated = None
        gates = meta.get('gates', {})
        if not isinstance(gates, dict) or set(gates) != GATES or any(v not in {'pass', 'fail', 'unknown'} for v in gates.values()):
            fail(path, 'all six promotion gates need pass/fail/unknown states')
            gates = {}
        disposition = meta.get('disposition')
        if disposition not in {'follow-up', 'hold', 'blocked', 'provisional', 'deprioritized', 'promoted'}:
            fail(path, 'unknown candidate disposition')
        if (meta.get('hard_blocks') or 'fail' in gates.values()) and disposition != 'blocked':
            fail(path, 'hard block or failed gate requires blocked disposition')
        if not isinstance(meta.get('human_approval'), bool):
            fail(path, 'human approval must be explicit boolean')
        if disposition == 'promoted' and not promotion_eligible(meta, policy):
            fail(path, 'promotion denied: score, evidence gates, or human approval missing')
        if calculated is None and meta.get('score_status') != 'provisional':
            fail(path, 'missing ratings must leave score provisional')
        if meta.get('human_approval') is not False or disposition == 'promoted':
            fail(path, 'baseline demonstration must have no approved/promoted candidates')

    example = root / '.env.example'
    if not example.exists():
        fail('.env.example', 'environment template is required')
    else:
        for line in example.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                if (key.endswith('_KEY') or key.endswith('_URL') or key == 'NCBI_EMAIL') and value:
                    fail('.env.example', f'{key} must be blank')
    # Never read .env: the file can contain secrets and is absent from a clean checkout.
    ignored = (root / '.gitignore').read_text() if (root / '.gitignore').exists() else ''
    if '.env' not in ignored.splitlines() or '!.env.example' not in ignored.splitlines():
        fail('.gitignore', 'ignore .env and retain the blank .env.example template')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        errors = validate(args.root)
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(f'Validation failed: malformed repository structure: {exc}', file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f'ERROR {error}', file=sys.stderr)
        return 1
    print('PASS: 108 original files; 15 candidates, 20 experiments, 20 publications, '
          '12 history periods, 10 ADRs; links, scores, gates, context budgets; '
          'native Stop hook, 3 skills, and 2 commands.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
