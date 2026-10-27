"""`validate-network-request-result` — is an HTTP result successful (status 2xx)?

Terminal cmdlet: it answers a yes/no question about the block produced by
``get-content-network-fetch``. The block must have the same shape the fetch
cmdlet produces — a block with ``status`` (integer), ``body`` (text), and
``headers`` (block) fields — otherwise a readable error is raised.

Returns ``true`` when ``status`` is in ``200..299`` (the same condition as
``response.ok``), and ``false`` otherwise (including ``3xx``/``4xx``/``5xx``).
"""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue

_REQUIRED_FIELDS = ('status', 'body', 'headers')


@cmdlets.register('validate-network-request-result', kind='terminal')
def validate_network_request_result(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` when the network result's ``status`` is 2xx.

    The value must be the block produced by ``get-content-network-fetch`` —
    a block with ``status`` (integer), ``body`` (text), and ``headers`` (block)
    fields. A differently-shaped value raises.
    """
    status = _require_network_result(value)
    return 200 <= status < 300


def _require_network_result(value):
    if not isinstance(value, dict):
        raise TypeError(
            'validate-network-request-result: expected the block produced by '
            f'get-content-network-fetch, got {type(value).__name__}'
        )
    missing = [field for field in _REQUIRED_FIELDS if field not in value]
    if missing:
        raise ValueError(
            'validate-network-request-result: missing field(s) '
            f'{", ".join(missing)}'
        )
    status = value['status']
    if isinstance(status, bool) or not isinstance(status, int):
        raise TypeError(
            'validate-network-request-result: status must be an integer, got '
            f'{type(status).__name__}'
        )
    return status
