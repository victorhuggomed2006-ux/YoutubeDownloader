"""The application's main window."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QTimer, QUrl, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__
from ..core import ffmpeg as ffmpeg_module
from ..core.formats import (
    AUDIO_CONTAINERS,
    AUDIO_QUALITIES,
    VIDEO_CONTAINERS,
    VIDEO_QUALITIES,
    MediaKind,
)
from ..core.history import HistoryStore
from ..core.models import (
    DownloadRequest,
    DownloadTask,
    HistoryEntry,
    Progress,
    TaskStatus,
    VideoInfo,
)
from ..core.settings import SettingsStore
from ..core.urls import parse_url
from .dialogs import AboutDialog, SettingsDialog
from .i18n import translate_core
from .theme import build_stylesheet
from .widgets import HistoryView, PreviewCard, QueueItemWidget
from .workers import (
    DownloadWorker,
    InfoWorker,
    PlaylistWorker,
    ThumbnailWorker,
    UpdateCheckWorker,
    UpdateInstallWorker,
)

logger = logging.getLogger(__name__)

PREVIEW_DEBOUNCE_MS = 600
MAX_PLAYLIST_ITEMS = 100


class MainWindow(QMainWindow):
    """The single window: input, options, queue and history."""

    def __init__(self, settings_store: SettingsStore, history_store: HistoryStore) -> None:
        super().__init__()
        self._settings_store = settings_store
        self._history_store = history_store

        self._tasks: dict[str, DownloadTask] = {}
        self._widgets: dict[str, QueueItemWidget] = {}
        self._workers: dict[str, DownloadWorker] = {}
        self._current_info: VideoInfo | None = None
        self._preview_token = 0
        self._info_worker: InfoWorker | None = None

        # Two pools: downloads must not starve the preview and thumbnail work.
        self._download_pool = QThreadPool()
        self._download_pool.setMaxThreadCount(
            max(1, min(settings_store.settings.max_concurrent_downloads, 5))
        )
        self._aux_pool = QThreadPool()
        self._aux_pool.setMaxThreadCount(4)

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(PREVIEW_DEBOUNCE_MS)
        self._preview_timer.timeout.connect(self._load_preview)

        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.setMinimumSize(940, 720)
        self._apply_window_icon()

        self._build_ui()
        self._apply_theme()
        self._restore_geometry()
        self._check_ffmpeg()
        self._maybe_check_updates()

    # ── Building the interface ───────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 14)
        root.setSpacing(16)

        root.addLayout(self._build_header())
        root.addWidget(self._build_input_card())
        root.addWidget(self._build_tabs(), 1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(self.tr("Ready"))

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(1)

        title = QLabel(__app_name__)
        title.setObjectName("AppTitle")
        titles.addWidget(title)

        subtitle = QLabel(self.tr("Download video and audio at any quality"))
        subtitle.setObjectName("AppSubtitle")
        titles.addWidget(subtitle)

        header.addLayout(titles)
        header.addStretch(1)

        settings_button = QPushButton(self.tr("Settings"))
        settings_button.setObjectName("GhostButton")
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.clicked.connect(self._open_settings)
        header.addWidget(settings_button)

        about_button = QPushButton(self.tr("About"))
        about_button.setObjectName("GhostButton")
        about_button.setCursor(Qt.CursorShape.PointingHandCursor)
        about_button.clicked.connect(self._open_about)
        header.addWidget(about_button)

        return header

    def _build_input_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        url_label = QLabel(self.tr("VIDEO LINK"))
        url_label.setObjectName("SectionLabel")
        layout.addWidget(url_label)

        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText(
            self.tr("Paste a video link — YouTube, Vimeo, Twitch, SoundCloud and more")
        )
        self._url_edit.setClearButtonEnabled(True)
        self._url_edit.textChanged.connect(self._on_url_changed)
        self._url_edit.returnPressed.connect(self._start_download)
        url_row.addWidget(self._url_edit, 1)

        paste_button = QPushButton(self.tr("Paste"))
        paste_button.setObjectName("GhostButton")
        paste_button.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_button.clicked.connect(self._paste_from_clipboard)
        url_row.addWidget(paste_button)

        layout.addLayout(url_row)

        self._preview = PreviewCard()
        layout.addWidget(self._preview)

        layout.addLayout(self._build_options_row())
        layout.addLayout(self._build_folder_row())

        self._download_button = QPushButton(self.tr("Download"))
        self._download_button.setObjectName("PrimaryButton")
        self._download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._download_button.setEnabled(False)
        self._download_button.clicked.connect(self._start_download)
        layout.addWidget(self._download_button)

        return card

    def _build_options_row(self) -> QHBoxLayout:
        settings = self._settings_store.settings
        row = QHBoxLayout()
        row.setSpacing(14)

        kind_column = QVBoxLayout()
        kind_column.setSpacing(6)
        kind_label = QLabel(self.tr("WHAT TO GET"))
        kind_label.setObjectName("SectionLabel")
        kind_column.addWidget(kind_label)

        segment = QHBoxLayout()
        segment.setSpacing(0)

        self._video_button = QPushButton(self.tr("Video"))
        self._video_button.setObjectName("SegmentLeft")
        self._video_button.setCheckable(True)
        self._video_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self._audio_button = QPushButton(self.tr("Audio"))
        self._audio_button.setObjectName("SegmentRight")
        self._audio_button.setCheckable(True)
        self._audio_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self._kind_group = QButtonGroup(self)
        self._kind_group.setExclusive(True)
        self._kind_group.addButton(self._video_button)
        self._kind_group.addButton(self._audio_button)

        if settings.last_kind == "audio":
            self._audio_button.setChecked(True)
        else:
            self._video_button.setChecked(True)

        self._video_button.toggled.connect(self._on_kind_changed)

        segment.addWidget(self._video_button)
        segment.addWidget(self._audio_button)
        segment.addStretch(1)
        kind_column.addLayout(segment)
        row.addLayout(kind_column)

        quality_column = QVBoxLayout()
        quality_column.setSpacing(6)
        self._quality_label = QLabel(self.tr("QUALITY"))
        self._quality_label.setObjectName("SectionLabel")
        quality_column.addWidget(self._quality_label)
        self._quality_combo = QComboBox()
        self._quality_combo.setMinimumWidth(190)
        self._quality_combo.currentIndexChanged.connect(self._persist_choices)
        quality_column.addWidget(self._quality_combo)
        row.addLayout(quality_column, 1)

        container_column = QVBoxLayout()
        container_column.setSpacing(6)
        container_label = QLabel(self.tr("FORMAT"))
        container_label.setObjectName("SectionLabel")
        container_column.addWidget(container_label)
        self._container_combo = QComboBox()
        self._container_combo.setMinimumWidth(110)
        self._container_combo.currentIndexChanged.connect(self._persist_choices)
        container_column.addWidget(self._container_combo)
        row.addLayout(container_column)

        self._reload_options()
        return row

    def _build_folder_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel(self.tr("Save to:"))
        label.setObjectName("Muted")
        row.addWidget(label)

        self._folder_label = QLabel()
        self._folder_label.setObjectName("Muted")
        self._folder_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        row.addWidget(self._folder_label, 1)

        change_button = QPushButton(self.tr("Change folder"))
        change_button.setObjectName("LinkButton")
        change_button.setCursor(Qt.CursorShape.PointingHandCursor)
        change_button.clicked.connect(self._choose_output_dir)
        row.addWidget(change_button)

        self._update_folder_label()
        return row

    def _build_tabs(self) -> QTabWidget:
        self._tabs = QTabWidget()

        queue_page = QWidget()
        queue_layout = QVBoxLayout(queue_page)
        queue_layout.setContentsMargins(0, 8, 0, 0)
        queue_layout.setSpacing(8)

        self._queue_scroll = QScrollArea()
        self._queue_scroll.setWidgetResizable(True)
        self._queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._queue_layout = QVBoxLayout(container)
        self._queue_layout.setContentsMargins(2, 2, 8, 2)
        self._queue_layout.setSpacing(9)
        self._queue_layout.addStretch(1)
        self._queue_scroll.setWidget(container)

        self._queue_empty = QLabel(
            self.tr("Nothing in the queue.\nPaste a link above and click Download.")
        )
        self._queue_empty.setObjectName("EmptyState")
        self._queue_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)

        queue_layout.addWidget(self._queue_empty)
        queue_layout.addWidget(self._queue_scroll, 1)
        self._queue_scroll.setVisible(False)

        self._tabs.addTab(queue_page, self.tr("Downloads"))

        history_page = QWidget()
        history_layout = QVBoxLayout(history_page)
        history_layout.setContentsMargins(0, 8, 0, 0)
        self._history_view = HistoryView(self._history_store)
        self._history_view.open_file_requested.connect(self._open_path)
        history_layout.addWidget(self._history_view)
        self._tabs.addTab(history_page, self.tr("History"))

        return self._tabs

    # ── Appearance ───────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(self._settings_store.settings.theme))

    def _apply_window_icon(self) -> None:
        from ..core import paths

        for name in ("icon.ico", "icon.png"):
            candidate = paths.resource_path(name)
            if candidate.is_file():
                self.setWindowIcon(QIcon(str(candidate)))
                return

    def _restore_geometry(self) -> None:
        raw = self._settings_store.settings.window_geometry
        if not raw:
            return
        try:
            from PySide6.QtCore import QByteArray

            self.restoreGeometry(QByteArray.fromBase64(raw.encode("ascii")))
        except Exception:
            logger.debug("Could not restore the window geometry.")

    # ── Options ──────────────────────────────────────────────────────────

    @property
    def _kind(self) -> MediaKind:
        return MediaKind.AUDIO if self._audio_button.isChecked() else MediaKind.VIDEO

    def _reload_options(self) -> None:
        """Refill quality and format for the selected media kind."""
        settings = self._settings_store.settings
        is_audio = self._kind is MediaKind.AUDIO

        self._quality_combo.blockSignals(True)
        self._container_combo.blockSignals(True)

        self._quality_combo.clear()
        self._container_combo.clear()

        if is_audio:
            self._quality_label.setText(self.tr("BITRATE"))
            qualities, containers = AUDIO_QUALITIES, AUDIO_CONTAINERS
        else:
            self._quality_label.setText(self.tr("QUALITY"))
            qualities, containers = VIDEO_QUALITIES, VIDEO_CONTAINERS

        for option in qualities:
            self._quality_combo.addItem(translate_core(option.label), option.key)
            self._quality_combo.setItemData(
                self._quality_combo.count() - 1,
                translate_core(option.description),
                Qt.ItemDataRole.ToolTipRole,
            )
        for container in containers:
            self._container_combo.addItem(container.upper(), container)

        if is_audio:
            self._select_data(self._quality_combo, settings.audio_quality)
            self._select_data(self._container_combo, settings.audio_container)
        else:
            self._select_data(self._quality_combo, settings.video_quality)
            self._select_data(self._container_combo, settings.video_container)

        self._quality_combo.blockSignals(False)
        self._container_combo.blockSignals(False)

    @staticmethod
    def _select_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    @Slot()
    def _on_kind_changed(self) -> None:
        self._reload_options()
        self._persist_choices()

    @Slot()
    def _persist_choices(self) -> None:
        quality = self._quality_combo.currentData()
        container = self._container_combo.currentData()
        if quality is None or container is None:
            return
        if self._kind is MediaKind.AUDIO:
            self._settings_store.update(
                last_kind="audio", audio_quality=quality, audio_container=container
            )
        else:
            self._settings_store.update(
                last_kind="video", video_quality=quality, video_container=container
            )

    def _update_folder_label(self) -> None:
        path = self._settings_store.settings.resolved_output_dir()
        self._folder_label.setText(str(path))
        self._folder_label.setToolTip(str(path))

    @Slot()
    def _choose_output_dir(self) -> None:
        current = str(self._settings_store.settings.resolved_output_dir())
        chosen = QFileDialog.getExistingDirectory(
            self, self.tr("Choose the destination folder"), current
        )
        if chosen:
            self._settings_store.update(output_dir=chosen)
            self._update_folder_label()

    # ── URL input and preview ────────────────────────────────────────────

    @Slot()
    def _paste_from_clipboard(self) -> None:
        clipboard = QGuiApplication.clipboard()
        text = (clipboard.text() if clipboard else "").strip()
        if not text:
            self.statusBar().showMessage(self.tr("The clipboard is empty."), 4000)
            return
        self._url_edit.setText(text)
        self._url_edit.setFocus()

    @Slot(str)
    def _on_url_changed(self, text: str) -> None:
        text = text.strip()
        parsed = parse_url(text)

        if not text:
            state = ""
            self._download_button.setEnabled(False)
        elif parsed.is_supported:
            state = "valid"
            self._download_button.setEnabled(True)
        else:
            state = "invalid"
            self._download_button.setEnabled(False)

        if self._url_edit.property("state") != state:
            self._url_edit.setProperty("state", state)
            self._url_edit.style().unpolish(self._url_edit)
            self._url_edit.style().polish(self._url_edit)

        self._current_info = None
        self._preview_timer.stop()

        if parsed.is_playlist:
            self._preview.clear()
            self.statusBar().showMessage(
                self.tr("Playlist link detected. Click Download to pick the videos."),
                6000,
            )
        elif parsed.is_supported:
            self._preview.show_loading()
            self._preview_timer.start()
            if not parsed.is_youtube:
                self.statusBar().showMessage(
                    self.tr("Recognised site: {site}").format(site=parsed.site_name), 4000
                )
        else:
            self._preview.clear()

    def _load_preview(self) -> None:
        url = self._url_edit.text().strip()
        parsed = parse_url(url)
        if not parsed.is_supported or parsed.is_playlist:
            return

        if self._info_worker is not None:
            self._info_worker.cancel()

        self._preview_token += 1
        token = str(self._preview_token)

        # On YouTube the thumbnail address is predictable, so it shows up right
        # away. On other sites, only once the lookup answers.
        thumbnail = parsed.thumbnail_url
        if thumbnail:
            self._start_thumbnail(thumbnail, f"preview:{token}")

        worker = InfoWorker(parsed.canonical, self._cookies_setting(), token)
        worker.signals.ready.connect(self._on_preview_ready)
        worker.signals.failed.connect(self._on_preview_failed)
        self._info_worker = worker
        self._aux_pool.start(worker)

    def _start_thumbnail(self, url: str, token: str) -> None:
        worker = ThumbnailWorker(url, token)
        worker.signals.ready.connect(self._on_thumbnail_ready)
        self._aux_pool.start(worker)

    @Slot(str, object)
    def _on_preview_ready(self, token: str, info: VideoInfo) -> None:
        if token != str(self._preview_token):
            return
        self._current_info = info
        self._preview.show_info(info)
        if info.thumbnail:
            self._start_thumbnail(info.thumbnail, f"preview:{token}")

    @Slot(str, str)
    def _on_preview_failed(self, token: str, message: str) -> None:
        if token != str(self._preview_token):
            return
        self._current_info = None
        self._preview.show_error(translate_core(message))

    @Slot(str, bytes)
    def _on_thumbnail_ready(self, token: str, data: bytes) -> None:
        if token.startswith("preview:"):
            if token.split(":", 1)[1] == str(self._preview_token):
                self._preview.set_thumbnail(data)
            return
        widget = self._widgets.get(token)
        if widget is not None:
            widget.set_thumbnail(data)

    def _cookies_setting(self) -> str:
        return self._settings_store.settings.cookies_from_browser

    # ── Downloads ────────────────────────────────────────────────────────

    def _current_request(self, url: str) -> DownloadRequest:
        settings = self._settings_store.settings
        return DownloadRequest(
            url=url,
            kind=self._kind,
            quality=self._quality_combo.currentData() or "",
            container=self._container_combo.currentData() or "",
            output_dir=settings.resolved_output_dir(),
            embed_thumbnail=settings.embed_thumbnail,
            embed_metadata=settings.embed_metadata,
            write_subtitles=settings.write_subtitles,
        ).normalized()

    @Slot()
    def _start_download(self) -> None:
        url = self._url_edit.text().strip()
        parsed = parse_url(url)
        if not parsed.is_supported:
            self.statusBar().showMessage(self.tr("Enter a valid video address."), 5000)
            return

        if self._kind is MediaKind.VIDEO and not ffmpeg_module.is_available():
            self._warn_missing_ffmpeg()
            return

        if parsed.is_playlist:
            self._ask_playlist(parsed.canonical)
            return

        self._enqueue(self._current_request(parsed.canonical), self._current_info)
        self._url_edit.clear()
        self._preview.clear()
        self._current_info = None
        self._tabs.setCurrentIndex(0)

    def _ask_playlist(self, url: str) -> None:
        answer = QMessageBox.question(
            self,
            self.tr("Playlist detected"),
            self.tr(
                "This link points to a playlist.\n\nAdd its videos to the queue (up to {limit})?"
            ).format(limit=MAX_PLAYLIST_ITEMS),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.statusBar().showMessage(self.tr("Reading the playlist..."))
        worker = PlaylistWorker(url, self._cookies_setting(), "playlist")
        worker.signals.ready.connect(self._on_playlist_ready)
        worker.signals.failed.connect(self._on_playlist_failed)
        self._aux_pool.start(worker)

    @Slot(str, object)
    def _on_playlist_ready(self, _token: str, videos: list[VideoInfo]) -> None:
        selected = videos[:MAX_PLAYLIST_ITEMS]
        for info in selected:
            url = info.webpage_url or f"https://www.youtube.com/watch?v={info.video_id}"
            self._enqueue(self._current_request(url), info)

        self.statusBar().showMessage(
            self.tr("%n video(s) added to the queue.", "", len(selected)), 6000
        )
        self._url_edit.clear()
        self._preview.clear()
        self._tabs.setCurrentIndex(0)

    @Slot(str, str)
    def _on_playlist_failed(self, _token: str, message: str) -> None:
        translated = translate_core(message)
        self.statusBar().showMessage(translated, 8000)
        QMessageBox.warning(self, self.tr("Could not read the playlist"), translated)

    def _enqueue(self, request: DownloadRequest, info: VideoInfo | None) -> None:
        task = DownloadTask(request=request, info=info)
        self._tasks[task.task_id] = task

        widget = QueueItemWidget(task)
        widget.cancel_requested.connect(self._cancel_task)
        widget.remove_requested.connect(self._remove_task)
        widget.retry_requested.connect(self._retry_task)
        widget.open_file_requested.connect(self._open_task_file)
        widget.open_folder_requested.connect(self._open_task_folder)

        self._widgets[task.task_id] = widget
        self._queue_layout.insertWidget(self._queue_layout.count() - 1, widget)
        self._queue_empty.setVisible(False)
        self._queue_scroll.setVisible(True)

        thumbnail = info.thumbnail if info else parse_url(request.url).thumbnail_url
        if thumbnail:
            self._start_thumbnail(thumbnail, task.task_id)

        self._launch(task)

    def _launch(self, task: DownloadTask) -> None:
        task.status = TaskStatus.QUEUED
        task.progress = Progress(status=TaskStatus.QUEUED)
        task.error = ""

        worker = DownloadWorker(task.task_id, task.request, self._cookies_setting(), task.info)
        worker.signals.progress.connect(self._on_task_progress)
        worker.signals.completed.connect(self._on_task_completed)
        worker.signals.failed.connect(self._on_task_failed)
        worker.signals.cancelled.connect(self._on_task_cancelled)
        worker.signals.info_ready.connect(self._on_task_info)

        self._workers[task.task_id] = worker
        self._download_pool.start(worker)
        self._update_status_summary()

    # ── Worker callbacks ─────────────────────────────────────────────────

    @Slot(str, object)
    def _on_task_progress(self, task_id: str, progress: Progress) -> None:
        task = self._tasks.get(task_id)
        widget = self._widgets.get(task_id)
        if task is None or widget is None:
            return
        task.progress = progress
        task.status = progress.status
        widget.update_progress(progress)
        self._update_status_summary()

    @Slot(str, object)
    def _on_task_info(self, task_id: str, info: VideoInfo) -> None:
        task = self._tasks.get(task_id)
        widget = self._widgets.get(task_id)
        if task is None or widget is None:
            return
        task.info = info
        widget.update_task(task)
        if info.thumbnail:
            self._start_thumbnail(info.thumbnail, task_id)

    @Slot(str, object)
    def _on_task_completed(self, task_id: str, path: Path) -> None:
        task = self._tasks.get(task_id)
        widget = self._widgets.get(task_id)
        if task is None or widget is None:
            return

        task.status = TaskStatus.COMPLETED
        task.output_file = Path(path)
        task.progress.status = TaskStatus.COMPLETED
        task.progress.percent = 100.0
        if task.output_file.exists():
            size = task.output_file.stat().st_size
            task.progress.total_bytes = size
            task.progress.downloaded_bytes = size

        widget.update_task(task)
        self._workers.pop(task_id, None)
        self._record_history(task)
        self.statusBar().showMessage(
            self.tr("Finished: {title}").format(title=task.display_title), 8000
        )

        if self._settings_store.settings.open_folder_when_done:
            self._open_path(str(task.output_file.parent))

        self._update_status_summary()

    @Slot(str, str)
    def _on_task_failed(self, task_id: str, message: str) -> None:
        task = self._tasks.get(task_id)
        widget = self._widgets.get(task_id)
        if task is None or widget is None:
            return
        task.status = TaskStatus.FAILED
        task.error = message
        widget.update_task(task)
        self._workers.pop(task_id, None)
        self._record_history(task)
        self.statusBar().showMessage(translate_core(message), 10000)
        self._update_status_summary()

    @Slot(str)
    def _on_task_cancelled(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        widget = self._widgets.get(task_id)
        if task is None or widget is None:
            return
        task.status = TaskStatus.CANCELLED
        widget.update_task(task)
        self._workers.pop(task_id, None)
        self.statusBar().showMessage(self.tr("Download cancelled."), 5000)
        self._update_status_summary()

    def _record_history(self, task: DownloadTask) -> None:
        try:
            self._history_view.add_entry(HistoryEntry.from_task(task))
        except Exception:
            logger.exception("Failed to record the history entry")

    # ── Queue actions ────────────────────────────────────────────────────

    @Slot(str)
    def _cancel_task(self, task_id: str) -> None:
        worker = self._workers.get(task_id)
        if worker is not None:
            worker.cancel()
        else:
            self._on_task_cancelled(task_id)

    @Slot(str)
    def _remove_task(self, task_id: str) -> None:
        widget = self._widgets.pop(task_id, None)
        self._tasks.pop(task_id, None)
        self._workers.pop(task_id, None)
        if widget is not None:
            self._queue_layout.removeWidget(widget)
            widget.deleteLater()
        if not self._widgets:
            self._queue_scroll.setVisible(False)
            self._queue_empty.setVisible(True)
        self._update_status_summary()

    @Slot(str)
    def _retry_task(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        widget = self._widgets.get(task_id)
        if task is None or widget is None:
            return
        self._launch(task)
        widget.update_task(task)

    @Slot(str)
    def _open_task_file(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task and task.output_file:
            self._open_path(str(task.output_file))

    @Slot(str)
    def _open_task_folder(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task and task.output_file:
            self._reveal_in_explorer(task.output_file)
        else:
            self._open_path(str(self._settings_store.settings.resolved_output_dir()))

    @Slot(str)
    def _open_path(self, path: str) -> None:
        if not path:
            return
        target = Path(path)
        if not target.exists():
            self.statusBar().showMessage(self.tr("The file is no longer where it was saved."), 6000)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _reveal_in_explorer(self, path: Path) -> None:
        """Open Explorer with the file already selected.

        The path comes from a file the application itself just wrote, and goes
        in as a list argument rather than through an interpreted command line —
        a file name cannot turn into a command here.
        """
        if not path.exists():
            self._open_path(str(path.parent))
            return

        if sys.platform == "win32":
            explorer = Path(os.environ.get("WINDIR", r"C:\Windows")) / "explorer.exe"
            try:
                subprocess.run(  # noqa: S603 - list arguments, no shell
                    [str(explorer), "/select,", os.path.normpath(str(path))],
                    check=False,
                )
                return
            except OSError:
                logger.debug("Could not open Explorer; falling back to the folder.")

        self._open_path(str(path.parent))

    def _update_status_summary(self) -> None:
        active = sum(1 for task in self._tasks.values() if not task.status.is_final)
        if active:
            self.statusBar().showMessage(self.tr("%n download(s) in progress", "", active))

    # ── Dialogs ──────────────────────────────────────────────────────────

    @Slot()
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings_store, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._apply_theme()
            self._update_folder_label()
            self._reload_options()
            self._download_pool.setMaxThreadCount(
                max(1, min(self._settings_store.settings.max_concurrent_downloads, 5))
            )

            if dialog.language_changed:
                # Qt only rebuilds the text of widgets created after the switch;
                # asking for a restart is more honest than showing half a
                # translated interface.
                QMessageBox.information(
                    self,
                    self.tr("Language changed"),
                    self.tr("Close and reopen the app to apply the new language."),
                )

            self.statusBar().showMessage(self.tr("Settings saved."), 4000)

    @Slot()
    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _check_ffmpeg(self) -> None:
        if ffmpeg_module.is_available():
            return
        self.statusBar().showMessage(
            self.tr("FFmpeg not found — audio conversion and high resolution are unavailable."),
            12000,
        )

    def _warn_missing_ffmpeg(self) -> None:
        QMessageBox.warning(
            self,
            self.tr("FFmpeg not found"),
            self.tr(
                "FFmpeg is required to merge video with audio and to convert files.\n\n"
                "If you used the official installer, reinstall the app. Running from "
                "source, execute packaging/fetch_ffmpeg.ps1."
            ),
        )

    # ── yt-dlp updates ───────────────────────────────────────────────────

    def _maybe_check_updates(self) -> None:
        if not self._settings_store.settings.check_ytdlp_updates:
            return
        worker = UpdateCheckWorker()
        worker.signals.available.connect(self._on_update_available)
        self._aux_pool.start(worker)

    @Slot(str)
    def _on_update_available(self, version: str) -> None:
        answer = QMessageBox.question(
            self,
            self.tr("Update available"),
            self.tr(
                "A newer version of the download engine is available (yt-dlp {version}).\n\n"
                "Keeping this component up to date is what keeps downloads working. "
                "Update now?"
            ).format(version=version),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.statusBar().showMessage(self.tr("Updating the download engine..."))
        worker = UpdateInstallWorker()
        worker.signals.installed.connect(self._on_update_installed)
        worker.signals.failed.connect(self._on_update_failed)
        self._aux_pool.start(worker)

    @Slot(str)
    def _on_update_failed(self, message: str) -> None:
        self.statusBar().showMessage(
            self.tr("Update failed: {reason}").format(reason=message), 10000
        )

    @Slot(str)
    def _on_update_installed(self, version: str) -> None:
        self.statusBar().showMessage(
            self.tr("yt-dlp {version} installed.").format(version=version), 8000
        )
        QMessageBox.information(
            self,
            self.tr("Update complete"),
            self.tr(
                "The download engine was updated to version {version}.\n\n"
                "Close and reopen the app to start using it."
            ).format(version=version),
        )

    # ── Shutdown ─────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        active = [task for task in self._tasks.values() if not task.status.is_final]
        if active:
            answer = QMessageBox.question(
                self,
                self.tr("Quit the application"),
                self.tr(
                    "There are %n download(s) in progress.\n\nCancel them and quit?",
                    "",
                    len(active),
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        for worker in list(self._workers.values()):
            worker.cancel()

        geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
        self._settings_store.update(window_geometry=geometry)

        self._download_pool.waitForDone(3000)
        self._aux_pool.waitForDone(1500)
        event.accept()
