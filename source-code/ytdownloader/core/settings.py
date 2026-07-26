"""Application settings, stored as JSON in the user's data folder."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from . import paths
from .formats import (
    DEFAULT_AUDIO_CONTAINER,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_VIDEO_CONTAINER,
    DEFAULT_VIDEO_QUALITY,
)

logger = logging.getLogger(__name__)

#: Browsers cookies can be imported from, which clears the "confirm you are
#: not a bot" prompts. "none" disables the feature, and is the default.
COOKIE_BROWSERS = ("none", "chrome", "edge", "firefox", "brave", "opera", "vivaldi", "chromium")

#: 1.2.0 stored this setting in Portuguese. Left alone, the value would reach
#: yt-dlp as a browser name and every download would fail.
_LEGACY_COOKIE_VALUES = {"nenhum": "none"}


def _migrate(raw: dict) -> bool:
    """Bring values written by an older version up to date, in place.

    Returns whether anything changed, so the caller can write the file back.
    """
    cookies = raw.get("cookies_from_browser")
    if isinstance(cookies, str) and cookies in _LEGACY_COOKIE_VALUES:
        raw["cookies_from_browser"] = _LEGACY_COOKIE_VALUES[cookies]
        logger.info("Setting migrated: cookies_from_browser %r -> 'none'", cookies)
        return True
    return False


@dataclass
class Settings:
    """The user's preferences."""

    output_dir: str = ""
    last_kind: str = "video"
    video_quality: str = DEFAULT_VIDEO_QUALITY
    audio_quality: str = DEFAULT_AUDIO_QUALITY
    video_container: str = DEFAULT_VIDEO_CONTAINER
    audio_container: str = DEFAULT_AUDIO_CONTAINER
    theme: str = "dark"
    #: "auto" follows the Windows language; otherwise "en", "pt_BR" or "es".
    language: str = "auto"
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    write_subtitles: bool = False
    cookies_from_browser: str = "none"
    max_concurrent_downloads: int = 2
    open_folder_when_done: bool = False
    check_ytdlp_updates: bool = True
    window_geometry: str = ""

    def resolved_output_dir(self) -> Path:
        if self.output_dir:
            return Path(self.output_dir)
        return paths.default_download_dir()


class SettingsStore:
    """Reads and writes the settings, tolerating a broken file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or paths.settings_file()
        self._lock = threading.Lock()
        self._migrated = False
        self._settings = self._load()
        if self._migrated:
            self.save()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def settings(self) -> Settings:
        return self._settings

    def _load(self) -> Settings:
        if not self._path.exists():
            return Settings()
        try:
            # utf-8-sig, not utf-8: Notepad and PowerShell both write a BOM,
            # and a file edited by hand should still load.
            raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read the settings (%s); using defaults.", exc)
            return Settings()

        if not isinstance(raw, dict):
            return Settings()

        # A file written by a newer version must not crash an older one.
        known = {f.name for f in fields(Settings)}
        filtered = {key: value for key, value in raw.items() if key in known}
        self._migrated = _migrate(filtered)
        try:
            return Settings(**filtered)
        except TypeError as exc:
            logger.warning("Invalid settings (%s); using defaults.", exc)
            return Settings()

    def save(self) -> None:
        """Persist the settings without letting a disk error break the app."""
        with self._lock:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                temp = self._path.with_suffix(".tmp")
                temp.write_text(
                    json.dumps(asdict(self._settings), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                temp.replace(self._path)
            except OSError as exc:
                logger.error("Failed to save the settings: %s", exc)

    def update(self, **values: object) -> None:
        """Update known fields and persist."""
        known = {f.name for f in fields(Settings)}
        for key, value in values.items():
            if key in known:
                setattr(self._settings, key, value)
        self.save()

    def reset(self) -> None:
        self._settings = Settings()
        self.save()
