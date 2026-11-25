"""Resolve explicitly selected shared code and Markdown; never execute resources."""
import re
from pathlib import Path

from .common import is_link, valid_name


def safe_reference(value):
    return (isinstance(value, str) and bool(re.fullmatch(r'[a-z][a-z0-9-]*\.md', value))
            and valid_name(value[:-3]))


def shared_file(root: Path, value, filename_check):
    if not isinstance(value, str) or value.count('/') != 2 or not value.startswith('shared/'):
        raise ValueError('Expected shared/<family>/<filename> source')
    _, family, filename = value.split('/')
    if not valid_name(family) or not filename_check(filename):
        raise ValueError('Invalid shared resource source')
    path = root / 'shared'
    for part in (family, filename):
        if is_link(path) or not path.is_dir():
            raise ValueError('Shared resource ancestors must be real directories')
        path /= part
    if is_link(path) or not path.is_file():
        raise ValueError('Missing or linked shared resource')
    return path
