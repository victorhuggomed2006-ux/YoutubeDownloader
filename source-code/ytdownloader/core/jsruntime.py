"""Detection of the JavaScript runtimes yt-dlp can use.

Since 2026 yt-dlp relies on a JavaScript interpreter to resolve part of
YouTube's formats. By default it only looks for Deno; here Node and Bun are
accepted too, since they are far more common on users' machines.

With no runtime at all downloads still work, but some videos offer fewer
quality options.
"""

from __future__ import annotations

import logging
import shutil
from functools import lru_cache

from . import paths

logger = logging.getLogger(__name__)

#: Preference order. Deno is the officially supported runtime.
SUPPORTED_RUNTIMES = ("deno", "node", "bun")


@lru_cache(maxsize=1)
def detect() -> dict[str, dict]:
    """Build the value for yt-dlp's ``js_runtimes`` option.

    Looks next to the executable first — in case a runtime is ever shipped
    alongside the app — and then on the system PATH.
    """
    found: dict[str, dict] = {}

    for name in SUPPORTED_RUNTIMES:
        executable = f"{name}.exe"
        bundled = paths.install_dir() / executable
        if bundled.is_file():
            found[name] = {"path": str(bundled)}
            continue

        system = shutil.which(name)
        if system:
            found[name] = {"path": system}

    if found:
        logger.info("JavaScript runtimes available: %s", ", ".join(found))
    else:
        logger.info("No JavaScript runtime found; some videos may offer fewer quality options.")
    return found


def is_available() -> bool:
    return bool(detect())


def names() -> tuple[str, ...]:
    return tuple(detect())


def reset_cache() -> None:
    """Clear the detection cache. Useful in tests."""
    detect.cache_clear()
