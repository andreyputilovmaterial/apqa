"""Webserver port configuration for the UI entry point.

The desktop app's backend listens on ``localhost``. The port is chosen with the
``--config-webserver-port`` CLI flag:

* ``<port>``  — a fixed port: start there and fail if it is occupied.
* ``<port>+`` — start at ``<port>`` and auto-increment by one until a free port
  is found.
* (omitted)   — the default: auto-increment starting at 5280 (same as ``5280+``).

NOTE for developers: the Vite frontend dev server has port 5280 pre-configured
and hard-coded (``src/frontend/app_js/vite.config.js`` proxies every API call to
``http://localhost:5280``), so while developing against Vite the backend must
land on 5280. Without the dev frontend server (i.e. the normal backend-served
bundle) any port works equally well.
"""

import os
import socket

from .webserver_engine.webserve.src.find_free_port import find_free_port


DEFAULT_PORT = 5280


def parse_webserver_port(value):
    """Parse a ``--config-webserver-port`` value into ``(port, auto_increment)``.

    ``None`` means the default (auto-increment from 5280). A trailing ``+``
    requests auto-increment; otherwise the port is fixed (fail if occupied).
    """
    if value is None:
        return DEFAULT_PORT, True
    text = str(value).strip()
    auto_increment = text.endswith('+')
    if auto_increment:
        text = text[:-1].strip()
    try:
        port = int(text)
    except ValueError:
        raise ValueError(
            f'--config-webserver-port must be a port number, optionally followed '
            f'by "+" to auto-increment (got {value!r})'
        ) from None
    if not (1 <= port <= 65535):
        raise ValueError(
            f'--config-webserver-port out of range 1..65535: {port}'
        )
    return port, auto_increment


def _port_is_free(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if os.name != "nt":
            # The real listener (HTTPServer) sets SO_REUSEADDR; mirror that here
            # so a port held only by a TIME_WAIT socket from a just-stopped
            # server is not reported as "already in use". Skipped on Windows,
            # where SO_REUSEADDR has different (permissive) semantics that would
            # weaken the fixed-port "fail if occupied" guarantee.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def select_webserver_port(host, value):
    """Pick the listen port for ``host`` according to the flag value.

    See the module docstring for the three behaviours.
    """
    port, auto_increment = parse_webserver_port(value)
    if auto_increment:
        return find_free_port(host, start=port)
    if not _port_is_free(host, port):
        raise RuntimeError(f'port {port} is already in use')
    return port
