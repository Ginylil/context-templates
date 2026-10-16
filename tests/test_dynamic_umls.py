"""Behavioral checks for standalone diagram packages and HTML generation."""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dynamic_umls_fixture import (
    DynamicUmlFixture,
    ROOT,
    SKILLS,
    CANONICAL_PACKAGE,
    load,
    family,
    renderer,
    installer,
)


class DynamicUmlTests(DynamicUmlFixture):
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

    def test_renamed_catalog_preserves_installed_legacy_copies(self):
        legacy_names = {
            'dynamic-umls': 'ct-dynamic-uml',
            'dynamic-sequence-diagram': 'ct-dynamic-uml-sequence',
            'dynamic-class-diagram': 'ct-dynamic-uml-class',
            'dynamic-flowchart': 'ct-dynamic-uml-flowchart',
            'dynamic-state-diagram': 'ct-dynamic-uml-state',
            'dynamic-activity-diagram': 'ct-dynamic-uml-activity',
            'dynamic-component-diagram': 'ct-dynamic-uml-component',
        }
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            legacy = base / 'old-catalog'
            home = base / 'home'
            for name in legacy_names:
                folder = legacy / 'skills' / name
                folder.mkdir(parents=True)
                (folder / 'SKILL.md').write_text(
                    f'---\nname: {name}\ndescription: "Legacy diagram skill"\n---\nLegacy instructions.\n',
                    encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                installer.install(legacy, home, list(installer.TARGETS), [], False)
            snapshots = {}
            for agent, destination in installer.TARGETS.items():
                for name in legacy_names:
                    folder = home / destination / name
                    # Locally edited former catalog entries remain user-owned.
                    (folder / 'SKILL.md').write_text((folder / 'SKILL.md').read_text() + 'Local note.\n')
                    snapshots[(agent, name)] = installer.snapshot(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                installer.install(ROOT, home, list(installer.TARGETS), list(legacy_names.values()), False)
            for agent, destination in installer.TARGETS.items():
                for old, new in legacy_names.items():
                    self.assertEqual(installer.snapshot(home / destination / old), snapshots[(agent, old)])
                    self.assertEqual(installer.snapshot(home / destination / new), installer.snapshot(SKILLS / new))
            self.assertFalse(set(legacy_names) & set(installer.catalog(ROOT)))

    def test_long_sequence_renders_from_isolated_installed_copies(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / 'home'
            for agent in installer.TARGETS:
                with contextlib.redirect_stdout(io.StringIO()):
                    installer.install(ROOT, home, [agent], ['ct-dynamic-uml-sequence'], False)
                folder = home / installer.TARGETS[agent] / 'ct-dynamic-uml-sequence'
                output = Path(temporary) / f'{agent}-long.html'
                result = subprocess.run([sys.executable, str(folder / 'scripts/render.py'),
                    str(folder / 'assets/long-example.json'), '--expect', 'sequence', '--output', str(output)],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output.read_bytes(), (ROOT / 'examples/dynamic-umls/sequence-long.html').read_bytes())

    def test_renderer_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'keep.html'
            output.write_text('user content')
            result = subprocess.run([sys.executable, str(CANONICAL_PACKAGE / 'scripts/render.py'),
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

    def test_flowchart_rules_reject_dense_backwards_crossing_and_missing_subflows(self):
        mutations = [
            (lambda m: m['nodes'].extend(dict(m['nodes'][0], id='extra-'+str(i), x=120+i*220, y=700) for i in range(3)), 'exceeds 7'),
            (lambda m: m['nodes'][1].update(y=85), 'clearance'),
            (lambda m: m['edges'][0].update(fromPort='right'), 'orthogonal'),
            (lambda m: m['edges'][0].update(route='loop'), 'earlier node'),
            (lambda m: m['edges'][-1].update(toPort='top'), 'side ports|orthogonal'),
            (lambda m: m['edges'][-1]['via'][0].update(x=790), 'orthogonal'),
            (lambda m: m['nodes'][-1].update(subflow='missing'), 'local subflow'),
            (lambda m: m['subflows'][0]['edges'][0].update(route='loop'), 'earlier node'),
        ]
        for mutate, error in mutations:
            model = self.model('flowchart'); mutate(model)
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                renderer.validate(model)
        # An additional start-to-end connector overlaps the main path and crosses a node.
        model = self.model('flowchart')
        model['edges'].append(dict(model['edges'][0], id='shortcut', to='ready'))
        with self.assertRaisesRegex(ValueError, 'crosses node|overlapping'):
            renderer.validate(model)
        # A short inner retry rail crosses the outgoing No branch.
        model = self.model('flowchart')
        model['edges'][-1].update(fromPort='left', toPort='right', via=[
            {'x':500,'y':520}, {'x':500,'y':205}])
        with self.assertRaisesRegex(ValueError, 'outer side rail'):
            renderer.validate(model)

    def test_orthogonal_geometry_detects_crossings_overlaps_and_shared_points(self):
        layout = load(CANONICAL_PACKAGE / 'scripts/validate_flowchart.py', 'flow_geometry')
        self.assertEqual(layout.intersection(((0, 20), (80, 20)), ((40, 0), (40, 50))), (40, 20))
        self.assertEqual(layout.intersection(((0, 20), (80, 20)), ((40, 20), (100, 20))), 'overlap')
        self.assertIsNone(layout.intersection(((0, 20), (80, 20)), ((0, 40), (80, 40))))
        self.assertEqual(layout.intersection(((0, 20), (40, 20)), ((40, 20), (40, 50))), (40, 20))
        self.assertTrue(layout.touches_interior(((0, 20), (80, 20)), (30, 10, 50, 30)))
        self.assertFalse(layout.touches_interior(((0, 10), (80, 10)), (30, 10, 50, 30)))
        # Two disjoint node pairs whose connectors cross in otherwise empty space.
        m = {'nodes': [{'id':'a','x':100,'y':50,'w':40,'h':40},
                       {'id':'b','x':300,'y':350,'w':40,'h':40},
                       {'id':'c','x':300,'y':50,'w':40,'h':40},
                       {'id':'d','x':100,'y':350,'w':40,'h':40}],
             'edges': [{'id':'one','from':'a','to':'b','route':'forward','fromPort':'bottom','toPort':'top','via':[{'x':100,'y':150},{'x':300,'y':150}]},
                       {'id':'two','from':'c','to':'d','route':'forward','fromPort':'bottom','toPort':'top','via':[{'x':300,'y':250},{'x':100,'y':250}]}]}
        with self.assertRaisesRegex(ValueError, 'edges one / two: crossing'):
            layout.validate_layout(m)

    def test_flow_validator_cli_checks_json_and_embedded_html(self):
        validator = CANONICAL_PACKAGE / 'scripts/validate_flowchart.py'
        for path in [family.CANONICAL / 'assets/examples/flowchart.json', ROOT / 'examples/dynamic-umls/flowchart.html']:
            result = subprocess.run([sys.executable, str(validator), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'bad.json'
            model = self.model('flowchart'); model['subflows'][0]['nodes'][1]['y'] = 55
            path.write_text(json.dumps(model))
            result = subprocess.run([sys.executable, str(validator), str(path)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('clearance', result.stderr)

    def test_class_relationship_direction_and_activity_parallelism(self):
        classes = self.model('class')
        composition = next(e for e in classes['edges'] if e['kind'] == 'composition')
        inheritance = next(e for e in classes['edges'] if e['kind'] == 'inheritance')
        self.assertEqual((composition['from'], composition['to']), ('order', 'item'))
        self.assertEqual((inheritance['from'], inheritance['to']), ('card', 'payment'))
        parallel = self.model('activity')['scenarios'][0]['steps'][1]
        self.assertTrue({'stock', 'payment', 'fork'}.issubset(parallel['nodes']))
        self.assertTrue({'stock-start', 'payment-start'}.issubset(parallel['edges']))



if __name__ == "__main__":
    unittest.main()
