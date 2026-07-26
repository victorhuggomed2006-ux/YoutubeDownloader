"""Locating the FFmpeg used to convert and merge streams.

In the installed application FFmpeg ships alongside the executable. Running
from source, it is looked up in ``packaging/vendor/ffmpeg`` and, as a last
resort, on the system PATH.
"""

from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path

from . import paths

EXE_SUFFIX = ".exe" if os.name == "nt" else ""
FFMPEG_NAME = f"ffmpeg{EXE_SUFFIX}"
FFPROBE_NAME = f"ffprobe{EXE_SUFFIX}"

#: Environment variable that points at a specific FFmpeg build.
ENV_OVERRIDE = "YTDOWNLOADER_FFMPEG"


def _candidate_dirs() -> list[Path]:
    dirs: list[Path] = []

    override = os.getenv(ENV_OVERRIDE)
    if override:
        candidate = Path(override)
        dirs.append(candidate if candidate.is_dir() else candidate.parent)

    # Packaged: next to the executable and inside the temporary bundle.
    dirs.append(paths.install_dir() / "ffmpeg")
    dirs.append(paths.install_dir())
    dirs.append(paths.bundle_dir() / "ffmpeg")

    # Development: binaries fetched by the build script. parents[2] is the
    # project root (source-code/), which is where packaging/ lives.
    project_root = Path(__file__).resolve().parents[2]
    dirs.append(project_root / "packaging" / "vendor" / "ffmpeg")
    dirs.append(project_root / "packaging" / "vendor" / "ffmpeg" / "bin")

    return dirs


def _find(binary_name: str) -> Path | None:
    for directory in _candidate_dirs():
        candidate = directory / binary_name
        if candidate.is_file():
            return candidate

    found = shutil.which(binary_name)
    if found:
        return Path(found)
    return None


@lru_cache(maxsize=1)
def ffmpeg_path() -> Path | None:
    """Path to the FFmpeg executable, or ``None`` when not found."""
    return _find(FFMPEG_NAME)


@lru_cache(maxsize=1)
def ffprobe_path() -> Path | None:
    """Path to the FFprobe executable, or ``None`` when not found."""
    return _find(FFPROBE_NAME)


def ffmpeg_location() -> str | None:
    """Value for yt-dlp's ``ffmpeg_location`` option.

    yt-dlp takes the directory holding the binaries, which also makes
    ``ffprobe`` visible to it.
    """
    path = ffmpeg_path()
    if path is None:
        return None
    return str(path.parent)


def is_available() -> bool:
    return ffmpeg_path() is not None


def reset_cache() -> None:
    """Clear the lookup cache. Useful in tests."""
    ffmpeg_path.cache_clear()
    ffprobe_path.cache_clear()
