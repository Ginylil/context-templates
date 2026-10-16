"""Bounded UI occurrence discovery and evidence checks; no automatic code edits."""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
EXTENSIONS = {'.css', '.scss', '.sass', '.less', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
              '.html', '.htm', '.vue', '.svelte', '.astro', '.json', '.mdx', '.php', '.erb', '.swift', '.kt', '.dart'}
EXCLUDED = {'.git', 'node_modules', 'vendor', 'dist', 'build', '.next', 'coverage', 'Pods', '.gradle'}


def api_module():
    spec = importlib.util.spec_from_file_location('ct_interface_workflow', Path(__file__).with_name('workflow.py'))
    api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
    return api


def relative_path(root, name, api):
    part = Path(name)
    api['require'](not part.is_absolute() and '..' not in part.parts, 'interface: expected repository-relative path')
    cursor = root.resolve()
    for p in part.parts:
        cursor = cursor / p
        api['require'](not cursor.is_symlink(), 'interface: symlink path is outside scan coverage')
    api['require'](cursor.resolve().is_relative_to(root.resolve()), 'interface: path escapes repository')
    return cursor


def scan(root, search, api):
    root = root.resolve()
    api['fields'](search, 'roots terms', 'interface search')
    for key in ('roots', 'terms'):
        api['strings'](search[key], 'search.' + key, 1)
        api['require'](len(set(search[key])) == len(search[key]), 'interface: duplicate search selector')
    roots = [relative_path(root, name, api) for name in search['roots']]
    api['require'](all(p.is_dir() for p in roots), 'interface: each scan root must exist as a directory')
    api['require'](api['revision'](root) is not None, 'interface: Git checkout with HEAD required')
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
    files, matches, skipped = {}, [], []
    for raw in sorted(set(names)):
        if not raw:
            continue
        name = raw.decode('utf-8')
        candidate = root / name
        if not any(candidate.is_relative_to(p) for p in roots):
            continue
        if any(p in EXCLUDED for p in Path(name).parts) or candidate.suffix.lower() not in EXTENSIONS or candidate.name.startswith('.env'):
            continue
        try:
            path = relative_path(root, name, api)
            if not path.is_file():
                skipped.append({'path': name, 'reason': 'Missing or nonregular source'}); continue
            if path.stat().st_size > 1024 * 1024:
                skipped.append({'path': name, 'reason': 'Source exceeds 1 MiB'}); continue
            content = path.read_text(encoding='utf-8')
        except (ValueError, UnicodeError, OSError):
            skipped.append({'path': name, 'reason': 'Unreadable, non-UTF8 or linked source'}); continue
        files[name] = api['file_digest'](path)
        for line, content_line in enumerate(content.splitlines(), 1):
            for term in search['terms']:
                if term in content_line:
                    matches.append({'id': 'match-' + api['digest']([name, line, term]), 'path': name, 'line': line, 'term': term})
    return {'kind': 'ct-interface-scan.v1', 'schema_version': 1,
            'repository': {'path': str(root), 'revision': api['revision'](root), 'working_tree_sha256': api['tree_digest'](root)},
            'search': search, 'files': files, 'matches': matches, 'skipped': skipped,
            'limitations': ['Literal, case-sensitive source discovery only; generated/dependency/ignored files and unsupported extensions are excluded.',
                            'Review component consumers, routes, semantic aliases, runtime states and intentional variants manually; this scan does not prove whole-project coverage.']}


