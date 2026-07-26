"""Descoberta dos diretórios usados pelo aplicativo.

Funciona tanto rodando a partir do código-fonte quanto dentro do executável
gerado pelo PyInstaller, onde os recursos ficam em ``sys._MEIPASS``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "YouTubeDownloader"


def is_frozen() -> bool:
    """Retorna True quando o código está rodando dentro do executável."""
    return getattr(sys, "frozen", False)


def bundle_dir() -> Path:
    """Diretório onde ficam os recursos empacotados.

    No executável é a pasta temporária de extração (``sys._MEIPASS``); no
    código-fonte é a raiz do pacote ``ytdownloader``.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def install_dir() -> Path:
    """Pasta onde o aplicativo está instalado (onde vive o .exe)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def resource_path(*parts: str) -> Path:
    """Caminho de um arquivo dentro de ``ytdownloader/resources``."""
    return bundle_dir().joinpath("resources", *parts)


def app_data_dir() -> Path:
    """Pasta de dados do usuário (configurações, histórico, logs)."""
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
    """Pasta onde versões atualizadas do yt-dlp são instaladas."""
    path = app_data_dir() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_download_dir() -> Path:
    """Pasta de destino padrão dos downloads."""
    candidates = [Path.home() / "Downloads", Path.home() / "Transferências"]
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
