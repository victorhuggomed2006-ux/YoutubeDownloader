"""Tests for settings and history persistence."""

from __future__ import annotations

import json
from pathlib import Path

from ytdownloader.core.formats import MediaKind
from ytdownloader.core.history import HistoryStore
from ytdownloader.core.models import (
    DownloadRequest,
    DownloadTask,
    HistoryEntry,
    TaskStatus,
)
from ytdownloader.core.settings import Settings, SettingsStore

# ── Settings ─────────────────────────────────────────────────────────────


def test_uses_defaults_when_there_is_no_file(tmp_path: Path) -> None:
    store = SettingsStore(path=tmp_path / "settings.json")
    assert store.settings.theme == "dark"
    assert store.settings.video_quality == "1080p"


def test_writes_and_reloads(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path=path)
    store.update(theme="light", video_quality="720p")

    reloaded = SettingsStore(path=path)
    assert reloaded.settings.theme == "light"
    assert reloaded.settings.video_quality == "720p"


def test_ignores_unknown_fields(tmp_path: Path) -> None:
    """A file written by a future version must not break an older one."""
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"theme": "light", "option_that_does_not_exist": 42}), encoding="utf-8"
    )
    store = SettingsStore(path=path)
    assert store.settings.theme == "light"


def test_migrates_the_cookie_value_written_by_1_2_0(tmp_path: Path) -> None:
    """The value used to be Portuguese; yt-dlp would read it as a browser name."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"cookies_from_browser": "nenhum"}), encoding="utf-8")
    assert SettingsStore(path=path).settings.cookies_from_browser == "none"


def test_the_migration_is_written_back_to_disk(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"cookies_from_browser": "nenhum"}), encoding="utf-8")
    SettingsStore(path=path)
    assert json.loads(path.read_text(encoding="utf-8"))["cookies_from_browser"] == "none"


def test_a_file_that_needs_nothing_is_left_alone(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    SettingsStore(path=path)
    assert path.read_text(encoding="utf-8") == before


def test_a_settings_file_with_a_bom_still_loads(tmp_path: Path) -> None:
    """Notepad and PowerShell write one; the file should not be discarded."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "light"}), encoding="utf-8-sig")
    assert SettingsStore(path=path).settings.theme == "light"


def test_corrupt_file_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{this is not json", encoding="utf-8")
    assert SettingsStore(path=path).settings.theme == "dark"


def test_output_dir_has_a_usable_value_when_empty() -> None:
    assert Settings().resolved_output_dir().name


def test_reset_restores_the_defaults(tmp_path: Path) -> None:
    store = SettingsStore(path=tmp_path / "settings.json")
    store.update(theme="light")
    store.reset()
    assert store.settings.theme == "dark"


# ── History ──────────────────────────────────────────────────────────────


def _entry(title: str = "Test video") -> HistoryEntry:
    return HistoryEntry(
        title=title,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        kind="video",
        quality="1080p",
        container="mp4",
        status="completed",
        size_bytes=1024,
    )


def test_history_keeps_newest_first(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.json")
    store.add(_entry("first"))
    store.add(_entry("second"))

    titles = [e.title for e in store.entries()]
    assert titles == ["second", "first"]


def test_history_survives_between_sessions(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    HistoryStore(path=path).add(_entry("stored"))
    assert [e.title for e in HistoryStore(path=path).entries()] == ["stored"]


def test_history_respects_its_limit(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.json", max_entries=3)
    for i in range(10):
        store.add(_entry(f"item {i}"))

    entries = store.entries()
    assert len(entries) == 3
    assert entries[0].title == "item 9"


def test_a_history_file_with_a_bom_still_loads(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    HistoryStore(path=path).add(_entry("stored"))
    path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8-sig")
    assert [e.title for e in HistoryStore(path=path).entries()] == ["stored"]


def test_history_clears(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.json")
    store.add(_entry())
    store.clear()
    assert store.entries() == []


def test_history_ignores_an_invalid_file(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")
    assert HistoryStore(path=path).entries() == []


def test_entry_from_a_finished_task(tmp_path: Path) -> None:
    file = tmp_path / "video.mp4"
    file.write_bytes(b"x" * 2048)

    task = DownloadTask(
        request=DownloadRequest(
            url="https://youtu.be/dQw4w9WgXcQ",
            kind=MediaKind.VIDEO,
            quality="720p",
            container="mp4",
            output_dir=tmp_path,
        ),
        status=TaskStatus.COMPLETED,
        output_file=file,
    )

    entry = HistoryEntry.from_task(task)
    assert entry.status == "completed"
    assert entry.size_bytes == 2048
    assert entry.file_path == str(file)


def test_entry_round_trips_through_a_dictionary() -> None:
    original = _entry()
    assert HistoryEntry.from_dict(original.to_dict()) == original
