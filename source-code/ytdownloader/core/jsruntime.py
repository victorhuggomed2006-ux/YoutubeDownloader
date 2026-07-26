"""Detecção dos runtimes JavaScript usados pelo yt-dlp.

Desde 2026 o yt-dlp usa um interpretador JavaScript para resolver parte dos
formatos do YouTube. Por padrão ele só procura o Deno; aqui também aceitamos
Node e Bun, que são bem mais comuns nas máquinas dos usuários.

Sem nenhum runtime o download continua funcionando, mas alguns vídeos podem
oferecer menos opções de qualidade.
"""

from __future__ import annotations

import logging
import shutil
from functools import lru_cache

from . import paths

logger = logging.getLogger(__name__)

#: Ordem de preferência. O Deno é o runtime oficialmente suportado.
SUPPORTED_RUNTIMES = ("deno", "node", "bun")


@lru_cache(maxsize=1)
def detect() -> dict[str, dict]:
    """Monta o valor da opção ``js_runtimes`` do yt-dlp.

    Procura primeiro ao lado do executável (caso um runtime seja distribuído
    junto no futuro) e depois no PATH do sistema.
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
        logger.info("Runtimes JavaScript disponíveis: %s", ", ".join(found))
    else:
        logger.info(
            "Nenhum runtime JavaScript encontrado; alguns vídeos podem oferecer "
            "menos opções de qualidade."
        )
    return found


def is_available() -> bool:
    return bool(detect())


def names() -> tuple[str, ...]:
    return tuple(detect())


def reset_cache() -> None:
    """Limpa o cache de detecção (útil em testes)."""
    detect.cache_clear()
