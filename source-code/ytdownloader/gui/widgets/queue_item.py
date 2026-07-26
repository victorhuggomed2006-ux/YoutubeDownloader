"""Item da fila de downloads."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from ...core.formats import MediaKind
from ...core.models import DownloadTask, Progress, TaskStatus
from ...core.urls import format_eta, format_size, format_speed
from ..i18n import traduzir_do_nucleo

THUMB_WIDTH = 96
THUMB_HEIGHT = 54

#: Separador visual entre as informações da linha. Não é texto traduzível.
SEPARADOR = "  ·  "


class QueueItemWidget(QFrame):
    """Uma linha da fila: miniatura, título, progresso e ações."""

    cancel_requested = Signal(str)
    remove_requested = Signal(str)
    open_file_requested = Signal(str)
    open_folder_requested = Signal(str)
    retry_requested = Signal(str)

    def __init__(self, task: DownloadTask, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("QueueItem")
        self.task_id = task.task_id
        self._task = task

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 11, 12, 11)
        root.setSpacing(13)

        self._thumb = QLabel()
        self._thumb.setObjectName("Thumb")
        self._thumb.setFixedSize(THUMB_WIDTH, THUMB_HEIGHT)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._thumb)

        column = QVBoxLayout()
        column.setSpacing(6)

        self._title = QLabel(task.display_title)
        self._title.setObjectName("QueueTitle")
        self._title.setWordWrap(False)
        self._title.setTextFormat(Qt.TextFormat.PlainText)
        column.addWidget(self._title)

        self._progress = QProgressBar()
        self._progress.setRange(0, 1000)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        column.addWidget(self._progress)

        self._status = QLabel(TaskStatus.QUEUED.label)
        self._status.setObjectName("QueueMeta")
        self._status.setWordWrap(True)
        column.addWidget(self._status)

        root.addLayout(column, 1)

        actions = QVBoxLayout()
        actions.setSpacing(6)
        actions.addStretch(1)

        self._primary_button = QPushButton(self.tr("Cancelar"))
        self._primary_button.setObjectName("GhostButton")
        self._primary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._primary_button.clicked.connect(self._on_primary_clicked)
        actions.addWidget(self._primary_button)

        self._secondary_button = QPushButton(self.tr("Abrir pasta"))
        self._secondary_button.setObjectName("GhostButton")
        self._secondary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._secondary_button.setVisible(False)
        self._secondary_button.clicked.connect(self._on_secondary_clicked)
        actions.addWidget(self._secondary_button)

        actions.addStretch(1)
        root.addLayout(actions)

        self.update_task(task)

    # ── Atualização ──────────────────────────────────────────────────────

    def set_thumbnail(self, data: bytes) -> None:
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        scaled = pixmap.scaled(
            THUMB_WIDTH,
            THUMB_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - THUMB_WIDTH) // 2)
        y = max(0, (scaled.height() - THUMB_HEIGHT) // 2)
        self._thumb.setPixmap(scaled.copy(x, y, THUMB_WIDTH, THUMB_HEIGHT))

    def update_task(self, task: DownloadTask) -> None:
        """Redesenha o item a partir do estado atual da tarefa."""
        self._task = task
        self._title.setText(self._elided_title(task.display_title))
        self._title.setToolTip(task.display_title)
        self._apply_status(task)

    def update_progress(self, progress: Progress) -> None:
        self._task.progress = progress
        if progress.status is not TaskStatus.QUEUED:
            self._task.status = progress.status
        self._apply_status(self._task)

    def _elided_title(self, text: str, limit: int = 68) -> str:
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _apply_status(self, task: DownloadTask) -> None:
        status = task.status
        progress = task.progress

        self._progress.setValue(int(max(0.0, min(progress.percent, 100.0)) * 10))
        self._set_progress_state("normal")

        kind_label = self.tr("Áudio") if task.request.kind is MediaKind.AUDIO else self.tr("Vídeo")
        quality = task.request.quality
        if task.request.kind is MediaKind.AUDIO:
            quality = self.tr("{taxa} kbps").format(taxa=quality)
        base = SEPARADOR.join([kind_label, quality, task.request.container.upper()])

        if status is TaskStatus.DOWNLOADING:
            pieces = [f"{progress.percent:.1f}%"]
            if progress.total_bytes:
                pieces.append(
                    self.tr("{baixado} de {total}").format(
                        baixado=format_size(progress.downloaded_bytes),
                        total=format_size(progress.total_bytes),
                    )
                )
            if progress.speed:
                pieces.append(format_speed(progress.speed))
            if progress.eta:
                pieces.append(self.tr("faltam {tempo}").format(tempo=format_eta(progress.eta)))
            self._status.setText(SEPARADOR.join(pieces))
            self._status.setObjectName("QueueMeta")
            self._show_cancel()

        elif status is TaskStatus.CONVERTING:
            self._progress.setValue(1000)
            self._status.setText(
                traduzir_do_nucleo(progress.detail) or self.tr("Processando o arquivo...")
            )
            self._status.setObjectName("QueueMeta")
            self._show_cancel()

        elif status is TaskStatus.FETCHING:
            self._progress.setValue(0)
            self._status.setText(
                traduzir_do_nucleo(progress.detail) or self.tr("Consultando o vídeo...")
            )
            self._status.setObjectName("QueueMeta")
            self._show_cancel()

        elif status is TaskStatus.QUEUED:
            self._progress.setValue(0)
            self._status.setText(SEPARADOR.join([self.tr("Na fila"), base]))
            self._status.setObjectName("QueueMeta")
            self._show_cancel()

        elif status is TaskStatus.COMPLETED:
            self._progress.setValue(1000)
            self._set_progress_state("done")
            size = format_size(progress.total_bytes or progress.downloaded_bytes)
            self._status.setText(SEPARADOR.join([self.tr("Concluído"), base, size]))
            self._status.setObjectName("StatusOk")
            self._show_completed()

        elif status is TaskStatus.FAILED:
            self._set_progress_state("error")
            self._progress.setValue(1000)
            self._status.setText(traduzir_do_nucleo(task.error) or self.tr("Falhou"))
            self._status.setObjectName("StatusError")
            self._show_retry()

        elif status is TaskStatus.CANCELLED:
            self._progress.setValue(0)
            self._status.setText(self.tr("Cancelado"))
            self._status.setObjectName("QueueMeta")
            self._show_retry()

        self._restyle(self._status)

    def _set_progress_state(self, state: str) -> None:
        if self._progress.property("state") != state:
            self._progress.setProperty("state", state)
            self._restyle(self._progress)

    @staticmethod
    def _restyle(widget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    # ── Botões ───────────────────────────────────────────────────────────

    def _show_cancel(self) -> None:
        self._primary_button.setText(self.tr("Cancelar"))
        self._primary_button.setEnabled(True)
        self._secondary_button.setVisible(False)

    def _show_completed(self) -> None:
        self._primary_button.setText(self.tr("Abrir"))
        self._primary_button.setEnabled(True)
        self._secondary_button.setText(self.tr("Abrir pasta"))
        self._secondary_button.setVisible(True)

    def _show_retry(self) -> None:
        self._primary_button.setText(self.tr("Tentar de novo"))
        self._primary_button.setEnabled(True)
        self._secondary_button.setText(self.tr("Remover"))
        self._secondary_button.setVisible(True)

    def _on_primary_clicked(self) -> None:
        status = self._task.status
        if status is TaskStatus.COMPLETED:
            self.open_file_requested.emit(self.task_id)
        elif status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.retry_requested.emit(self.task_id)
        else:
            self._primary_button.setEnabled(False)
            self._primary_button.setText(self.tr("Cancelando..."))
            self.cancel_requested.emit(self.task_id)

    def _on_secondary_clicked(self) -> None:
        if self._task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.remove_requested.emit(self.task_id)
        else:
            self.open_folder_requested.emit(self.task_id)
