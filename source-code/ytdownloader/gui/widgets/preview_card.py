"""Cartão que mostra os dados do vídeo antes do download."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ...core.models import VideoInfo
from ...core.urls import format_duration

THUMB_WIDTH = 160
THUMB_HEIGHT = 90

#: Separador visual entre canal, duração e demais informações.
SEPARADOR = "  ·  "


class PreviewCard(QFrame):
    """Miniatura, título, canal e duração do vídeo consultado."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewCard")
        self.setVisible(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 14, 12)
        layout.setSpacing(14)

        self._thumb = QLabel()
        self._thumb.setObjectName("Thumb")
        self._thumb.setFixedSize(THUMB_WIDTH, THUMB_HEIGHT)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setScaledContents(False)
        layout.addWidget(self._thumb)

        text_column = QVBoxLayout()
        text_column.setSpacing(5)
        text_column.setContentsMargins(0, 2, 0, 2)

        self._title = QLabel()
        self._title.setObjectName("PreviewTitle")
        self._title.setWordWrap(True)
        self._title.setMaximumHeight(46)
        text_column.addWidget(self._title)

        self._meta = QLabel()
        self._meta.setObjectName("PreviewMeta")
        self._meta.setWordWrap(True)
        text_column.addWidget(self._meta)

        text_column.addStretch(1)
        layout.addLayout(text_column, 1)

    # ── Estados ──────────────────────────────────────────────────────────

    def show_loading(self) -> None:
        self.setVisible(True)
        self._thumb.clear()
        self._thumb.setText("...")
        self._title.setText(self.tr("Consultando o vídeo..."))
        self._meta.setText("")

    def show_info(self, info: VideoInfo) -> None:
        self.setVisible(True)
        self._title.setText(info.title)

        parts: list[str] = []
        if info.uploader:
            parts.append(info.uploader)
        if info.duration:
            parts.append(format_duration(info.duration))
        if info.is_live:
            parts.append(self.tr("AO VIVO"))
        self._meta.setText(SEPARADOR.join(parts) if parts else "")

        if not self._thumb.pixmap() or self._thumb.pixmap().isNull():
            self._thumb.setText("")

    def show_error(self, message: str) -> None:
        self.setVisible(True)
        self._thumb.clear()
        self._thumb.setText("!")
        self._title.setText(self.tr("Não foi possível ler o vídeo"))
        self._meta.setText(message)

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
        # Recorta o excedente para preencher a área sem distorcer a imagem.
        x = max(0, (scaled.width() - THUMB_WIDTH) // 2)
        y = max(0, (scaled.height() - THUMB_HEIGHT) // 2)
        self._thumb.setText("")
        self._thumb.setPixmap(scaled.copy(x, y, THUMB_WIDTH, THUMB_HEIGHT))

    def clear(self) -> None:
        self.setVisible(False)
        self._thumb.clear()
        self._thumb.setText("")
        self._title.setText("")
        self._meta.setText("")
