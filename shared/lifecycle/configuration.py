"""Read-only project discovery and checked configuration/setup handoffs."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

sys.dont_write_bytecode = True
AREAS = ('app-identity', 'toolchain', 'runtime', 'native-project', 'build-export', 'signing',
         'upload-auth', 'store-record', 'store-metadata', 'privacy-permissions', 'testing', 'recovery', 'tracking')
CAPABILITIES = ('authentication', 'deep-links', 'camera', 'notifications', 'payments', 'offline')
SECRET_SUFFIXES = {'.p8', '.p12', '.pfx', '.pem', '.key', '.jks', '.keystore', '.mobileprovision'}
SOURCE_SUFFIXES = {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.py', '.swift', '.kt', '.java', '.gradle', '.kts', '.sh'}
ENV_PATTERNS = [r'(?:process\.env|import\.meta\.env)\.([A-Za-z_][A-Za-z0-9_]*)',
                r'''(?:process\.env|os\.environ|environment)\s*\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]''',
                r'''(?:getenv|os\.getenv)\s*\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']''']


def api_module():
    spec = importlib.util.spec_from_file_location('ct_configuration_workflow', Path(__file__).with_name('workflow.py'))
    api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
    return api


def safe_relative(root, relative, api):
    path = Path(relative)
    api['require'](not path.is_absolute() and '..' not in path.parts, 'setup: expected repository-relative path')
    root = root.resolve()
    resolved = root / path
    cursor = root
    for part in path.parts:
        cursor = cursor / part
        api['require'](not cursor.is_symlink(), 'setup: symlink path not allowed')
    api['require'](resolved.resolve().is_relative_to(root.resolve()), 'setup: path escapes repository')
    return resolved


def check_private_paths(root, api):
    """Fail before source hashing if recognizable private files enter Git's public set."""
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
    for raw in names:
        if not raw:
            continue
        path = Path(raw.decode('utf-8'))
        template = path.name in ('.env.example', '.env.template')
        private = (path.name.startswith('.env') and not template) or path.suffix.lower() in SECRET_SUFFIXES
        api['require'](not private, 'discovery: private environment/signing file is tracked or not ignored; fix its storage/ignore rule before source hashing')


def discover(root, platform, api):
    root = root.resolve()
    api['require'](api['revision'](root) is not None, 'discovery: a local Git checkout is required; establish one before binding source')
    check_private_paths(root, api)
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
    files, manifests, variables, skipped = [], {}, {}, []
    dirs = {Path('.')}
    for raw in names:
        if not raw:
            continue
        relative = raw.decode('utf-8')
        path = root / relative
        parts = Path(relative).parts
        if any(p in ('node_modules', '.git', 'vendor', 'Pods', '.gradle', 'build', 'dist', '.next') for p in parts):
            continue
        dirs.add(Path(relative).parent)
        if path.is_symlink():
            skipped.append(relative); continue
        try:
            path = safe_relative(root, relative, api)
        except ValueError:
            skipped.append(relative); continue
        if not path.is_file():
            continue
        if path.name.startswith('.env') or path.suffix.lower() in SECRET_SUFFIXES:
            continue  # Do not read values, private key bytes, or their hashes.
        if path.name == 'package.json' or path.name in ('Info.plist', 'AndroidManifest.xml', 'project.pbxproj') or path.name.startswith(('capacitor.config.', 'app.config.', 'app.json', 'build.gradle', 'settings.gradle')) or path.suffix in ('.entitlements', '.xcconfig'):
            files.append(relative)
        if path.stat().st_size > 1024 * 1024:
            if path.suffix in SOURCE_SUFFIXES or path.name == 'package.json': skipped.append(relative)
            continue
        if path.name == 'package.json':
            data = api['load'](path)
            api['require'](isinstance(data, dict) and isinstance(data.get('dependencies', {}), dict) and isinstance(data.get('devDependencies', {}), dict), 'discovery: malformed dependency manifest')
            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            manifests[relative] = sorted(name for name in ('@capacitor/core', 'expo', 'react-native', 'next', 'vite', 'react-scripts') if name in dependencies)
        if path.suffix in SOURCE_SUFFIXES:
            content = path.read_text(encoding='utf-8', errors='replace')
            for pattern in ENV_PATTERNS:
                for name in re.findall(pattern, content): variables.setdefault(name, set()).add(relative)
    env_files = []
    for directory in sorted(dirs, key=str):
        base = root / directory
        for path in sorted(base.glob('.env*')):
            relative = path.relative_to(root).as_posix()
            try:
                safe_relative(root, relative, api)
            except ValueError:
                skipped.append(relative); continue
            if path.is_symlink() or not path.is_file(): continue
            ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--', relative], cwd=root).returncode == 0
            env_files.append({'path': relative, 'ignored': ignored})
    stacks = sorted({name for names in manifests.values() for name in names})
    return {'schema_version': 1, 'kind': 'ct-configuration-discovery.v1', 'platform': platform,
            'repository': {'path': str(root), 'revision': api['revision'](root), 'working_tree_sha256': api['tree_digest'](root)},
            'configuration_files': sorted(files), 'package_manifests': manifests, 'detected_dependencies': stacks,
            'environment_references': [{'name': k, 'paths': sorted(v)} for k, v in sorted(variables.items())],
            'environment_files': env_files, 'skipped': sorted(skipped),
            'limitations': ['Source patterns are discovery hints, not a complete parser. Review dynamic/custom loaders, ignored configuration and platform settings manually.',
                            'Environment values and signing files were not parsed. Recognizable private files must be ignored and untracked before source hashing; public .env.example/.env.template files belong to the source fingerprint. No build, installation, secret lookup or provider request was executed.']}


