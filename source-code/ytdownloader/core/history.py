"""Download history, stored as JSON."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from . import paths
from .models import HistoryEntry

logger = logging.getLogger(__name__)

MAX_ENTRIES = 500


class HistoryStore:
    """The most recent downloads, newest first."""

    def __init__(self, path: Path | None = None, max_entries: int = MAX_ENTRIES) -> None:
        self._path = path or paths.history_file()
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._entries: list[HistoryEntry] = self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> list[HistoryEntry]:
        if not self._path.exists():
            return []
        try:
            # utf-8-sig for the same reason as the settings: a hand-edited file
            # may carry a BOM, and that should not throw the history away.
            raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read the history (%s); starting empty.", exc)
            return []

        if not isinstance(raw, list):
            return []

        entries: list[HistoryEntry] = []
        for item in raw:
            if isinstance(item, dict):
                try:
                    entries.append(HistoryEntry.from_dict(item))
                except (TypeError, ValueError):
                    continue
        return entries[: self._max_entries]

    def _save_locked(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temp = self._path.with_suffix(".tmp")
            temp.write_text(
                json.dumps([e.to_dict() for e in self._entries], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            temp.replace(self._path)
        except OSError as exc:
            logger.error("Failed to save the history: %s", exc)

    def add(self, entry: HistoryEntry) -> None:
        with self._lock:
            self._entries.insert(0, entry)
            del self._entries[self._max_entries :]
            self._save_locked()

    def entries(self) -> list[HistoryEntry]:
        with self._lock:
            return list(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._save_locked()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
