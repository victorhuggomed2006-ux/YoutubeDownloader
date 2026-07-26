"""Discovery of the directories the application uses.

Works both when running from source and inside the PyInstaller executable,
where resources live under ``sys._MEIPASS``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "YouTubeDownloader"


def is_frozen() -> bool:
    """True when the code is running inside the packaged executable."""
    return getattr(sys, "frozen", False)


def bundle_dir() -> Path:
    """Where the bundled resources live.

    In the executable this is the temporary extraction folder
    (``sys._MEIPASS``); from source it is the root of the ``ytdownloader``
    package.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def install_dir() -> Path:
    """The folder the application is installed in (where the .exe lives).

    Running from source there is no install folder, so the project root stands
    in for it — that is where the development binaries sit.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    """Path to a file inside ``ytdownloader/resources``."""
    return bundle_dir().joinpath("resources", *parts)


def app_data_dir() -> Path:
    """The user's data folder: settings, history and logs."""
    base = os.getenv("APPDATA")
    if base:
        path = Path(base) / APP_DIR_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    else:
        xdg = os.getenv("XDG_CONFIG_HOME")
        root = Path(xdg) if xdg else Path.home() / ".config"
        path = root / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_dir() -> Path:
    """Where updated yt-dlp versions are installed."""
    path = app_data_dir() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_download_dir() -> Path:
    """The default destination for downloads.

    Windows localises the Downloads folder, so the common translations are
    checked before falling back to the home directory.
    """
    candidates = [
        Path.home() / "Downloads",
        Path.home() / "Transferências",  # pt-BR
        Path.home() / "Descargas",  # es
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate / "YouTube Downloader"
    return Path.home() / "YouTube Downloader"


def settings_file() -> Path:
    return app_data_dir() / "settings.json"


def history_file() -> Path:
    return app_data_dir() / "history.json"


def log_file() -> Path:
    return app_data_dir() / "ytdownloader.log"