def check_input(rule, value, context, api):
    data = value['inputs']
    if data['discovery'] is not None:
        snapshot = api['load'](api['reference'](data['discovery'], context['base']))
        api['require']('repository' in context, 'setup: discovery requires repository identity')
        actual = discover(context['repository'], rule['platform'], api)
        api['require'](snapshot == actual, 'setup: stale or modified discovery; regenerate from the current source')
        context['configuration_discovery'] = snapshot


def check_report(rule, result, value, context, api):
    require = api['require']
    data = value['inputs']
    rows = result['configuration']
    plan = result['setup_plan']
    ids = {r['id']: r for r in rows}
    if rows:
        required_areas = set(AREAS) | set(data['requested_capabilities'])
        require(required_areas <= {r['area'] for r in rows if r['required']}, 'setup: missing required configuration area')
        for row in rows:
            require(not (row['sensitive'] and row['bundled']), 'setup: secrets must never be bundled into a client')
            require(not row['sensitive'] or row['storage'] in ('local-env', 'ci-secret', 'keychain', 'secret-manager'), 'setup: unsafe secret storage')
            if row['status'] == 'configured': require(bool(row['evidence_ids']), 'setup: configured item lacks verification evidence')
            if row['storage'] == 'local-env':
                require(result['environment_loader'] not in ('unknown', 'not-applicable'), 'setup: identify the actual environment loader')
                if row['sensitive'] and row['status'] == 'configured':
                    snapshot = context.get('configuration_discovery', {})
                    require(any(e['path'] == row['location'] and e['ignored'] for e in snapshot.get('environment_files', [])), 'setup: local secret file must exist and be ignored')
            prefixes = set(data['build_exposure_prefixes']) | {'NEXT_PUBLIC_', 'VITE_', 'EXPO_PUBLIC_', 'REACT_APP_'}
            if row['sensitive']:
                require(not any(row['name'].startswith(p) for p in prefixes), 'setup: client-exposed variable cannot be a secret')
        env_names = {r['name'] for r in rows if r['area'] == 'runtime'}
        expected_env = {r['name'] for r in context.get('configuration_discovery', {}).get('environment_references', [])}
        require(expected_env <= env_names, 'setup: discovered environment reference omitted from inventory')
    require(all(p['configuration_id'] in ids for p in plan), 'setup: plan references unknown configuration item')
    unresolved = {r['id'] for r in rows if r['required'] and r['status'] in ('missing', 'invalid', 'unverified')}
    require(unresolved <= {p['configuration_id'] for p in plan if p['status'] in ('pending', 'blocked')}, 'setup: missing actionable setup step')
    for step in plan:
        if step['status'] == 'done':
            require(ids[step['configuration_id']]['status'] == 'configured' and bool(step['evidence_ids']), 'setup: done step lacks verified configuration')
    wrapper = result['wrapper']
    if wrapper['mode'] != 'unknown':
        require(wrapper['mode'] in ('existing-native', 'capacitor', 'expo', 'react-native', 'custom', 'unsupported'), 'setup: unknown wrapper route')
    if data['setup_mode'] == 'wrap-web' and wrapper['mode'] == 'existing-native':
        raise ValueError('setup: web wrapping cannot claim an existing-native route')


