"""Behavioral checks for standalone diagram packages and HTML generation."""
import contextlib
import io
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


family = load(ROOT / 'scripts/dynamic_umls.py', 'dynamic_family')
renderer = load(family.CANONICAL / 'scripts/render.py', 'dynamic_render')
installer = load(ROOT / 'scripts/skills.py', 'dynamic_install')


class DynamicUmlTests(unittest.TestCase):
    def model(self, kind='sequence'):
        return json.loads((family.CANONICAL / f'assets/examples/{kind}.json').read_text(encoding='utf-8'))

    def test_canonical_copies_and_review_examples_are_current(self):
        for path, expected in family.outputs().items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), expected)

    def test_every_skill_renders_from_an_isolated_installed_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / 'home with spaces'
            for agent in installer.TARGETS:
                with contextlib.redirect_stdout(io.StringIO()):
                    installer.install(ROOT, home, [agent], list(family.NAMES.values()), False)
                for kind, name in family.NAMES.items():
                    folder = home / installer.TARGETS[agent] / name
                    output = Path(temporary) / f'{agent}-{kind}.html'
                    result = subprocess.run([sys.executable, str(folder / 'scripts/render.py'),
                        str(folder / 'assets/example.json'), '--expect', kind, '--output', str(output)],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    page = output.read_text(encoding='utf-8')
                    self.assertIn('https://contexttemplates.com', page)
                    self.assertNotIn('__DIAGRAM_DATA__', page)
                    self.assertNotIn('<script src=', page)
                    self.assertNotIn('<link ', page)

    def test_renderer_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'keep.html'
            output.write_text('user content')
            result = subprocess.run([sys.executable, str(family.CANONICAL / 'scripts/render.py'),
                str(family.CANONICAL / 'assets/examples/class.json'), '--output', str(output)],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding='utf-8'), 'user content')

    def test_model_text_cannot_break_out_of_embedded_json(self):
        model = self.model()
        attack = '</script><img src=x onerror=alert(1)>'
        model['title'] = attack
        model['scenarios'][0]['steps'][0]['body'] = attack
        page = renderer.render(model)
        payload = page.split('<script id="diagram-data" type="application/json">')[1].split('</script>')[0]
        self.assertNotIn('<', payload)
        self.assertEqual(json.loads(payload)['title'], attack)
        self.assertNotIn('<img src=x', page)
        self.assertIn('&lt;/script&gt;', page)

    def test_literal_template_markers_remain_user_data(self):
        model = self.model()
        model['title'] = '__DIAGRAM_DATA__ & explanation'
        model['lede'] = '__PAGE_TITLE__'
        page = renderer.render(model)
        payload = page.split('<script id="diagram-data" type="application/json">')[1].split('</script>')[0]
        self.assertEqual(json.loads(payload), model)
        self.assertIn('<title>__DIAGRAM_DATA__ &amp; explanation</title>', page)

    def test_invalid_paths_and_notation_are_rejected(self):
        for mutate in [
            lambda m: m.update(type=[]),
            lambda m: m['nodes'][0].update(kind=[]),
            lambda m: m['edges'][0].update(kind=[]),
            lambda m: m['edges'][0].update(to={}),
            lambda m: m['edges'][0].update(to='missing'),
            lambda m: m['nodes'][1].update(id=m['nodes'][0]['id']),
            lambda m: m['edges'][0].update(kind='composition'),
            lambda m: m['scenarios'][0]['steps'][0].update(nodes=['browser']),
            lambda m: m['sources'][0].update(href='javascript:alert(1)'),
            lambda m: m['sources'][0].update(href='https://user:secret@example.com'),
            lambda m: m.update(height=200),
            lambda m: m['nodes'][0].update(x=float('nan')),
            lambda m: m['nodes'][0].update(x=0),
        ]:
            model = self.model(); mutate(model)
            with self.subTest(model=model), self.assertRaises(ValueError):
                renderer.render(model)
        with self.assertRaises(ValueError):
            renderer.render(self.model(), expected='class')

    def test_class_relationship_direction_and_activity_parallelism(self):
        classes = self.model('class')
        composition = next(e for e in classes['edges'] if e['kind'] == 'composition')
        inheritance = next(e for e in classes['edges'] if e['kind'] == 'inheritance')
        self.assertEqual((composition['from'], composition['to']), ('order', 'item'))
        self.assertEqual((inheritance['from'], inheritance['to']), ('card', 'payment'))
        parallel = self.model('activity')['scenarios'][0]['steps'][1]
        self.assertTrue({'stock', 'payment', 'fork'}.issubset(parallel['nodes']))
        self.assertTrue({'stock-start', 'payment-start'}.issubset(parallel['edges']))


if __name__ == '__main__':
    unittest.main()
