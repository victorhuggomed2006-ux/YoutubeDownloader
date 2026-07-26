"""Configurações do aplicativo, persistidas em JSON na pasta do usuário."""

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

#: Navegadores aceitos para importar cookies (contorna o "confirme que você não é um robô").
COOKIE_BROWSERS = ("nenhum", "chrome", "edge", "firefox", "brave", "opera", "vivaldi", "chromium")


@dataclass
class Settings:
    """Preferências do usuário."""

    output_dir: str = ""
    last_kind: str = "video"
    video_quality: str = DEFAULT_VIDEO_QUALITY
    audio_quality: str = DEFAULT_AUDIO_QUALITY
    video_container: str = DEFAULT_VIDEO_CONTAINER
    audio_container: str = DEFAULT_AUDIO_CONTAINER
    theme: str = "dark"
    #: "auto" segue o idioma do Windows; ou "pt_BR" / "en".
    language: str = "auto"
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    write_subtitles: bool = False
    cookies_from_browser: str = "nenhum"
    max_concurrent_downloads: int = 2
    open_folder_when_done: bool = False
    check_ytdlp_updates: bool = True
    window_geometry: str = ""

    def resolved_output_dir(self) -> Path:
        if self.output_dir:
            return Path(self.output_dir)
        return paths.default_download_dir()


class SettingsStore:
    """Lê e grava as configurações em disco de forma tolerante a falhas."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or paths.settings_file()
        self._lock = threading.Lock()
        self._settings = self._load()

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
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Não foi possível ler as configurações (%s); usando padrões.", exc)
            return Settings()

        if not isinstance(raw, dict):
            return Settings()

        known = {f.name for f in fields(Settings)}
        filtered = {key: value for key, value in raw.items() if key in known}
        try:
            return Settings(**filtered)
        except TypeError as exc:
            logger.warning("Configurações inválidas (%s); usando padrões.", exc)
            return Settings()

    def save(self) -> None:
        """Grava as configurações, sem deixar o app quebrar se o disco falhar."""
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
                logger.error("Falha ao salvar configurações: %s", exc)

    def update(self, **values: object) -> None:
        """Atualiza campos conhecidos e persiste."""
        known = {f.name for f in fields(Settings)}
        for key, value in values.items():
            if key in known:
                setattr(self._settings, key, value)
        self.save()

    def reset(self) -> None:
        self._settings = Settings()
        self.save()
