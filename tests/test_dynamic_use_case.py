"""Behavioral checks for the independently installed actor-first explorer."""
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dynamic_umls_fixture import ROOT, installer

NAME = 'ct-dynamic-use-case'
MODEL = ROOT / 'skills/ct-dynamic-uml/assets/examples/use-case.json'
SPEC = importlib.util.spec_from_file_location('use_case_validation',
    ROOT / 'shared/dynamic-uml/use_case_model.py')
validation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation)


class DynamicUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.model = json.loads(MODEL.read_text(encoding='utf-8'))

    def reject(self, mutate):
        candidate = copy.deepcopy(self.model)
        mutate(candidate)
        with self.assertRaises(ValueError):
            validation.validate(candidate)

    def test_sample_is_valid_and_recovery_cycles_do_not_expand_recursively(self):
        validation.validate(self.model)
        error = self.model['use_cases']['login']['scenarios'][2]
        error['recovery'].append({'label': 'Try this path again', 'to': error['id']})
        validation.validate(self.model)

    def test_references_and_evidence_are_checked(self):
        self.reject(lambda m: m['actors']['admin']['subjects'].append('unknown'))
        self.reject(lambda m: m['subjects']['users']['cases'].append('unknown'))
        self.reject(lambda m: m['use_cases']['login']['evidence'].update(status='verified'))
        self.reject(lambda m: m['use_cases']['login']['scenarios'][2]['recovery'][0]
                    .update(to='missing'))
        self.reject(lambda m: m['use_cases']['login']['scenarios'].append(
            copy.deepcopy(m['use_cases']['login']['scenarios'][0])))
        self.reject(lambda m: m['subjects'].update(orphan={'name': 'Orphan', 'cases': ['login']}))
        self.reject(lambda m: m['sources'].append(
            {'id': 'bad', 'label': 'Bad source', 'reference': 'javascript:alert(1)'}))
        self.reject(lambda m: m['actors'].update(constructor=m['actors']['admin']))
        self.reject(lambda m: m['use_cases']['login']['scenarios'][0].update(category=[]))

    def test_add_and_remove_require_reconciling_references(self):
        original_login = copy.deepcopy(self.model['use_cases']['login'])
        added = copy.deepcopy(self.model['use_cases']['roles'])
        added['id'] = 'review-access'
        added['name'] = 'Review access'
        self.model['use_cases'][added['id']] = added
        self.model['subjects']['users']['cases'].append(added['id'])
        validation.validate(self.model)
        del self.model['use_cases'][added['id']]
        with self.assertRaises(ValueError):
            validation.validate(self.model)
        self.model['subjects']['users']['cases'].remove(added['id'])
        validation.validate(self.model)
        self.assertEqual(original_login, self.model['use_cases']['login'])

    def test_sources_support_verified_status_without_claiming_runtime_proof(self):
        self.model['sources'] = [
            {'id': 'auth', 'label': 'Inspected authentication route',
             'reference': 'src/routes/auth.py'}]
        self.model['use_cases']['login']['evidence'] = {
            'status': 'verified', 'source_ids': ['auth']}
        validation.validate(self.model)

    def test_each_agent_gets_an_independent_render_and_extract_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            home = base / 'home with spaces'
            for agent, destination in installer.TARGETS.items():
                with self.subTest(agent=agent):
                    with contextlib.redirect_stdout(io.StringIO()):
                        installer.install(ROOT, home, [agent], [NAME], False)
                    package = home / destination / NAME
                    script = package / 'scripts/render_use_case.py'
                    source = package / 'assets/example.json'
                    output = base / f'{agent}.html'
                    recovered = base / f'{agent}.json'
                    def run(*args):
                        return subprocess.run([sys.executable, str(script), *map(str, args)],
                            capture_output=True, text=True)
                    self.assertEqual(run('validate', source).returncode, 0)
                    result = run('render', source, '--output', output)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    page = output.read_text(encoding='utf-8')
                    self.assertIn('data:image/png;base64,', page)
                    self.assertNotIn('<script src=', page)
                    self.assertNotIn('«extend»', page)
                    self.assertNotIn('«include»', page)
                    self.assertNotIn('__RUNTIME__', page)
                    self.assertEqual(run('extract', output, '--output', recovered).returncode, 0)
                    self.assertEqual(json.loads(recovered.read_text()), self.model)
                    snapshot = output.read_bytes()
                    self.assertNotEqual(run('render', source, '--output', output).returncode, 0)
                    self.assertEqual(output.read_bytes(), snapshot)
                    snapshot = recovered.read_bytes()
                    self.assertNotEqual(run('extract', output, '--output', recovered).returncode, 0)
                    self.assertEqual(recovered.read_bytes(), snapshot)

    def test_html_text_and_model_embedding_are_inert(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            installer.assemble(ROOT, base / 'skills', [NAME])
            script = base / 'skills' / NAME / 'scripts/render_use_case.py'
            malicious = '</script><script>alert("sample")</script>__RUNTIME__'
            self.model['scope'] = malicious
            self.model['use_cases']['login']['name'] = '<img src=x onerror=alert(1)>'
            source = base / 'source.json'
            source.write_text(json.dumps(self.model), encoding='utf-8')
            output = base / 'output.html'
            result = subprocess.run([sys.executable, str(script), 'render', str(source),
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = output.read_text(encoding='utf-8')
            self.assertNotIn('</script><script>alert', page)
            self.assertIn('\\u003c/script\\u003e', page)
            self.assertIn('&lt;/script&gt;', page)
            recovered = base / 'recovered.json'
            result = subprocess.run([sys.executable, str(script), 'extract', str(output),
                '--output', str(recovered)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(recovered.read_text()), self.model)


if __name__ == '__main__':
    unittest.main()
