"""Diagnostic notes: the out-of-band channel a QC run uses to report *where*
a validation or comparison failed.

A QC rule run has two kinds of bad outcome (see ``docs/qc-results-reporting.md``):

* an **error** — a cmdlet cannot do its work (missing field, unreadable file,
  unknown cmdlet) and raises; the runner adds chain-step context via
  ``ChainError`` and the original exception stays attached as ``__cause__``;
* a **validation failure** — the rule *runs* but compares to ``False``; there is
  no exception to carry the "why", so the cmdlets that know *where* the value
  failed (validators, and in the future comparisons) record a **note** here.

A note is a small JSON-safe mapping::

    {'path': ['Fields', 'BrandAwareness', 'Label'], 'message': '…'}

``path`` is the **data path** — the sequence of block keys and array indices that
leads from the top-level piped value to the offending leaf. It is the "which
component, which field, during which iteration" answer. Notes are collected per
rule run in a :class:`Notes` instance stored in a ``contextvars.ContextVar``, so
a cmdlet records notes by calling :func:`record_note` without threading any extra
parameter through its signature, and concurrent rule runs (the webserver is
multithreaded) never mix their notes.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import re

__all__ = [
    'Notes',
    'current_notes',
    'record_note',
    'collect_notes',
    'note_path_prefix',
    'format_path',
    'format_note',
    'format_notes',
]

_NOTES = ContextVar('apqa_notes', default=None)

_PATH_PREFIX = ContextVar('apqa_notes_path_prefix', default=None)

_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _prefixed(path):
    """Return ``path`` with the active path prefix prepended (if any)."""
    path = list(path)
    prefix = _PATH_PREFIX.get()
    if prefix:
        return prefix + path
    return path


class Notes:
    """A mutable list of diagnostic notes collected during one rule run."""

    def __init__(self):
        self.items = []

    def note(self, path, message):
        self.items.append({'path': _prefixed(path), 'message': f'{message}'})


def current_notes():
    """Return the :class:`Notes` for the current run, or ``None`` outside a run."""
    return _NOTES.get()


def record_note(path, message):
    """Append a note to the current run's notes, if one is active.

    Called by cmdlets while they walk a value; a no-op when the cmdlet is
    executed directly (outside :func:`collect_notes`).
    """
    notes = _NOTES.get()
    if notes is not None:
        notes.note(path, message)


@contextmanager
def collect_notes():
    """Provide a fresh :class:`Notes` for the current run context.

    Yields the ``Notes`` instance; the previous context is restored on exit, so
    nested and threaded runs stay isolated.
    """
    notes = Notes()
    token = _NOTES.set(notes)
    try:
        yield notes
    finally:
        _NOTES.reset(token)


@contextmanager
def note_path_prefix(prefix):
    """Run the block with ``prefix`` prepended to every recorded note path.

    ``prefix`` is a list of path segments (block keys / array indices) leading to
    the value being processed. Nested prefixes accumulate, so a validator running
    inside ``foreach-deep-node`` records the full data path even though it starts
    its own walk at ``[]``.
    """
    if not prefix:
        yield
        return
    prefix = list(prefix)
    current = _PATH_PREFIX.get()
    combined = current + prefix if current else prefix
    token = _PATH_PREFIX.set(combined)
    try:
        yield
    finally:
        _PATH_PREFIX.reset(token)


def format_path(path):
    """Render a data path as a short, human-readable address.

    ``['Fields', 'BrandAwareness', 'Label']`` becomes
    ``Fields.BrandAwareness.Label``; collection indices become ``[i]``; a key
    that is not a plain identifier is quoted, e.g.
    ``Fields.Gender.Elements['None of the above'].Label``.
    """
    result = ''
    for part in path:
        if isinstance(part, int):
            result += f'[{part}]'
            continue
        text = f'{part}'
        if _IDENTIFIER.match(text):
            if result:
                result += '.'
            result += text
        else:
            result += f'[{text!r}]'
    return result


def format_note(note):
    """Render one note as ``<path>: <message>`` (or just the message)."""
    path = format_path(note.get('path', []))
    message = note.get('message', '')
    if path:
        return f'{path}: {message}'
    return f'{message}'


def format_notes(notes):
    """Render a list of notes as a bulleted, newline-separated block."""
    return '\n'.join(f'- {format_note(note)}' for note in notes)
