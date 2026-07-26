"""Application logging setup."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from . import paths

LOG_FORMAT = "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 1 * 1024 * 1024
BACKUP_COUNT = 2


def configure(level: int = logging.INFO) -> None:
    """Install the file and console handlers, once."""
    root = logging.getLogger()
    if getattr(root, "_ytdownloader_configured", False):
        return

    root.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    try:
        file_handler = RotatingFileHandler(
            paths.log_file(), maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        pass  # no write permission: carry on with the console alone

    # A windowed executable has no console; this avoids a null-stream error.
    if sys.stderr is not None:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    root._ytdownloader_configured = True  # type: ignore[attr-defined]
