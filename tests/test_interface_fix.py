"""UI contract invariants with disposable source and synthetic PNGs, not browser proof."""
import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills'
NAME = 'ct-design-fix-interface'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result

workflow = module('interface_test_workflow', SKILLS / 'ct-product-manage-project/scripts/workflow.py')
interface = module('interface_test_helper', SKILLS / NAME / 'scripts/interface.py')
installer = module('interface_test_installer', ROOT / 'scripts/skills.py')
manager = module('interface_test_manager', SKILLS / 'ct-product-manage-project/scripts/manage.py')

def asset(name, file):
    return json.loads((SKILLS / name / 'assets' / file).read_text())

def png(width, height, color):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * width) * height)) + chunk(b'IEND', b'')


class InterfaceFixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.repo = self.base / 'repository'; self.repo.mkdir()
        for name in ('forms.css', 'legacy.css'):
            (self.repo / name).write_text('.ActionButton { white-space: nowrap; overflow: hidden; }\n')
        (self.repo / 'toolbar.css').write_text('.ActionButton--compact { white-space: nowrap; overflow: hidden; }\n')
        (self.repo / 'check.py').write_text('from pathlib import Path\nassert all("white-space: normal" in Path(p).read_text() for p in ("forms.css", "legacy.css")), "clipped form labels"\n')
        for argv in (['git','init','-q'], ['git','add','.'], ['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic fixture']):
            subprocess.run(argv, cwd=self.repo, check=True, capture_output=True)
        self.policy, self.intake, self.report = [asset(NAME, f) for f in ('contract.json','example-input.json','example-output.json')]
        self.argv = [sys.executable, 'check.py']
        self.intake['inputs'].update(candidate_revision=workflow.revision(self.repo), expected_behavior='Form action labels wrap without clipping; compact toolbar stays compact.',
            understanding_source='user-report', search={'roots':['.'],'terms':['ActionButton']}, reproduction_argv=self.argv)
        self.before_scan = interface.scan(self.repo, self.intake['inputs']['search'], vars(workflow))
        self.intake['inputs']['before_scan'] = self.write('before-scan.json', self.before_scan)
        self.proof('before', self.argv)
        for name in ('forms.css', 'legacy.css'):
            (self.repo / name).write_text('.ActionButton { white-space: normal; overflow: visible; }\n')
        self.report.update(status='ready', blockers=[], summary='Synthetic source and PNG contract fixture; not actual browser or acceptance evidence.')
        self.result = self.report['result']
        self.result.update(candidate_revision=workflow.revision(self.repo), expected_behavior=self.intake['inputs']['expected_behavior'],
            root_cause='Shared and duplicated fixed-line label rules clip long form labels.', before_check='before', after_check='after', related_check='related', build_check='related',
            scope_review={'routes':['profile','checkout','toolbar'], 'components':['shared form action','legacy form action','compact toolbar'],
                          'additional_searches':['Inspected consumers and compact toolbar semantics.'], 'exclusions':[], 'limitations':['Synthetic CSS fixture; no actual browser.']})
        self.report['evidence'] = [self.before_evidence]
        self.refresh()
        self.result['occurrences'] = []
        for path in ('forms.css','legacy.css','toolbar.css'):
            self.result['occurrences'].append({'id':path.split('.')[0], 'path':path, 'owner_paths':[path], 'context':'Synthetic component context.',
                'scan_matches':[{'phase':phase,'match_id':h['id']} for phase,data in (('before',self.before_scan),('after',self.final_scan)) for h in data['matches'] if h['path']==path],
                'verdict':'intentional' if path=='toolbar.css' else 'fixed', 'rationale':'Preserve a justified compact variant.' if path=='toolbar.css' else 'Apply form label invariant.',
                'question_id':None, 'evidence_ids':['inspection'], 'surface_ids':[] if path=='toolbar.css' else ['mobile','desktop']})
        for key, color in [('before',(170,50,50)),('after',(30,140,70))]:
            for viewport in self.intake['inputs']['viewports']:
                name=key+'-'+viewport['id']; path=self.base/(name+'.png');path.write_bytes(png(viewport['width'],viewport['height'],color))
                self.report['evidence'].append({'id':name,'kind':'artifact','reference':{'path':path.name,'sha256':workflow.file_digest(path)}})
        observation={'kind':'ct-observation.v1','source':'Synthetic offline fixture','observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),
                     'statement':'Synthetic contract data only; no rendered visual inspection is claimed.','limitations':'Generated PNG shapes do not prove UI correctness.'}
        self.report['evidence'].append({'id':'inspection','kind':'observation','reference':self.write('inspection.json',observation)})
        self.result['surfaces']=[{'id':'mobile' if v['id']=='reported-mobile' else 'desktop','occurrence_ids':['forms','legacy'], 'route':'Synthetic forms fixture',
            'state':'Long form action label', 'viewport_id':v['id'], 'before':'before-'+v['id'],'after':'after-'+v['id'],'inspection':'inspection','interaction_check':'after','status':'passed'} for v in self.intake['inputs']['viewports']]
        self.bind()

    def write(self, name, data):
        path=self.base/name;path.write_text(json.dumps(data));return {'path':name,'sha256':workflow.file_digest(path)}

    def proof(self, name, argv):
        path=self.base/(name+'.json')
        workflow.record(argv,self.repo,path)
        evidence={'id':name,'kind':'command','reference':{'path':path.name,'sha256':workflow.file_digest(path)}}
        if name=='before': self.before_evidence=evidence
        else:self.report['evidence'].append(evidence)

    def bind(self):self.report['input_sha256']=workflow.digest(self.intake)

    def refresh(self):
        self.intake['repository']={'path':'repository','revision':workflow.revision(self.repo),'working_tree_sha256':workflow.tree_digest(self.repo)}
        self.report['evidence']=[e for e in self.report['evidence'] if e['id'] not in ('after','related')]
        for name,argv in [('after',self.argv),('related',[sys.executable,'-c','from pathlib import Path; assert "nowrap" in Path("toolbar.css").read_text()'])]:
            path=self.base/(name+'.json')
            if path.exists():path.unlink()
            self.proof(name,argv)
        self.final_scan=interface.scan(self.repo,self.intake['inputs']['search'],vars(workflow))
        self.result['after_scan']=self.write('after-scan.json',self.final_scan)
        self.bind()

    def validate(self):return workflow.validate_output(self.policy,self.intake,self.report,self.base)

    def reject(self, message):
        with self.assertRaisesRegex(ValueError,message): self.validate()

    def pending(self):
        ledger=asset('ct-product-define-project','example-ledger.json')
        ledger['input']['project_id']=self.intake['project_id']
        ledger['events'] += [
            {'id':'add-toolbar','type':'add-decisions','decisions':[{'id':'toolbar','topic':'Whether the compact toolbar also needs multiline labels.','depends_on':[],'blocking':True,'resolution':None}]},
            {'id':'ask-toolbar','type':'ask','questions':[{'id':'Q3','decision_id':'toolbar','prompt':'Should compact toolbar actions wrap too?','options':['Preserve compact','Wrap labels'],'recommended_option':0}]}]
        self.intake['ledger']=self.write('ledger.json',ledger);self.bind();return ledger

    def test_complete_source_correction_and_preserved_variant_validate(self):self.validate()

    def test_uncertain_variant_is_held_and_blocks_completion_until_answered(self):
        ledger=self.pending();row=self.result['occurrences'][-1];row.update(verdict='uncertain',question_id='Q3')
        self.report.update(status='blocked',blockers=[{'reason':'Toolbar intent needs clarification.','next_action':'Wait for the recorded Q3 answer.'}]);self.validate()
        self.report.update(status='ready',blockers=[]);self.reject('unanswered|unanswered correction')
        ledger['events'].append({'id':'answer-toolbar','type':'answer','answers':[{'question_id':'Q3','answer':'Preserve compact toolbar; form labels wrap.','source':'Synthetic fixture answer; no actual human consent.'}]})
        self.intake['ledger']=self.write('ledger.json',ledger);row['verdict']='intentional';self.bind();self.validate()

    def test_uncertain_file_cannot_change_even_during_partial_work(self):
        self.pending();self.result['occurrences'][-1].update(verdict='uncertain',question_id='Q3')
        self.report.update(status='blocked',blockers=[{'reason':'Question pending.','next_action':'Wait.'}])
        with (self.repo/'toolbar.css').open('a') as f:f.write('/* independent looking change */\n')
        self.refresh();self.reject('uncertain correction was changed')

    def test_uncertain_consumer_holds_its_shared_owner_even_when_consumer_is_unchanged(self):
        self.pending();self.result['occurrences'][-1].update(verdict='uncertain',question_id='Q3',owner_paths=['forms.css'])
        self.report.update(status='blocked',blockers=[{'reason':'Shared owner affects an uncertain consumer.','next_action':'Wait for clarification.'}])
        self.reject('shared owners for clarification')

    def test_clear_report_needs_no_redundant_question(self):
        self.assertIsNone(self.intake['ledger']);self.validate()

    def test_unresolved_correction_cannot_claim_fixed_rows(self):
        self.intake['inputs']['understanding_source']='unresolved';self.bind()
        self.report.update(status='blocked',blockers=[{'reason':'Intent unclear.','next_action':'Ask.'}]);self.reject('cannot fix an unclear')

    def test_user_answer_must_exist_and_be_answered(self):
        self.pending();self.intake['inputs'].update(understanding_source='user-answer',understanding_question_id='Q3');self.bind()
        self.reject('actual answer')

    def test_unknown_clarification_question_is_rejected(self):
        self.pending();self.result['occurrences'][-1].update(verdict='uncertain',question_id='Q99');self.reject('unknown clarification')

    def test_repository_based_understanding_needs_source(self):
        self.intake['inputs']['understanding_source']='repository-evidence';self.bind();self.reject('needs source evidence')

    def test_report_cannot_replace_agreed_correction(self):
        self.result['expected_behavior']='Shrink all labels.';self.reject('differs from agreed')

    def test_omitted_or_duplicate_discovered_occurrences_block_ready(self):
        self.result['occurrences'].pop();self.reject('occurrence classification')

    def test_occurrence_cannot_claim_a_match_in_another_location(self):
        self.result['occurrences'][0]['path']='toolbar.css';self.reject('wrong location')

    def test_matching_before_after_regression_is_required(self):
        self.result['after_check']='related';self.reject('same command')

    def test_final_scan_tampering_is_rejected(self):
        self.final_scan['files'].pop('legacy.css');self.result['after_scan']=self.write('after-scan.json',self.final_scan)
        self.reject('malformed match|modified final scan')

    def test_baseline_scan_must_match_failing_reproduction_source(self):
        self.before_scan['repository']['working_tree_sha256']='0'*64
        self.intake['inputs']['before_scan']=self.write('before-scan.json',self.before_scan);self.bind();self.reject('baseline scan differs')

    def test_png_dimensions_and_real_file_type_are_checked(self):
        self.result['surfaces'][0]['before']='before-desktop';self.reject('dimensions differ')
        self.report['evidence'].append({'id':'text-artifact','kind':'artifact','reference':self.write('not-image.json',{'synthetic':'not a screenshot'})})
        self.result['surfaces'][0]['before']='text-artifact';self.reject('actual PNG')

    def test_visual_observation_and_passing_interaction_are_required(self):
        self.result['surfaces'][0]['inspection']='after';self.reject('visual inspection observation')
        self.result['surfaces'][0]['inspection']='inspection';self.result['surfaces'][0]['interaction_check']='before';self.reject('unexpected exit')

    def test_each_declared_viewport_and_fixed_occurrence_needs_coverage(self):
        self.result['surfaces'].pop();self.reject('missing viewport')

    def test_fixed_occurrence_cannot_borrow_another_occurrences_viewport_coverage(self):
        self.result['occurrences'][0]['surface_ids']=['mobile']
        self.reject('fixed occurrence lacks requested viewport')

    def test_manual_occurrences_must_belong_to_inspected_source_scope(self):
        row=copy.deepcopy(self.result['occurrences'][-1]);row.update(id='made-up',path='uninspected.css',scan_matches=[])
        self.result['occurrences'].append(row);self.reject('outside inspected source scope')

    def test_scan_finds_duplicates_omits_line_values_and_refuses_overwrite(self):
        script=SKILLS/NAME/'scripts/interface.py';output=self.base/'scan-cli.json'
        argv=[sys.executable,str(script),'--repository',str(self.repo),'--root','.','--term','ActionButton','--output',str(output)]
        first=subprocess.run(argv,capture_output=True,text=True);self.assertEqual(first.returncode,0,first.stderr)
        data=json.loads(output.read_text());self.assertEqual(len(data['matches']),3);self.assertNotIn('white-space',output.read_text())
        second=subprocess.run(argv,capture_output=True,text=True);self.assertNotEqual(second.returncode,0)
        self.assertEqual(data,json.loads(output.read_text()))

    def test_scan_rejects_outside_root_and_reports_skipped_source(self):
        with self.assertRaisesRegex(ValueError,'relative path'):
            interface.scan(self.repo,{'roots':['..'],'terms':['ActionButton']},vars(workflow))
        (self.repo/'large.css').write_text('x'*(1024*1024+1))
        snapshot=interface.scan(self.repo,self.intake['inputs']['search'],vars(workflow))
        self.assertEqual(snapshot['skipped'][0]['path'],'large.css')

    def test_manager_routes_directly_without_new_product_definition(self):
        state=asset('ct-product-manage-project','example-state.json');state.update(project_id=self.intake['project_id'],intent='fix-interface')
        route=manager.route(state,self.base,SKILLS);self.assertEqual(route['next_skill'],NAME)

    def test_shared_question_limits_cannot_be_reset_or_exceeded(self):
        ledger=self.pending()
        ledger['events'].append({'id':'answer-toolbar','type':'answer','answers':[{'question_id':'Q3','answer':'Preserve compact.', 'source':'Synthetic answer.'}]})
        ledger['events'].append({'id':'third-batch','type':'ask','questions':[{'id':'Q4','decision_id':'toolbar','prompt':'Another question?', 'options':[], 'recommended_option':None}]})
        self.intake['ledger']=self.write('ledger.json',ledger);self.bind();self.reject('maximum 2 batches')
        ledger['events']=[{'id':'eleven-questions','type':'ask','questions':[{'id':f'Q{i}', 'decision_id':f'decision-{i}', 'prompt':f'Question {i}?', 'options':[], 'recommended_option':None} for i in range(1,12)]}]
        ledger['input']['decisions']=[{'id':f'decision-{i}','topic':f'Question {i}', 'depends_on':[], 'blocking':True, 'resolution':None} for i in range(1,12)]
        self.intake['ledger']=self.write('ledger.json',ledger);self.bind();self.reject('maximum 10 questions')

    def test_ready_cli_from_each_agent_install_and_zip(self):
        import contextlib,io,zipfile
        with contextlib.redirect_stdout(io.StringIO()):
            installer.install(ROOT,self.base/'home',list(installer.TARGETS),[NAME],False)
            installer.build(ROOT,self.base/'packages')
        paths=[self.base/'home'/p/NAME for p in installer.TARGETS.values()]
        with zipfile.ZipFile(self.base/'packages'/(NAME+'.zip')) as z:z.extractall(self.base/'zip')
        paths.append(self.base/'zip'/NAME)
        intake=self.write('input.json',self.intake);report=self.write('output.json',self.report)
        for i,path in enumerate(paths):
            for args in (['validate-input',str(self.base/intake['path'])], ['validate-output',str(self.base/intake['path']),str(self.base/report['path'])],
                         ['render',str(self.base/intake['path']),str(self.base/report['path']),'--output',str(self.base/f'report-{i}.md')]):
                result=subprocess.run([sys.executable,str(path/'scripts/workflow.py'),*args],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
