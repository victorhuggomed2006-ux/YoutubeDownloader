"""Tests for the yt-dlp update mechanism.

This is the most sensitive module in the project: it downloads a package from
the internet and puts it on ``sys.path``, from where the code will be imported
and executed. These tests exist above all to keep the defences in place.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from ytdownloader.core import paths, updater


@pytest.fixture(autouse=True)
def isolated_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keep the real user folder out of the tests."""
    destination = tmp_path / "runtime"
    destination.mkdir()
    monkeypatch.setattr(paths, "runtime_dir", lambda: destination)
    return destination


def _wheel(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buffer.getvalue()


def _valid_wheel() -> bytes:
    return _wheel(
        {
            "yt_dlp/__init__.py": "__version__ = '2030.1.1'\n",
            "yt_dlp/version.py": "__version__ = '2030.1.1'\n",
        }
    )


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def iter_content(self, chunk_size: int = 8192):
        for i in range(0, len(self._payload), chunk_size):
            yield self._payload[i : i + chunk_size]


def _fake_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
    import requests

    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(payload))


# ── Version comparison ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026.7.4", (2026, 7, 4)),
        ("2026.07.04", (2026, 7, 4)),
        ("1.0", (1, 0)),
        ("", (0,)),
        ("not-a-version", (0,)),
    ],
)
def test_parses_versions(text: str, expected: tuple) -> None:
    assert updater.parse_version(text) == expected


def test_version_order_is_numeric_not_alphabetical() -> None:
    """Compared as text, "2026.10.1" would come before "2026.9.1"."""
    assert updater.parse_version("2026.10.1") > updater.parse_version("2026.9.1")
    assert updater.parse_version("2027.1.1") > updater.parse_version("2026.12.31")


# ── Installation ─────────────────────────────────────────────────────────


def test_installs_and_leaves_a_usable_package(
    monkeypatch: pytest.MonkeyPatch, isolated_folder: Path
) -> None:
    payload = _valid_wheel()
    _fake_download(monkeypatch, payload)
    digest = hashlib.sha256(payload).hexdigest()

    destination = updater.install("2030.1.1", "https://example/package.whl", digest)

    assert destination.is_dir()
    assert (destination / "yt_dlp" / "__init__.py").is_file()
    assert destination.parent == isolated_folder


def test_rejects_a_package_with_the_wrong_checksum(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without this check, anything the network returned would be imported."""
    _fake_download(monkeypatch, _valid_wheel())

    with pytest.raises(RuntimeError, match="integrity"):
        updater.install("2030.1.1", "https://example/package.whl", "0" * 64)


def test_rejects_a_package_that_escapes_the_destination(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Zip Slip: a member with ".." in its path would overwrite files outside
    the destination folder, including the application's own executable."""
    malicious = _wheel(
        {
            "yt_dlp/__init__.py": "",
            "../../../evil.py": "print('pwned')",
        }
    )
    _fake_download(monkeypatch, malicious)

    with pytest.raises(RuntimeError, match="invalid paths"):
        updater.install("2030.1.1", "https://example/package.whl", "")

    assert not (tmp_path.parent / "evil.py").exists()


def test_rejects_a_package_without_yt_dlp_inside(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_download(monkeypatch, _wheel({"something_else/__init__.py": ""}))

    with pytest.raises(RuntimeError, match="does not contain yt-dlp"):
        updater.install("2030.1.1", "https://example/package.whl", "")


def test_rejects_an_oversized_package(monkeypatch: pytest.MonkeyPatch) -> None:
    """A compromised server must not be able to fill the user's disk."""
    _fake_download(monkeypatch, b"x" * (updater.MAX_WHEEL_BYTES + 1024))

    with pytest.raises(RuntimeError, match="larger than expected"):
        updater.install("2030.1.1", "https://example/package.whl", "")


def test_a_failed_install_leaves_nothing_behind(
    monkeypatch: pytest.MonkeyPatch, isolated_folder: Path
) -> None:
    _fake_download(monkeypatch, _wheel({"nothing/__init__.py": ""}))

    with pytest.raises(RuntimeError):
        updater.install("2030.1.1", "https://example/package.whl", "")

    assert list(isolated_folder.iterdir()) == []


# ── Activation ───────────────────────────────────────────────────────────


def test_with_nothing_installed_the_bundled_copy_is_used() -> None:
    assert updater.activate() is None


def test_does_not_swap_the_engine_once_yt_dlp_is_imported(
    monkeypatch: pytest.MonkeyPatch, isolated_folder: Path
) -> None:
    """Changing sys.path after the import would have no effect and would
    falsely suggest the update is in use."""
    import sys

    (isolated_folder / "yt_dlp-2030.1.1" / "yt_dlp").mkdir(parents=True)
    (isolated_folder / "yt_dlp-2030.1.1" / "yt_dlp" / "__init__.py").write_text("")

    monkeypatch.setitem(sys.modules, "yt_dlp", object())
    assert updater.activate() is None


def test_always_picks_the_newest_version(
    monkeypatch: pytest.MonkeyPatch, isolated_folder: Path
) -> None:
    import sys

    for version in ("2026.1.1", "2026.10.1", "2026.9.1"):
        folder = isolated_folder / f"yt_dlp-{version}" / "yt_dlp"
        folder.mkdir(parents=True)
        (folder / "__init__.py").write_text("")

    monkeypatch.delitem(sys.modules, "yt_dlp", raising=False)
    original_path = list(sys.path)
    try:
        assert updater.activate() == "2026.10.1"
        assert str(isolated_folder / "yt_dlp-2026.10.1") == sys.path[0]
    finally:
        sys.path[:] = original_path


def test_ignores_a_folder_without_the_package_inside(
    monkeypatch: pytest.MonkeyPatch, isolated_folder: Path
) -> None:
    """An interrupted install leaves a half-written folder; it must not be
    picked over the bundled copy, which works."""
    import sys

    (isolated_folder / "yt_dlp-2030.1.1").mkdir()  # without the yt_dlp subfolder
    monkeypatch.delitem(sys.modules, "yt_dlp", raising=False)

    original_path = list(sys.path)
    try:
        assert updater.activate() is None
    finally:
        sys.path[:] = original_path


# ── Querying the package index ───────────────────────────────────────────


def test_available_version_is_compared_with_the_current_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(updater, "current_version", lambda: "2026.1.1")
    monkeypatch.setattr(
        updater, "latest_version", lambda: ("2026.7.4", "https://example/p.whl", "abc")
    )
    assert updater.update_available() == "2026.7.4"

    monkeypatch.setattr(updater, "current_version", lambda: "2026.7.4")
    assert updater.update_available() is None


def test_an_unreachable_index_does_not_break_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    import requests

    def explode(*a, **k):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", explode)
    assert updater.latest_version() is None
    assert updater.update_available() is None


def test_rejects_a_strangely_formatted_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only numeric versions are accepted; anything else coming back from the
    API is treated as an invalid response."""
    import requests

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "info": {"version": "1.0.0-beta; rm -rf /"},
                "urls": [
                    {
                        "packagetype": "bdist_wheel",
                        "filename": "x-py3-none-any.whl",
                        "url": "u",
                    }
                ],
            }

    monkeypatch.setattr(requests, "get", lambda *a, **k: Response())
    assert updater.latest_version() is None
