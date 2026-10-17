#!/usr/bin/env python3
"""Validate a next-session handoff and render a standalone continuation prompt."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location(
    'ct_handoff_validation', Path(__file__).with_name('handoff_validation.py'))
checks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checks)


def render(intake, output, base):
    sources = checks.validate_output(intake, output, base)
    if output['status'] == 'no-follow-up':
        lines = ['No next-session prompt is needed.', '', output['summary']]
        for item in output['unverified_state']:
            lines.append('Unverified information: ' + item['statement'])
        return '\n'.join(lines) + '\n'
    scope = intake['scope']
    lines = [f"You are continuing work on {scope['description']}."]
    if scope['workspace'] is None:
        lines.append('Workspace is unverified; establish its location before acting.')
    else:
        lines.append('Workspace: ' + scope['workspace'])
    lines += ['', 'Read first:']
    for item in output['read_first']:
        source = sources[item['source_id']]
        lines.append(f"- {source['location']}: {item['instruction']}")
    lines += ['', 'Verified state:']
    for item in output['verified_state']:
        lines.append(f"- {item['statement']} (sources: {', '.join(item['source_ids'])})")
    if not output['verified_state']:
        lines.append('- No completed work has been verified.')
    lines += ['', 'Unverified state — check before acting:']
    for item in output['unverified_state']:
        lines.append(f"- {item['statement']} First check: {item['check_first']}")
    if not output['unverified_state']:
        lines.append('- No additional uncertainty was recorded; refresh state before action.')
    lines += ['', 'Sources checked in the previous session:']
    for source in sources.values():
        lines.append(f"- {source['id']} [{source['status']}]: {source['location']}")
        if source['status'] == 'verified':
            path = checks.source_file(source['reference'], base)
            lines.append(f"  Evidence: {path}; SHA-256: {source['reference']['sha256']}; checked: {source['checked_at']}")
    lines += ['', 'Current decision frame:']
    frame = output['decision_frame']
    lines += ['- Deciding: ' + item for item in frame['deciding']]
    lines += ['- Not deciding: ' + item for item in frame['not_deciding']]
    lines.append('- Why this next step: ' + frame['reason'])
    lines += ['', 'Immediate goal:', output['objective'], '', 'Constraints and non-goals:']
    lines += ['- ' + item for item in output['constraints']]
    lines += ['', 'Implementation and validation expectations:']
    lines.append('- Refresh repository and remote state; this handoff is evidence, not new authorization.')
    for item in output['validation']:
        lines.append(f"- {item['instruction']} Previous result: {item['previous_result']}.")
    for item in output['blockers']:
        lines.append(f"- Blocked: {item['reason']} Next action: {item['next_action']}")
    lines += ['', 'Final response should include:']
    lines += ['- ' + item for item in output['final_response']]
    return '\n'.join(lines) + '\n'


def write_prompt(path, prompt, workspace):
    path = Path(path)
    checks.safe(b'', path.name)
    checks.require(not path.is_symlink(), 'Refusing linked output')
    target = path.resolve()
    installed = Path(__file__).resolve().parents[1]
    checks.require(target != installed and installed not in target.parents,
                   'Store runtime handoffs outside the installed skill')
    if workspace is not None:
        root = Path(workspace).resolve()
        checks.require(target != root and root not in target.parents,
                       'Store runtime handoffs outside the inspected workspace')
    data = prompt.encode('utf-8')
    if path.exists():
        checks.require(path.is_file() and path.read_bytes() == data,
                       'Output exists with different content; preserve it and choose a new path')
        return 'unchanged'
    # Exclusive creation refuses races and existing/broken links, without overwrite.
    with path.open('xb') as stream:
        stream.write(data)
    return 'created'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate-input', 'hash-input', 'validate-output', 'render'):
        command = sub.add_parser(name)
        command.add_argument('input', type=Path)
        if name in ('validate-output', 'render'):
            command.add_argument('output', type=Path)
        if name == 'render':
            command.add_argument('--prompt', type=Path, required=True)
    args = parser.parse_args()
    try:
        intake = checks.load(args.input)
        base = args.input.resolve().parent
        checks.validate_input(intake, base)
        if args.command == 'hash-input':
            print(checks.digest(intake))
        elif args.command == 'validate-input':
            print('Input valid; source bytes checked. Live facts are not authenticated.')
        else:
            output = checks.load(args.output)
            checks.validate_output(intake, output, base)
            if args.command == 'validate-output':
                print('Output valid; structure and source bindings checked, not factual truth.')
            else:
                prompt = render(intake, output, base)
                action = write_prompt(args.prompt, prompt, intake['scope']['workspace'])
                print(f'{action}: {args.prompt}')
        return 0
    except (OSError, ValueError, RecursionError) as error:
        # Never echo a malformed JSON excerpt, path or raw command output.
        message = str(error) if type(error) is ValueError else type(error).__name__
        print('Handoff check failed: ' + message, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
