"""Atualização do yt-dlp sem reinstalar o aplicativo.

O YouTube muda a forma de servir os vídeos com frequência, então uma cópia do
yt-dlp congelada dentro do executável para de funcionar depois de algum tempo.
Para evitar isso, o aplicativo baixa o pacote oficial do PyPI (um arquivo .whl,
que é apenas um ZIP), extrai numa pasta do usuário e a coloca à frente no
``sys.path``. Nenhuma instalação de Python ou pip é necessária.

``activate()`` precisa ser chamada antes do primeiro ``import yt_dlp``.
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
    """Converte ``"2026.7.4"`` em ``(2026, 7, 4)`` para comparação."""
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
        if not (entry / "yt_dlp" / "__init__.py").is_file():
            continue
        found.append((parse_version(entry.name[len(PACKAGE_PREFIX) :]), entry))
    found.sort(key=lambda item: item[0])
    return found


def activate() -> str | None:
    """Coloca a cópia mais nova do yt-dlp à frente no ``sys.path``.

    Retorna a versão ativada, ou ``None`` se a versão embutida for usada.
    """
    if "yt_dlp" in sys.modules:
        logger.debug("yt-dlp já importado; mantendo a versão embutida.")
        return None

    installed = _installed_dirs()
    if not installed:
        return None

    version, directory = installed[-1]
    if str(directory) in sys.path:
        return ".".join(str(p) for p in version)

    sys.path.insert(0, str(directory))
    logger.info("Usando yt-dlp %s de %s", ".".join(str(p) for p in version), directory)
    return ".".join(str(p) for p in version)


def current_version() -> str:
    """Versão do yt-dlp efetivamente carregada."""
    try:
        from yt_dlp.version import __version__

        return str(__version__)
    except Exception:
        return "desconhecida"


def latest_version() -> tuple[str, str, str] | None:
    """Consulta o PyPI e devolve ``(versão, url_do_wheel, sha256)``."""
    try:
        import requests

        response = requests.get(PYPI_URL, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.warning("Não foi possível consultar o PyPI: %s", exc)
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
    """Retorna a versão nova disponível, ou ``None`` se já está atualizado."""
    latest = latest_version()
    if latest is None:
        return None
    version = latest[0]
    if parse_version(version) > parse_version(current_version()):
        return version
    return None


def install(version: str, url: str, sha256: str = "") -> Path:
    """Baixa e extrai o wheel do yt-dlp na pasta de dados do usuário."""
    import requests

    response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
    response.raise_for_status()

    buffer = io.BytesIO()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        buffer.write(chunk)
        if buffer.tell() > MAX_WHEEL_BYTES:
            raise RuntimeError("O pacote baixado é maior que o esperado.")

    payload = buffer.getvalue()
    if sha256:
        actual = hashlib.sha256(payload).hexdigest()
        if actual != sha256:
            raise RuntimeError("A verificação de integridade do pacote falhou.")

    target = paths.runtime_dir() / f"{PACKAGE_PREFIX}{version}"
    staging = target.with_name(target.name + ".tmp")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for member in archive.namelist():
            # Recusa caminhos que tentem escapar da pasta de destino.
            destination = (staging / member).resolve()
            if not str(destination).startswith(str(staging.resolve())):
                raise RuntimeError("O pacote contém caminhos inválidos.")
        archive.extractall(staging)

    if not (staging / "yt_dlp" / "__init__.py").is_file():
        shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError("O pacote baixado não contém o yt-dlp.")

    shutil.rmtree(target, ignore_errors=True)
    staging.replace(target)
    _prune_old(keep=target)
    logger.info("yt-dlp %s instalado em %s", version, target)
    return target


def update_now() -> str | None:
    """Baixa a versão mais recente se houver uma. Retorna a versão instalada."""
    latest = latest_version()
    if latest is None:
        return None

    version, url, digest = latest
    if parse_version(version) <= parse_version(current_version()):
        return None

    install(version, url, digest)
    return version


def _prune_old(keep: Path, max_kept: int = 1) -> None:
    """Remove cópias antigas para não acumular espaço."""
    installed = [d for _, d in _installed_dirs() if d != keep]
    for directory in installed[: max(0, len(installed) - max_kept + 1)]:
        if str(directory) in sys.path:
            continue  # em uso nesta sessão
        shutil.rmtree(directory, ignore_errors=True)
