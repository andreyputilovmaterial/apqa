"""Navigation path context.

A QC rule's left/right side is a chain of cmdlets. Some cmdlets *navigate*
into the piped value — ``select-field`` reads one named field, ``select-item``
picks one array element — while others transform or validate the value without
changing where it lives. The **navigation path** is the sequence of those
navigating steps, from the root value produced by the source reader down to the
value a given cmdlet is currently holding.

It is kept in a ``contextvars.ContextVar`` so that a downstream cmdlet (the
``filter`` cmdlet) can ask "where am I?" without any extra parameter threaded
through every signature, and so concurrent rule runs (the webserver is
multithreaded) never mix their paths:

* ``chain_runner.run_chain`` opens a fresh, mutable scope per chain run, so the
  left and right sides of a rule never share a path, and a nested chain (e.g.
  ``map``'s transform) gets its own scope;
* a navigating cmdlet records its canonical step (``{cmdlet, args}``) with
  :func:`record_navigation_step` before returning, so the path accumulates
  along the chain.

Each step has the same ``{cmdlet, args}`` shape a rule uses to store a cmdlet,
so a path is itself a little chain — the same uniform representation everywhere.
"""

from contextlib import contextmanager
from contextvars import ContextVar

__all__ = [
    'navigation_scope',
    'current_navigation',
    'record_navigation_step',
]

_NAVIGATION = ContextVar('apqa_navigation_path', default=None)


@contextmanager
def navigation_scope():
    """Provide a fresh, mutable navigation path for one chain run."""
    path = []
    token = _NAVIGATION.set(path)
    try:
        yield path
    finally:
        _NAVIGATION.reset(token)


def current_navigation():
    """The navigation steps applied so far in the current chain.

    A list of ``{cmdlet, args}`` mappings; empty outside a chain run.
    """
    path = _NAVIGATION.get()
    return list(path) if path is not None else []


def record_navigation_step(step):
    """Record one navigating step in the current chain's path.

    A no-op outside a chain run (i.e. when a navigating cmdlet is invoked
    directly, not through ``run_chain``).
    """
    path = _NAVIGATION.get()
    if path is not None:
        path.append(step)
