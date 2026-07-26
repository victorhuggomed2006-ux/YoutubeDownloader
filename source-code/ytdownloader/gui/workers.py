"""Tarefas executadas fora da thread da interface.

Cada worker é um ``QRunnable`` com um objeto de sinais próprio, para que o
resultado volte à interface pela fila de eventos do Qt.
"""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QObject, QRunnable, Signal

from ..core.downloader import Downloader
from ..core.errors import DownloadCancelled, DownloaderError, humanize
from ..core.models import DownloadRequest, Progress, VideoInfo

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15


class _Signals(QObject):
    """Sinais comuns a todos os workers."""

    finished = Signal(str)  # task_id


class InfoSignals(_Signals):
    ready = Signal(str, object)  # task_id, VideoInfo
    failed = Signal(str, str)  # task_id, mensagem


class InfoWorker(QRunnable):
    """Consulta os metadados de um vídeo."""

    def __init__(self, url: str, cookies_from_browser: str, token: str = "") -> None:
        super().__init__()
        # A janela guarda uma referência para poder cancelar; sem isto o Qt
        # destruiria o objeto ao fim da execução e a chamada seria inválida.
        self.setAutoDelete(False)
        self.url = url
        self.token = token
        self.signals = InfoSignals()
        self._downloader = Downloader(cookies_from_browser=cookies_from_browser)
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    def run(self) -> None:
        try:
            info = self._downloader.fetch_info(self.url)
        except DownloaderError as exc:
            if not self._cancelled.is_set():
                self.signals.failed.emit(self.token, str(exc))
        except Exception as exc:
            logger.exception("Falha inesperada ao consultar o vídeo")
            if not self._cancelled.is_set():
                self.signals.failed.emit(self.token, str(humanize(exc)))
        else:
            if not self._cancelled.is_set():
                self.signals.ready.emit(self.token, info)
        finally:
            self.signals.finished.emit(self.token)


class PlaylistSignals(_Signals):
    ready = Signal(str, object)  # token, list[VideoInfo]
    failed = Signal(str, str)


class PlaylistWorker(QRunnable):
    """Lista os vídeos de uma playlist."""

    def __init__(self, url: str, cookies_from_browser: str, token: str = "") -> None:
        super().__init__()
        self.url = url
        self.token = token
        self.signals = PlaylistSignals()
        self._downloader = Downloader(cookies_from_browser=cookies_from_browser)

    def run(self) -> None:
        try:
            videos = self._downloader.fetch_playlist(self.url)
        except DownloaderError as exc:
            self.signals.failed.emit(self.token, str(exc))
        except Exception as exc:
            logger.exception("Falha inesperada ao consultar a playlist")
            self.signals.failed.emit(self.token, str(humanize(exc)))
        else:
            self.signals.ready.emit(self.token, videos)
        finally:
            self.signals.finished.emit(self.token)


class ThumbnailSignals(QObject):
    ready = Signal(str, bytes)  # token, dados da imagem


class ThumbnailWorker(QRunnable):
    """Baixa a miniatura do vídeo."""

    def __init__(self, url: str, token: str) -> None:
        super().__init__()
        self.url = url
        self.token = token
        self.signals = ThumbnailSignals()

    def run(self) -> None:
        if not self.url:
            return
        try:
            import requests

            response = requests.get(self.url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            self.signals.ready.emit(self.token, response.content)
        except Exception as exc:
            logger.debug("Miniatura indisponível (%s)", exc)


class DownloadSignals(QObject):
    progress = Signal(str, object)  # task_id, Progress
    completed = Signal(str, object)  # task_id, Path
    failed = Signal(str, str)  # task_id, mensagem
    cancelled = Signal(str)  # task_id
    info_ready = Signal(str, object)  # task_id, VideoInfo


class DownloadWorker(QRunnable):
    """Executa um download completo, com progresso e cancelamento."""

    def __init__(
        self,
        task_id: str,
        request: DownloadRequest,
        cookies_from_browser: str,
        info: VideoInfo | None = None,
    ) -> None:
        super().__init__()
        # A fila mantém uma referência viva para permitir o cancelamento.
        self.setAutoDelete(False)
        self.task_id = task_id
        self.request = request
        self.info = info
        self.signals = DownloadSignals()
        self.cancel_event = threading.Event()
        self._downloader = Downloader(cookies_from_browser=cookies_from_browser)

    def cancel(self) -> None:
        self.cancel_event.set()

    def _emit_progress(self, progress: Progress) -> None:
        self.signals.progress.emit(self.task_id, progress)

    def run(self) -> None:
        if self.cancel_event.is_set():
            self.signals.cancelled.emit(self.task_id)
            return

        # Busca os metadados quando o item foi adicionado sem preview carregado.
        if self.info is None:
            try:
                info = self._downloader.fetch_info(self.request.url)
            except Exception:
                info = None
            if info is not None:
                self.info = info
                self.signals.info_ready.emit(self.task_id, info)

        try:
            path = self._downloader.download(
                self.request,
                on_progress=self._emit_progress,
                cancel_event=self.cancel_event,
            )
        except DownloadCancelled:
            self.signals.cancelled.emit(self.task_id)
        except DownloaderError as exc:
            self.signals.failed.emit(self.task_id, str(exc))
        except Exception as exc:
            logger.exception("Falha inesperada durante o download")
            self.signals.failed.emit(self.task_id, str(humanize(exc)))
        else:
            if self.cancel_event.is_set():
                self.signals.cancelled.emit(self.task_id)
            else:
                self.signals.completed.emit(self.task_id, path)


class UpdateSignals(QObject):
    available = Signal(str)  # nova versão
    up_to_date = Signal()
    installed = Signal(str)
    failed = Signal(str)


class UpdateCheckWorker(QRunnable):
    """Verifica no PyPI se existe uma versão mais nova do yt-dlp."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = UpdateSignals()

    def run(self) -> None:
        from ..core import updater

        try:
            version = updater.update_available()
        except Exception as exc:
            logger.debug("Verificação de atualização falhou: %s", exc)
            return
        if version:
            self.signals.available.emit(version)
        else:
            self.signals.up_to_date.emit()


class UpdateInstallWorker(QRunnable):
    """Baixa e instala a versão mais recente do yt-dlp."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = UpdateSignals()

    def run(self) -> None:
        from ..core import updater

        try:
            version = updater.update_now()
        except Exception as exc:
            logger.warning("Falha ao atualizar o yt-dlp: %s", exc)
            self.signals.failed.emit(str(exc))
            return

        if version:
            self.signals.installed.emit(version)
        else:
            self.signals.up_to_date.emit()
