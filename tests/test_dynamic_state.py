"""State diagram routing, label placement, and verifier CLI contracts."""
import subprocess
import sys
import unittest

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


class DynamicStateTests(DynamicUmlFixture):
    def test_state_routes_and_labels_are_validated(self):
        renderer.validate(self.model('state'))
        mutations = [
            (lambda m: m['edges'][1].update(labelAt={'x':1,'y':1}), 'labelOn'),
            (lambda m: m['edges'][1].update(labelOn={'segment':99}), 'invalid segment'),
            (lambda m: m['edges'][1].update(labelOn={'segment':0,'at':0}), 'does not fit'),
            (lambda m: m['edges'][1].update(label='A transition label that cannot fit this short arrow segment'), 'does not fit'),
            (lambda m: m['edges'][1].update(fromPort='top'), 'orthogonal'),
            (lambda m: m['nodes'][2].update(x=270), 'clearance'),
            (lambda m: m.update(orientation='diagonal'), 'orientation'),
            (lambda m: m['nodes'].append(dict(m['nodes'][0], id='extra', x=90, y=460)), 'exceeds 7'),
        ]
        for mutate, error in mutations:
            model = self.model('state'); mutate(model)
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                renderer.validate(model)
        model = self.model('state')
        model['edges'].append(dict(model['edges'][0], id='duplicate'))
        with self.assertRaisesRegex(ValueError, 'overlapping connectors'):
            renderer.validate(model)

    def test_state_outer_returns_self_transitions_vertical_views_and_details(self):
        model = self.state_loop_model(); renderer.validate(model)
        model['edges'][1]['via'] = [{'x':650,'y':130},{'x':180,'y':130}]
        with self.assertRaisesRegex(ValueError, 'outer side rail'):
            renderer.validate(model)
        model = self.state_loop_model()
        model['edges'][1].update(**{'from':'a','to':'a'},fromPort='top',toPort='bottom',
            via=[{'x':180,'y':45},{'x':50,'y':45},{'x':50,'y':270},{'x':180,'y':270}])
        renderer.validate(model)
        # Rotate the same valid horizontal graph to prove the vertical policy.
        model = self.state_loop_model();model['orientation']='vertical';model['width'],model['height']=model['height'],model['width']
        for n in model['nodes']:n['x'],n['y']=n['y'],n['x'];n['w'],n['h']=66,140
        sides={'right':'bottom','left':'top','top':'left','bottom':'right'}
        for e in model['edges']:
            e['fromPort']=sides[e['fromPort']];e['toPort']=sides[e['toPort']]
            for p in e.get('via',[]):p['x'],p['y']=p['y'],p['x']
        renderer.validate(model)
        model=self.model('state');child=self.state_loop_model();child['id']='draft-detail'
        model['nodes'][1]['subflow']='draft-detail';model['subflows']=[child]
        renderer.validate(model)
        model['nodes'][1]['subflow']='missing'
        with self.assertRaisesRegex(ValueError,'local subflow'):
            renderer.validate(model)

    def test_state_label_cannot_mask_another_transition(self):
        model = self.state_loop_model();model['edges']=model['edges'][:1]
        for name, x in [('c',320),('d',510)]:
            model['nodes'].append(dict(id=name,kind='state',label=name.upper(),detail='Illustrative alternate state.',x=x,y=300,w=100))
        model['edges'].append(dict(id='alternate',kind='transition',label='go',detail='Alternate transition.',
            **{'from':'c','to':'d'},fromPort='top',toPort='top',route='forward',
            via=[{'x':320,'y':188},{'x':510,'y':188}],labelOn={'segment':0}))
        model['scenarios'][0]['steps'][0]['edges']=['start']
        with self.assertRaisesRegex(ValueError,'label covers another transition'):
            renderer.validate(model)

    def test_state_verifier_cli_accepts_json_and_html(self):
        validator=CANONICAL_PACKAGE / 'scripts/validate_state.py'
        for path in [family.CANONICAL / 'assets/examples/state.json', ROOT / 'examples/dynamic-umls/state.html']:
            result=subprocess.run([sys.executable,str(validator),str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)



if __name__ == "__main__":
    unittest.main()
