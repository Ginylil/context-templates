"""Physical source-line limits for maintained code and delivered package code."""
from pathlib import Path
import subprocess

MAX_CODE_LINES = 300
CODE_SUFFIXES = frozenset({
    '.py', '.pyw', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.mts', '.cts',
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte', '.astro',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1', '.sql', '.rb', '.go', '.rs',
    '.java', '.kt', '.swift', '.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.cs',
    '.php', '.dart',
})
BUILD_FILES = frozenset({'Makefile', 'GNUmakefile', 'CMakeLists.txt'})
# These generated deliverables stay single-file/offline; their maintained inputs
# and every code file inside a skill package are still checked without exemption.
GENERATED_HTML = frozenset(
    f'examples/dynamic-umls/{name}.html' for name in (
        'sequence', 'class', 'flowchart', 'state', 'activity', 'component',
        'sequence-long', 'index',
    )
)


def is_code_file(name):
    path = Path(name)
    return path.suffix.lower() in CODE_SUFFIXES or path.name in BUILD_FILES


def code_length(data):
    """Count physical lines, including blank/comment lines and a final partial line."""
    return len(data.splitlines())


def check_code_length(data, name):
    if is_code_file(name):
        lines = code_length(data)
        if lines > MAX_CODE_LINES:
            raise ValueError(f'{name}: {lines} lines exceeds {MAX_CODE_LINES}; split by responsibility')


def repository_violations(root):
    """Include tracked and nonignored new code; omit only named generated HTML."""
    names = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
        cwd=root, encoding='utf-8', errors='surrogateescape',
    ).split('\0')
    violations = []
    for name in sorted(set(names)):
        if not name or name in GENERATED_HTML or not is_code_file(name):
            continue
        path = root / name
        if path.is_symlink():
            raise ValueError(f'{name}: cannot check linked source')
        if path.is_file():
            try:
                check_code_length(path.read_bytes(), name)
            except ValueError as error:
                violations.append(str(error))
    return violations
