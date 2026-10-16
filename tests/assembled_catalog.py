"""One disposable assembled catalog for runtime tests; never use real agent homes."""
import atexit
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('ct_test_assembler', ROOT / 'scripts/skills.py')
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)
_temporary = tempfile.TemporaryDirectory(prefix='ct-runtime-tests-')
atexit.register(_temporary.cleanup)
SKILLS = Path(_temporary.name) / 'skills'
with contextlib.redirect_stdout(io.StringIO()):
    installer.assemble(ROOT, SKILLS, [])