def check_ready(rule, result, value, context, api):
    require = api['require']
    data = value['inputs']
    require('configuration_discovery' in context, 'setup: current generated discovery required')
    require(bool(result['configuration']), 'setup: configuration inventory is missing')
    if data['target_stage'] == 'discover':
        require(result['store_readback'] is None and result['testing_readback'] is None and result['artifact_sha256'] is None and result['device_proof'] is None and result['acceptance_source'] is None,
                'setup: discovery must not claim an artifact or provider milestone')
        return
    rows = result['configuration']
    require(all(r['status'] in ('configured', 'not-applicable') for r in rows if r['required']), 'setup: unresolved required configuration')
    require(all(any(r['area'] == area and r['required'] and r['status'] == 'configured' for r in rows)
                for area in ('app-identity', 'toolchain', 'runtime', 'native-project', 'build-export', 'testing', 'tracking')),
            'setup: core native configuration cannot be marked not-applicable')
    require(not context['configuration_discovery']['skipped'], 'setup: discovery skipped sources; resolve coverage before release')
    wrapper = result['wrapper']
    require(wrapper['mode'] not in ('unknown', 'unsupported') and data['platform_variant'] in wrapper['native_targets'], 'setup: native wrapper target is not ready')
    if wrapper['mode'] == 'capacitor':
        require(set(wrapper['native_targets']) <= {'ios', 'android'}, 'setup: Capacitor supports only the selected iOS/Android native route; select a separate route for other targets')
    require(bool(wrapper['config_files']), 'setup: native configuration files missing')
    root = context['repository']
    for relative in wrapper['config_files']:
        require(safe_relative(root, relative, api).is_file(), 'setup: native configuration file does not exist')
    api['rule_valid']({'type': 'command', 'field': 'wrapper.smoke_check', 'exit': 'zero'}, result, value, context)
    if data['setup_mode'] == 'wrap-web':
        if wrapper['delivery'] == 'bundled':
            require(wrapper['web_output_dir'] is not None and safe_relative(root, wrapper['web_output_dir'], api).joinpath('index.html').is_file(), 'setup: built web output index.html missing')
        elif wrapper['delivery'] == 'hosted':
            require(wrapper['mode'] != 'capacitor', 'setup: Capacitor server.url is a development facility, not a production wrapper plan')
            url = urlparse(wrapper['runtime_url'] or '')
            require(url.scheme == 'https' and url.hostname not in (None, 'localhost', '127.0.0.1', '::1') and not url.username and not url.password and not url.query and not url.fragment,
                    'setup: hosted wrapper requires a safe production HTTPS URL')
        else:
            raise ValueError('setup: web delivery route is unresolved')
        if wrapper['source_kind'] == 'ssr': require(wrapper['backend_plan'] != 'not-applicable', 'setup: SSR requires an explicit server/backend plan')
        api['rule_valid']({'type': 'command', 'field': 'wrapper.sync_check', 'exit': 'zero'}, result, value, context)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--platform', required=True, choices=('apple', 'android'))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        module = api_module()
        snapshot = discover(args.repository, args.platform, vars(module))
        module.write_new(args.output, snapshot)
        print('Wrote redacted discovery; inspect the report and complete the configuration inventory.')
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Discovery could not complete: {error if isinstance(error, ValueError) else type(error).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
