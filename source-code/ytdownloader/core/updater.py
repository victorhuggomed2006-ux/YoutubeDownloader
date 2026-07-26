"""Updating yt-dlp without reinstalling the application.

Sites change how they serve video often, so a copy of yt-dlp frozen inside the
executable stops working after a while. To avoid that, the app downloads the
official package from PyPI (a .whl file, which is just a ZIP), extracts it into
the user's folder and puts that folder first on ``sys.path``. No Python
installation and no pip required.

``activate()`` must be called before the first ``import yt_dlp``.

This is the only component that runs code fetched at runtime, which is why the
checks below are not optional: the SHA-256 digest published by PyPI, refusal of
archive members whose path escapes the destination, a size ceiling, and refusal
of any package that does not actually contain yt-dlp.
"""

from __future__ import annotations

import hashlib
import io
import logging
import re
import shutil
import sys
import zipfile
from pathlib import Path

from . import paths

logger = logging.getLogger(__name__)

PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
PACKAGE_PREFIX = "yt_dlp-"
DOWNLOAD_TIMEOUT = 60
MAX_WHEEL_BYTES = 60 * 1024 * 1024

_VERSION_RE = re.compile(r"^\d+(\.\d+)*$")


def parse_version(text: str) -> tuple[int, ...]:
    """Turn ``"2026.7.4"`` into ``(2026, 7, 4)`` for comparison.

    Comparing as text would place "2026.10.1" before "2026.9.1".
    """
    parts: list[int] = []
    for chunk in str(text or "").split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def _installed_dirs() -> list[tuple[tuple[int, ...], Path]]:
    root = paths.runtime_dir()
    found: list[tuple[tuple[int, ...], Path]] = []
    for entry in root.iterdir() if root.is_dir() else []:
        if not entry.is_dir() or not entry.name.startswith(PACKAGE_PREFIX):
            continue
        # An interrupted install leaves a half-written folder behind; it must
        # not be picked over the bundled copy, which works.
        if not (entry / "yt_dlp" / "__init__.py").is_file():
            continue
        found.append((parse_version(entry.name[len(PACKAGE_PREFIX) :]), entry))
    found.sort(key=lambda item: item[0])
    return found


def activate() -> str | None:
    """Put the newest downloaded yt-dlp first on ``sys.path``.

    Returns the activated version, or ``None`` when the bundled one is used.
    """
    if "yt_dlp" in sys.modules:
        # Changing sys.path after the import would have no effect and would
        # falsely suggest the update is in use.
        logger.debug("yt-dlp already imported; keeping the bundled version.")
        return None

    installed = _installed_dirs()
    if not installed:
        return None

    version, directory = installed[-1]
    if str(directory) in sys.path:
        return ".".join(str(p) for p in version)

    sys.path.insert(0, str(directory))
    logger.info("Using yt-dlp %s from %s", ".".join(str(p) for p in version), directory)
    return ".".join(str(p) for p in version)


def current_version() -> str:
    """The yt-dlp version actually loaded."""
    try:
        from yt_dlp.version import __version__

        return str(__version__)
    except Exception:
        return "unknown"


def latest_version() -> tuple[str, str, str] | None:
    """Ask PyPI and return ``(version, wheel_url, sha256)``."""
    try:
        import requests

        response = requests.get(PYPI_URL, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.warning("Could not reach PyPI: %s", exc)
        return None

    version = str((data.get("info") or {}).get("version") or "")
    if not _VERSION_RE.match(version):
        return None

    for item in data.get("urls") or []:
        filename = str(item.get("filename") or "")
        if item.get("packagetype") == "bdist_wheel" and filename.endswith("py3-none-any.whl"):
            url = str(item.get("url") or "")
            digest = str((item.get("digests") or {}).get("sha256") or "")
            if url:
                return version, url, digest

    return None


def update_available() -> str | None:
    """The newer version available, or ``None`` when already up to date."""
    latest = latest_version()
    if latest is None:
        return None
    version = latest[0]
    if parse_version(version) > parse_version(current_version()):
        return version
    return None


def install(version: str, url: str, sha256: str = "") -> Path:
    """Download and extract the yt-dlp wheel into the user's data folder."""
    import requests

    response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
    response.raise_for_status()

    buffer = io.BytesIO()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        buffer.write(chunk)
        # A compromised server must not be able to fill the user's disk.
        if buffer.tell() > MAX_WHEEL_BYTES:
            raise RuntimeError("The downloaded package is larger than expected.")

    payload = buffer.getvalue()
    if sha256:
        actual = hashlib.sha256(payload).hexdigest()
        if actual != sha256:
            raise RuntimeError("The package failed its integrity check.")

    target = paths.runtime_dir() / f"{PACKAGE_PREFIX}{version}"
    staging = target.with_name(target.name + ".tmp")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for member in archive.namelist():
            # Zip Slip: a member with ".." in its path would overwrite files
            # outside the destination, including the application itself.
            destination = (staging / member).resolve()
            if not str(destination).startswith(str(staging.resolve())):
                raise RuntimeError("The package contains invalid paths.")
        archive.extractall(staging)

    if not (staging / "yt_dlp" / "__init__.py").is_file():
        shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError("The downloaded package does not contain yt-dlp.")

    shutil.rmtree(target, ignore_errors=True)
    staging.replace(target)
    _prune_old(keep=target)
    logger.info("yt-dlp %s installed at %s", version, target)
    return target


def update_now() -> str | None:
    """Download the newest version if there is one. Returns what was installed."""
    latest = latest_version()
    if latest is None:
        return None

    version, url, digest = latest
    if parse_version(version) <= parse_version(current_version()):
        return None

    install(version, url, digest)
    return version


def _prune_old(keep: Path, max_kept: int = 1) -> None:
    """Remove older copies so they do not pile up on disk."""
    installed = [d for _, d in _installed_dirs() if d != keep]
    for directory in installed[: max(0, len(installed) - max_kept + 1)]:
        if str(directory) in sys.path:
            continue  # in use in this session
        shutil.rmtree(directory, ignore_errors=True)
