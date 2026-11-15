"""Application logging setup.

All program output goes through the single ``apqa`` logger:

* informative progress messages are logged at INFO and written to stdout;
* warnings and errors are written to stderr.

Entry points call :func:`setup_logging` once at the start of their ``main()``.
Messages use a bare ``%(message)s`` formatter — the messages already carry their
own color codes and prefixes, so no level/logger preamble is added.
"""

import logging
import sys


LOGGER_NAME = "apqa"


class _DynamicStreamHandler(logging.StreamHandler):
    """A handler that resolves its stream at emit time (like ``print``).

    Binding ``sys.stdout`` / ``sys.stderr`` at configuration time would miss
    pytest's output capture and any later redirection. Resolving per emit keeps
    logger output following the *current* stream.
    """

    def __init__(self, stream_getter):
        super().__init__()
        self._stream_getter = stream_getter

    def emit(self, record):
        try:
            stream = self._stream_getter()
            stream.write(self.format(record) + self.terminator)
            stream.flush()
        except Exception:
            self.handleError(record)


def setup_logging():
    """Configure the ``apqa`` logger and return it (idempotent)."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    stdout_handler = _DynamicStreamHandler(lambda: sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(lambda record: record.levelno < logging.WARNING)
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stdout_handler)

    stderr_handler = _DynamicStreamHandler(lambda: sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stderr_handler)

    return logger
