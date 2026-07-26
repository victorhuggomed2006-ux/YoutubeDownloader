"""Work that runs off the interface thread.

Each worker is a ``QRunnable`` with its own signals object, so results come
back to the interface through Qt's event queue.
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
    """Signals shared by every worker."""

    finished = Signal(str)  # task_id


class InfoSignals(_Signals):
    ready = Signal(str, object)  # task_id, VideoInfo
    failed = Signal(str, str)  # task_id, message


class InfoWorker(QRunnable):
    """Fetches a video's metadata."""

    def __init__(self, url: str, cookies_from_browser: str, token: str = "") -> None:
        super().__init__()
        # The window keeps a reference so it can cancel; without this Qt would
        # destroy the object once run() returns and the call would be invalid.
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
            logger.exception("Unexpected failure while looking up the video")
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
    """Lists the videos in a playlist."""

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
            logger.exception("Unexpected failure while reading the playlist")
            self.signals.failed.emit(self.token, str(humanize(exc)))
        else:
            self.signals.ready.emit(self.token, videos)
        finally:
            self.signals.finished.emit(self.token)


class ThumbnailSignals(QObject):
    ready = Signal(str, bytes)  # token, image data


class ThumbnailWorker(QRunnable):
    """Downloads a video thumbnail."""

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
            # A missing thumbnail is cosmetic; never let it surface as an error.
            logger.debug("Thumbnail unavailable (%s)", exc)


class DownloadSignals(QObject):
    progress = Signal(str, object)  # task_id, Progress
    completed = Signal(str, object)  # task_id, Path
    failed = Signal(str, str)  # task_id, message
    cancelled = Signal(str)  # task_id
    info_ready = Signal(str, object)  # task_id, VideoInfo


class DownloadWorker(QRunnable):
    """Runs a full download, reporting progress and honouring cancellation."""

    def __init__(
        self,
        task_id: str,
        request: DownloadRequest,
        cookies_from_browser: str,
        info: VideoInfo | None = None,
    ) -> None:
        super().__init__()
        # The queue keeps a live reference so cancellation stays possible.
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

        # Items queued without a loaded preview have no metadata yet.
        if self.info is None:
            try:
                info = self._downloader.fetch_info(self.request.url)
            except Exception:  # the download itself reports the real error
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
            logger.exception("Unexpected failure during the download")
            self.signals.failed.emit(self.task_id, str(humanize(exc)))
        else:
            if self.cancel_event.is_set():
                self.signals.cancelled.emit(self.task_id)
            else:
                self.signals.completed.emit(self.task_id, path)


class UpdateSignals(QObject):
    available = Signal(str)  # new version
    up_to_date = Signal()
    installed = Signal(str)
    failed = Signal(str)


class UpdateCheckWorker(QRunnable):
    """Checks PyPI for a newer yt-dlp."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = UpdateSignals()

    def run(self) -> None:
        from ..core import updater

        try:
            version = updater.update_available()
        except Exception as exc:
            # Being offline must not produce an error dialog at startup.
            logger.debug("Update check failed: %s", exc)
            return
        if version:
            self.signals.available.emit(version)
        else:
            self.signals.up_to_date.emit()


class UpdateInstallWorker(QRunnable):
    """Downloads and installs the newest yt-dlp."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = UpdateSignals()

    def run(self) -> None:
        from ..core import updater

        try:
            version = updater.update_now()
        except Exception as exc:
            logger.warning("Failed to update yt-dlp: %s", exc)
            self.signals.failed.emit(str(exc))
            return

        if version:
            self.signals.installed.emit(version)
        else:
            self.signals.up_to_date.emit()