def snapshot(ref, value, context, api, current=False):
    data = api['load'](api['reference'](ref, context['base']))
    api['fields'](data, 'kind schema_version repository search files matches skipped limitations', 'interface scan')
    api['require'](data['kind'] == 'ct-interface-scan.v1' and data['schema_version'] == 1, 'interface: wrong scan kind/version')
    api['require'](data['search'] == value['inputs']['search'], 'interface: scan search scope differs from intake')
    api['require']('repository' in context, 'interface: scan requires repository identity')
    api['require'](Path(data['repository']['path']).resolve() == context['repository'].resolve(), 'interface: scan is for another repository')
    api['require'](isinstance(data['files'], dict) and isinstance(data['matches'], list), 'interface: malformed scan inventory')
    ids = []
    for hit in data['matches']:
        api['fields'](hit, 'id path line term', 'interface match')
        api['require'](hit['path'] in data['files'] and type(hit['line']) is int and hit['line'] > 0 and hit['term'] in data['search']['terms'], 'interface: malformed match')
        api['require'](hit['id'] == 'match-' + api['digest']([hit['path'], hit['line'], hit['term']]), 'interface: modified match identity')
        ids.append(hit['id'])
    api['require'](len(ids) == len(set(ids)), 'interface: duplicate scan match')
    if current:
        api['require'](data == scan(context['repository'], value['inputs']['search'], api), 'interface: stale or modified final scan')
    return data


def check_input(rule, value, context, api):
    data = value['inputs']
    for viewport in data['viewports']:
        api['require'](viewport['width'] > 0 and viewport['height'] > 0, 'interface: invalid viewport')
    if data['before_scan'] is not None:
        context['interface_before'] = snapshot(data['before_scan'], value, context, api)


def question(key, context, api, answered):
    ledger = context.get('ledger')
    api['require'](ledger is not None and key is not None, 'interface: uncertainty requires the shared question ledger')
    state = api['definition'].replay(ledger)
    asked = {q['id'] for e in ledger['events'] if e['type'] == 'ask' for q in e['questions']}
    api['require'](key in asked, 'interface: unknown clarification question')
    api['require']((key not in state['pending_question_ids']) == answered, 'interface: clarification must have an actual answer' if answered else 'interface: unresolved occurrence must name a pending question')


def check_report(rule, result, value, context, api):
    data, require = value['inputs'], api['require']
    require(result['expected_behavior'] == data['expected_behavior'], 'interface: correction differs from agreed intake')
    require(not result['occurrences'] or 'repository' in context, 'interface: occurrence inventory requires repository identity')
    if data['understanding_source'] == 'user-answer':
        question(data['understanding_question_id'], context, api, True)
    if data['understanding_source'] == 'repository-evidence':
        require(bool(data['understanding_source_ids']), 'interface: understanding needs source evidence')
    final = None
    if result['after_scan'] is not None:
        final = snapshot(result['after_scan'], value, context, api, current=True)
        context['interface_after'] = final
    before = context.get('interface_before')
    for row in result['occurrences']:
        for name in [row['path'], *row['owner_paths']]:
            relative_path(context['repository'], name, api)
        if row['verdict'] == 'uncertain':
            question(row['question_id'], context, api, False)
            require(before is not None, 'interface: uncertain file requires a baseline before any edits')
            if before:
                for name in {row['path'], *row['owner_paths']}:
                    original = before['files'].get(name)
                    path = relative_path(context['repository'], name, api)
                    require(original is not None and path.is_file() and api['file_digest'](path) == original,
                            'interface: a file with an uncertain correction was changed; hold its shared owners for clarification too')
        elif row['question_id'] is not None:
            question(row['question_id'], context, api, True)
        if row['verdict'] == 'fixed':
            require(data['understanding_source'] != 'unresolved' and data['expected_behavior'] is not None,
                    'interface: cannot fix an unclear correction')
            require(bool(row['surface_ids']), 'interface: fixed occurrence lacks rendered coverage')
        for link in row['scan_matches']:
            inventory = before if link['phase'] == 'before' else final
            require(inventory is not None and any(h['id'] == link['match_id'] and h['path'] == row['path'] for h in inventory['matches']),
                    'interface: occurrence cites unknown scan match or wrong location')


