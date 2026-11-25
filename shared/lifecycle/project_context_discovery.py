"""Read one optional project profile without searching outside the selected root."""
from pathlib import Path
import stat


class DiscoveryError(ValueError):
    """Fixed safe diagnostics, never interpolated profile contents."""


def linked(info):
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT))


def discover(root, profile, load_profile, validate_profile):
    root = Path(root)
    if not root.is_dir():
        raise DiscoveryError('Selected project root is unavailable')
    root = root.resolve()
    explicit = profile is not None
    if explicit:
        selected = Path(profile).expanduser()
        if not selected.is_absolute():
            selected = root / selected
    else:
        parent = root / 'context-templates'
        try:
            info = parent.lstat()
        except FileNotFoundError:
            info = None
        if info is not None:
            if linked(info):
                raise DiscoveryError('Linked project context directory is not allowed')
            if not stat.S_ISDIR(info.st_mode):
                raise DiscoveryError('Project context parent is not a directory')
        selected = parent / 'project.json'
    try:
        info = selected.lstat()
    except FileNotFoundError:
        if explicit:
            raise DiscoveryError('Explicit project profile is unavailable')
        return {'status': 'absent', 'project_root': str(root), 'profile_path': str(selected)}
    if linked(info):
        raise DiscoveryError('Linked project profile is not allowed')
    value = load_profile(selected)
    pending = validate_profile(value)
    return {'status': 'present', 'project_root': str(root), 'profile_path': str(selected.resolve()),
            'selection': 'explicit' if explicit else 'repository', 'undecided': pending,
            'provider_access_verified': False, 'profile': value}
