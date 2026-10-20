"""Class camera compatibility, complete decomposition and untrusted-data safety."""
import copy
import json
import unittest

from dynamic_umls_fixture import DynamicUmlFixture, renderer


class ClassCameraTests(DynamicUmlFixture):
    def test_class_default_uses_packaged_camera_and_keeps_source_json(self):
        model = self.model('class')
        page = renderer.render(model)
        self.assertIn('id="stage"', page)
        self.assertIn('Resume tour', page)
        self.assertNotIn('__ADAPTER__', page)
        data = page.split('<script id="diagram-data" type="application/json">')[1].split('</script>')[0]
        self.assertEqual(json.loads(data), model)

    def test_linked_views_retain_every_class_and_relationship(self):
        model = self.model('class')
        self.assertEqual(len(model['nodes']), 48)
        self.assertEqual(sum('order' in (e['from'], e['to']) for e in model['edges']), 27)
        renderer.validate(model)
        for mutate, message in [
            (lambda m: m.pop('views'), 'above 20'),
            (lambda m: m['views'].pop(), 'remain represented'),
            (lambda m: m['views'][0]['nodes'].remove('order'), 'endpoints'),
            (lambda m: m['views'][0]['edges'].append('unknown'), 'identifier'),
            (lambda m: m['views'][1].update(id=m['views'][0]['id']), 'duplicate id'),
            (lambda m: m['scenarios'][0]['steps'][0].update(focus='unknown'), 'focus'),
            (lambda m: m['scenarios'][0]['steps'][0].update(view='unknown'), 'incompatible'),
        ]:
            candidate = copy.deepcopy(model)
            mutate(candidate)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                renderer.validate(candidate)

    def test_legacy_single_view_and_all_relation_kinds_remain_valid(self):
        model = self.model('class')
        model.pop('views')
        model['nodes'] = model['nodes'][:2]
        model['edges'] = [dict(model['edges'][0], id=kind, kind=kind)
                          for kind in ['association', 'composition', 'aggregation', 'inheritance', 'dependency']]
        model['scenarios'] = [{'id': 'one', 'label': 'First explanation', 'steps': [{
            'title': 'A single view', 'body': 'Legacy fields still work.',
            'nodes': [n['id'] for n in model['nodes']], 'edges': [e['id'] for e in model['edges']]}]}]
        page = renderer.render(model)
        self.assertIn('id="stage"', page)
        self.assertEqual(len(model['nodes']), 2)

    def test_class_strings_and_template_markers_remain_data(self):
        model = self.model('class')
        attack = '</script><img src=x onerror=alert(1)>'
        model['title'] = '__LOGO__ ' + attack
        model['nodes'][0]['fields'].append(attack)
        page = renderer.render(model)
        data = page.split('<script id="diagram-data" type="application/json">')[1].split('</script>')[0]
        self.assertNotIn('<', data)
        self.assertEqual(json.loads(data), model)
        self.assertIn('&lt;/script&gt;', page)
        self.assertNotIn('<img src=x', page)


if __name__ == '__main__':
    unittest.main()