def image(key, viewport, context, api):
    item = context['evidence'][key]
    api['require'](item['kind'] == 'artifact', 'interface: screenshot must be an image artifact')
    content = item['path'].read_bytes()
    api['require'](len(content) >= 24 and content[:8] == b'\x89PNG\r\n\x1a\n' and content[12:16] == b'IHDR', 'interface: expected actual PNG screenshot')
    width, height = struct.unpack('>II', content[16:24])
    api['require'](width == viewport['width'] and height == viewport['height'], 'interface: screenshot dimensions differ from declared viewport; use viewport PNGs at device scale 1')
    return content


def check_ready(rule, result, value, context, api):
    data, require = value['inputs'], api['require']
    require(data['expected_behavior'] is not None and data['understanding_source'] != 'unresolved', 'interface: intended correction is unclear')
    require('interface_before' in context and 'interface_after' in context, 'interface: before and current final scans required')
    before, after = context['interface_before'], context['interface_after']
    require(bool(before['files']) and not before['skipped'] and not after['skipped'], 'interface: incomplete source scan coverage')
    proof = context['evidence'][result['before_check']]['data']
    require(proof['source_revision'] == before['repository']['revision'] and proof['working_tree_sha256'] == before['repository']['working_tree_sha256'], 'interface: baseline scan differs from reproduced source')
    rows = result['occurrences']
    require(bool(rows) and any(r['verdict'] == 'fixed' for r in rows), 'interface: no verified corrections')
    require(all(r['verdict'] != 'uncertain' for r in rows), 'interface: unanswered correction remains')
    for phase, inventory in (('before', before), ('after', after)):
        represented = [link['match_id'] for row in rows for link in row['scan_matches'] if link['phase'] == phase]
        require(len(represented) == len(set(represented)) and set(represented) == {h['id'] for h in inventory['matches']}, 'interface: missing or duplicate occurrence classification')
    surfaces = {s['id']: s for s in result['surfaces']}
    views = {v['id']: v for v in data['viewports']}
    require({s['viewport_id'] for s in surfaces.values()} == set(views), 'interface: missing viewport proof')
    require(bool(result['scope_review']['routes']) and bool(result['scope_review']['components']), 'interface: review route and component consumers beyond literal matches')
    for row in rows:
        require(all(name in before['files'] or name in after['files'] for name in [row['path'], *row['owner_paths']]), 'interface: occurrence lies outside inspected source scope')
        if row['verdict'] == 'fixed':
            require({surfaces[s]['viewport_id'] for s in row['surface_ids'] if s in surfaces} == set(views), 'interface: fixed occurrence lacks requested viewport coverage')
        require(bool(row['evidence_ids']), 'interface: occurrence lacks evidence or exception justification')
        require(all(s in surfaces and row['id'] in surfaces[s]['occurrence_ids'] for s in row['surface_ids']), 'interface: unknown or unlinked rendered surface')
    for surface in surfaces.values():
        require(surface['status'] == 'passed' and surface['viewport_id'] in views, 'interface: rendered check did not pass')
        require(bool(surface['occurrence_ids']) and all(i in {r['id'] for r in rows} for i in surface['occurrence_ids']), 'interface: surface cites unknown occurrence')
        image(surface['before'], views[surface['viewport_id']], context, api)
        image(surface['after'], views[surface['viewport_id']], context, api)
        require(context['evidence'][surface['inspection']]['kind'] == 'observation', 'interface: actual visual inspection observation required')
        api['rule_valid']({'type': 'command', 'field': 'interaction_check', 'exit': 'zero'}, surface, value, context)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--root', action='append', required=True, dest='roots')
    parser.add_argument('--term', action='append', required=True, dest='terms')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        api = api_module()
        api.write_new(args.output, scan(args.repository, {'roots': args.roots, 'terms': args.terms}, vars(api)))
        print('Wrote private occurrence inventory without source-line contents; no project code was executed.')
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f'Interface scan could not complete: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
