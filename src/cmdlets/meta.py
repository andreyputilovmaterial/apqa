"""Editor metadata for cmdlets and comparison ops.

The rule form needs to know, for every registered cmdlet, its name, its ``kind``
(whether it can be first in a chain), the args it accepts (with a type, required
flag, default and description), and a short help text — plus the same for the
comparison ops and their ``op_args``. The registries already collect that
metadata next to each cmdlet/op; this module just snapshots it into a single
JSON-serializable structure for the ``/functionality/cmdlet-metadata`` endpoint.
"""

from . import cmdlets, comparisons


def get_cmdlet_metadata():
    """Return ``{'cmdlets': [...], 'ops': [...]}`` for the rule editor."""
    return {
        'cmdlets': cmdlets.metadata(),
        'ops': comparisons.metadata(),
    }
