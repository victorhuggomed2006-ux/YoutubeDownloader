"""The download history table."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.history import HistoryStore
from ...core.models import HistoryEntry
from ...core.urls import format_size


class HistoryView(QWidget):
    """Lists past downloads and lets the user open the files."""

    open_file_requested = Signal(str)

    def __init__(self, store: HistoryStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self._summary = QLabel()
        self._summary.setObjectName("Muted")
        header.addWidget(self._summary)
        header.addStretch(1)

        self._open_button = QPushButton(self.tr("Open file"))
        self._open_button.setObjectName("GhostButton")
        self._open_button.setEnabled(False)
        self._open_button.clicked.connect(self._emit_open_selected)
        header.addWidget(self._open_button)

        self._clear_button = QPushButton(self.tr("Clear history"))
        self._clear_button.setObjectName("DangerButton")
        self._clear_button.clicked.connect(self._clear)
        header.addWidget(self._clear_button)
        layout.addLayout(header)

        self._columns = (
            self.tr("When"),
            self.tr("Title"),
            self.tr("Kind"),
            self.tr("Quality"),
            self.tr("Size"),
            self.tr("Status"),
        )

        self._table = QTableWidget(0, len(self._columns))
        self._table.setHorizontalHeaderLabels(self._columns)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.setShowGrid(False)
        self._table.setWordWrap(False)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.itemDoubleClicked.connect(lambda _: self._emit_open_selected())

        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, len(self._columns)):
            header_view.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._table, 1)

        self._empty = QLabel(self.tr("No downloads recorded yet."))
        self._empty.setObjectName("EmptyState")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty)

        self.refresh()

    def _status_label(self, status: str) -> str:
        return {
            "completed": self.tr("Done"),
            "failed": self.tr("Failed"),
            "cancelled": self.tr("Cancelled"),
        }.get(status, status)

    # ── Data ─────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        entries = self._store.entries()
        self._table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            self._table.setItem(row, 0, self._make_item(_format_timestamp(entry.timestamp)))

            title_item = self._make_item(entry.title)
            title_item.setToolTip(entry.file_path or entry.url)
            title_item.setData(Qt.ItemDataRole.UserRole, entry.file_path)
            self._table.setItem(row, 1, title_item)

            kind = self.tr("Audio") if entry.kind == "audio" else self.tr("Video")
            self._table.setItem(row, 2, self._make_item(kind))

            quality = f"{entry.quality} kbps" if entry.kind == "audio" else entry.quality
            self._table.setItem(row, 3, self._make_item(quality))

            self._table.setItem(row, 4, self._make_item(format_size(entry.size_bytes)))

            status_item = self._make_item(self._status_label(entry.status))
            if entry.error:
                status_item.setToolTip(entry.error)
            self._table.setItem(row, 5, status_item)

        has_entries = bool(entries)
        self._table.setVisible(has_entries)
        self._empty.setVisible(not has_entries)
        self._clear_button.setEnabled(has_entries)
        self._summary.setText(
            self.tr("%n download(s)", "", len(entries)) if has_entries else self.tr("History empty")
        )
        self._on_selection_changed()

    @staticmethod
    def _make_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    # ── Actions ──────────────────────────────────────────────────────────

    def _selected_path(self) -> str:
        rows = self._table.selectionModel().selectedRows() if self._table.selectionModel() else []
        if not rows:
            return ""
        item = self._table.item(rows[0].row(), 1)
        if item is None:
            return ""
        return str(item.data(Qt.ItemDataRole.UserRole) or "")

    def _on_selection_changed(self) -> None:
        path = self._selected_path()
        self._open_button.setEnabled(bool(path) and Path(path).exists())

    def _emit_open_selected(self) -> None:
        path = self._selected_path()
        if path and Path(path).exists():
            self.open_file_requested.emit(path)

    def _clear(self) -> None:
        self._store.clear()
        self.refresh()

    def add_entry(self, entry: HistoryEntry) -> None:
        self._store.add(entry)
        self.refresh()


def _format_timestamp(raw: str) -> str:
    """Convert the stored UTC timestamp to local time, in a short format."""
    if not raw:
        return "--"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return raw[:16].replace("T", " ")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone().strftime("%d/%m/%Y %H:%M")
