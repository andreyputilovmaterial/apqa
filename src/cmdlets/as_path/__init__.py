"""`as-path` — convert a value to a filesystem path."""

from pathlib import Path

from ..registry import cmdlets
from ..value_types import PathValue, PipeValue


@cmdlets.register('as-path', kind='processor')
def as_path(value: PipeValue, args: dict) -> PathValue:
    """Convert ``value`` to a path via ``pathlib.Path()``; errors propagate."""
    return Path(value)
