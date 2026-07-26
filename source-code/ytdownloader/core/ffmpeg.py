"""Localização do FFmpeg usado para converter e juntar as faixas.

No aplicativo instalado o FFmpeg vem embutido junto ao executável. Rodando a
partir do código-fonte, procura-se em ``packaging/vendor/ffmpeg`` e, por último,
no PATH do sistema.
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

#: Variável de ambiente que permite apontar um FFmpeg específico.
ENV_OVERRIDE = "YTDOWNLOADER_FFMPEG"


def _candidate_dirs() -> list[Path]:
    dirs: list[Path] = []

    override = os.getenv(ENV_OVERRIDE)
    if override:
        candidate = Path(override)
        dirs.append(candidate if candidate.is_dir() else candidate.parent)

    # Empacotado: ao lado do executável e dentro do bundle temporário.
    dirs.append(paths.install_dir() / "ffmpeg")
    dirs.append(paths.install_dir())
    dirs.append(paths.bundle_dir() / "ffmpeg")

    # Desenvolvimento: binários baixados pelo script de build.
    repo_root = Path(__file__).resolve().parents[3]
    dirs.append(repo_root / "packaging" / "vendor" / "ffmpeg")
    dirs.append(repo_root / "packaging" / "vendor" / "ffmpeg" / "bin")

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
    """Caminho do executável do FFmpeg, ou ``None`` se não for encontrado."""
    return _find(FFMPEG_NAME)


@lru_cache(maxsize=1)
def ffprobe_path() -> Path | None:
    """Caminho do executável do FFprobe, ou ``None`` se não for encontrado."""
    return _find(FFPROBE_NAME)


def ffmpeg_location() -> str | None:
    """Valor para a opção ``ffmpeg_location`` do yt-dlp.

    O yt-dlp aceita o diretório que contém os binários, o que também deixa o
    ``ffprobe`` visível para ele.
    """
    path = ffmpeg_path()
    if path is None:
        return None
    return str(path.parent)


def is_available() -> bool:
    return ffmpeg_path() is not None


def reset_cache() -> None:
    """Limpa o cache de descoberta (útil em testes)."""
    ffmpeg_path.cache_clear()
    ffprobe_path.cache_clear()
