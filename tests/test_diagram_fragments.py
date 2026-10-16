"""Fragment composition preserves standalone diagram rendering and useful errors."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from assembled_catalog import SKILLS

PACKAGE = SKILLS / 'ct-dynamic-uml'
ASSETS = PACKAGE / 'assets'
FRAGMENTS = ('styles.css', 'diagram.js', 'controls.js')
spec = importlib.util.spec_from_file_location('fragment_renderer', PACKAGE / 'scripts/render.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class DiagramFragmentTests(unittest.TestCase):
    def model(self):
        return json.loads((ASSETS / 'examples/sequence.json').read_text(encoding='utf-8'))

    def template_copy(self, folder):
        for name in ('template.html', *FRAGMENTS):
            (folder / name).write_bytes((ASSETS / name).read_bytes())
        return folder / 'template.html'

    def test_fragments_are_inlined_without_changing_standalone_bytes(self):
        shell = (ASSETS / 'template.html').read_text(encoding='utf-8')
        for marker, name in zip(('STYLES', 'RENDERER', 'CONTROLS'), FRAGMENTS):
            shell = shell.replace(f'__DIAGRAM_{marker}__\n', (ASSETS / name).read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as temporary:
            complete = Path(temporary) / 'complete.html'
            complete.write_text(shell, encoding='utf-8')
            self.assertEqual(renderer.render(self.model()), renderer.render(self.model(), template=complete))

    def test_missing_fragment_fails_instead_of_emitting_broken_html(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            template = self.template_copy(folder)
            (folder / 'controls.js').unlink()
            with self.assertRaisesRegex(FileNotFoundError, 'controls.js'):
                renderer.render(self.model(), template=template)

    def test_fragment_marker_names_in_model_text_remain_literal_data(self):
        model = self.model()
        model['title'] = '__DIAGRAM_STYLES__ __DIAGRAM_RENDERER__ __DIAGRAM_CONTROLS__'
        page = renderer.render(model)
        self.assertIn(f"<title>{model['title']}</title>", page)
        self.assertIn(f'"title":"{model["title"]}"', page)

    def test_fragment_boundaries_must_preserve_line_breaks(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            template = self.template_copy(folder)
            controls = folder / 'controls.js'
            controls.write_text(controls.read_text(encoding='utf-8').rstrip('\n'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'controls.js must end with a newline'):
                renderer.render(self.model(), template=template)
            self.template_copy(folder)
            template.write_text(template.read_text(encoding='utf-8').replace(
                '__DIAGRAM_STYLES__\n', '__DIAGRAM_STYLES__'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'placeholder on its own line'):
                renderer.render(self.model(), template=template)


if __name__ == '__main__':
    unittest.main()
