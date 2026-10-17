"""Disposable handoff artifacts; never inspect a developer's real agent home."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from assembled_catalog import ROOT, SKILLS, installer

NAME = 'ct-rnd-prepare-next-session'
SKILL = SKILLS / NAME
spec = importlib.util.spec_from_file_location('test_session_handoff', SKILL / 'scripts/handoff.py')
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)
checks = handoff.checks


class HandoffFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ct-handoff-proof-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        for name in ('example-input.json', 'example-output.json', 'example-source.md'):
            (self.base / name).write_bytes((SKILL / 'assets' / name).read_bytes())
        self.intake = checks.load(self.base / 'example-input.json')
        self.output = checks.load(self.base / 'example-output.json')

    def bind(self):
        self.output['input_sha256'] = checks.digest(self.intake)

    def validate(self):
        return checks.validate_output(self.intake, self.output, self.base)

    def save(self):
        for name, value in [('input.json', self.intake), ('output.json', self.output)]:
            (self.base / name).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def cli(self, *args, script=None, cwd=None):
        return subprocess.run([sys.executable, '-I', '-B', str(script or SKILL / 'scripts/handoff.py'),
                               *map(str, args)], cwd=cwd or self.base, capture_output=True, text=True)
