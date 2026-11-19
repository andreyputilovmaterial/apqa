"""`get-filesystem-obj-info` — stat a filesystem object into a small block.

Source reader: the piped value is ignored and the path is read from ``args``.

Args (stored named mapping):
    path    required; full path to the filesystem object.

The result is a block describing the object at ``path``:

    type       text — ``"file"``, ``"directory"``, or ``"other"``
    size       integer — the object size in bytes (``st_size``)
    mtime      timezone-aware date/time (UTC) — content modification time
               (``st_mtime``)
    ctime      timezone-aware date/time (UTC) — ``st_ctime``
    birthtime  timezone-aware date/time (UTC) or sysmissing — ``st_birthtime``
               when the platform exposes it, otherwise ``None``

``mtime`` / ``ctime`` / ``birthtime`` map one-to-one onto Python's
``os.stat_result`` fields and are deliberately not glossed: depending on the
platform, ``st_ctime`` means "metadata-change time" or "creation time", and
``st_birthtime`` is the creation time only where it exists. A rule reads the
field whose Python meaning it wants rather than a relabelled
"created"/"changed" field.

If ``path`` does not exist (there is no object — file or directory — at that
location) the cmdlet returns ``sysmissing`` (``None``). Reading uses only the
Python standard library (``os.stat`` / ``stat`` / ``datetime``), so there is no
pip-installable dependency.
"""

import stat
from datetime import datetime, timezone
from pathlib import Path

from ..registry import cmdlets
from ..value_types import Block, PipeValue, from_plain, sysmissing


def _to_utc(timestamp):
    """Return ``timestamp`` (seconds since the epoch) as an aware UTC datetime."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


@cmdlets.register(
    'get-filesystem-obj-info',
    kind='source',
    help='Stat a filesystem object into a block of type, size and timestamps.',
    args=[
        {
            'name': 'path',
            'type': 'path',
            'required': True,
            'description': 'Full path to the filesystem object.',
        },
    ],
    permissions=['filesystem'],
    compact=[
        {'text': '[file]', 'role': 'logo'},
        {'arg': 'path'},
    ],
)
def get_filesystem_obj_info(value: PipeValue, args: dict) -> PipeValue:
    path = args.get('path')
    if not path:
        raise ValueError("get-filesystem-obj-info: missing required arg 'path'")

    resolved = Path(path).expanduser().resolve()
    try:
        info = resolved.stat()
    except FileNotFoundError:
        return sysmissing

    mode = info.st_mode
    if stat.S_ISREG(mode):
        obj_type = 'file'
    elif stat.S_ISDIR(mode):
        obj_type = 'directory'
    else:
        obj_type = 'other'

    birthtime_value = getattr(info, 'st_birthtime', None)
    return from_plain(Block({
        'type': obj_type,
        'size': info.st_size,
        'mtime': _to_utc(info.st_mtime),
        'ctime': _to_utc(info.st_ctime),
        'birthtime': (
            _to_utc(birthtime_value) if birthtime_value is not None else sysmissing
        ),
    }))
