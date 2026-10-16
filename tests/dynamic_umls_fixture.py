"""Test-free dynamic umls fixtures shared by contract suites."""
import importlib.util
import json
import sys
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
from assembled_catalog import SKILLS
CANONICAL_PACKAGE = SKILLS / 'ct-dynamic-uml'
renderer = load(CANONICAL_PACKAGE / 'scripts/render.py', 'dynamic_render')
installer = load(ROOT / 'scripts/skills.py', 'dynamic_install')


class DynamicUmlFixture(unittest.TestCase):
    def model(self, kind='sequence'):
        return json.loads((family.CANONICAL / f'assets/examples/{kind}.json').read_text(encoding='utf-8'))

    def state_loop_model(self):
        model = self.model('state')
        model.update(width=900, height=420, nodes=[
            dict(id='a',kind='state',label='Waiting',detail='An illustrative stable state.',x=180,y=180,w=140),
            dict(id='b',kind='state',label='Working',detail='Another illustrative stable state.',x=650,y=180,w=140)],
            edges=[dict(id='start',kind='transition',label='start',detail='Begin work.',**{'from':'a','to':'b'},
                fromPort='right',toPort='left',route='forward',labelOn={'segment':0}),
                dict(id='retry',kind='transition',label='retry',detail='Return to Waiting.',**{'from':'b','to':'a'},
                fromPort='top',toPort='top',route='loop',via=[{'x':650,'y':60},{'x':180,'y':60}],labelOn={'segment':1})],
            scenarios=[dict(id='retry',label='Retry',steps=[dict(title='Retry the work',body='Return on an outer rail.',nodes=['a','b'],edges=['retry'])])])
        return model
