"""Tests for the download engine.

Nothing here touches the network: what is checked is how the options are put
together before being handed to yt-dlp, and how the final file is located
afterwards.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from ytdownloader.core import ffmpeg as ffmpeg_module
from ytdownloader.core.downloader import Downloader
from ytdownloader.core.errors import DownloaderError, FFmpegMissingError
from ytdownloader.core.formats import MediaKind
from ytdownloader.core.models import DownloadRequest


@pytest.fixture
def request_(tmp_path: Path) -> DownloadRequest:
    return DownloadRequest(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        kind=MediaKind.VIDEO,
        quality="1080p",
        container="mp4",
        output_dir=tmp_path,
    )


def _options(downloader: Downloader, request: DownloadRequest) -> dict:
    return downloader._download_options(request, lambda _: None, lambda _: None)


# ── Building the options ─────────────────────────────────────────────────


def test_output_template_is_relative(request_: DownloadRequest) -> None:
    """Regression: with an absolute outtmpl the long-name trim cut the whole
    path, and the file came out named after a fragment of the directory."""
    options = _options(Downloader(), request_)
    assert options["outtmpl"] == "%(title)s.%(ext)s"
    assert not Path(options["outtmpl"]).is_absolute()
    assert options["paths"]["home"] == str(request_.output_dir)


def test_name_trim_coexists_with_the_directory(request_: DownloadRequest) -> None:
    options = _options(Downloader(), request_)
    assert options["trim_file_name"] == 120
    assert options["windowsfilenames"] is True


def test_video_asks_for_h264_for_compatibility(request_: DownloadRequest) -> None:
    options = _options(Downloader(), request_)
    assert options["format_sort"][0] == "vcodec:h264"
    assert options["merge_output_format"] == "mp4"
    assert "[height<=1080]" in options["format"]


def test_audio_converts_to_the_chosen_codec(request_: DownloadRequest) -> None:
    request = DownloadRequest(
        url=request_.url,
        kind=MediaKind.AUDIO,
        quality="320",
        container="mp3",
        output_dir=request_.output_dir,
    )
    options = _options(Downloader(), request)

    extractors = [p for p in options["postprocessors"] if p["key"] == "FFmpegExtractAudio"]
    assert len(extractors) == 1
    assert extractors[0]["preferredcodec"] == "mp3"
    assert extractors[0]["preferredquality"] == "320"
    assert "format_sort" not in options  # only meaningful for video


def test_m4a_audio_is_not_reconverted(request_: DownloadRequest) -> None:
    """M4A is the native format sites deliver; reconverting only loses quality
    and time."""
    request = DownloadRequest(
        url=request_.url,
        kind=MediaKind.AUDIO,
        quality="192",
        container="m4a",
        output_dir=request_.output_dir,
    )
    options = _options(Downloader(), request)
    keys = [p["key"] for p in options.get("postprocessors", [])]
    assert "FFmpegExtractAudio" not in keys


def test_subtitles_only_when_asked_for(request_: DownloadRequest) -> None:
    assert "writesubtitles" not in _options(Downloader(), request_)

    with_subtitles = DownloadRequest(
        url=request_.url,
        kind=MediaKind.VIDEO,
        quality="720p",
        container="mp4",
        output_dir=request_.output_dir,
        write_subtitles=True,
    )
    options = _options(Downloader(), with_subtitles)
    assert options["writesubtitles"] is True
    assert "FFmpegEmbedSubtitle" in [p["key"] for p in options["postprocessors"]]


def test_cookies_only_sent_when_a_browser_is_chosen(request_: DownloadRequest) -> None:
    assert "cookiesfrombrowser" not in _options(Downloader("none"), request_)
    assert _options(Downloader("firefox"), request_)["cookiesfrombrowser"] == ("firefox",)


def test_quality_inconsistent_with_the_kind_is_corrected(tmp_path: Path) -> None:
    """Switching from video to audio must not leave "1080p" as a bitrate."""
    request = DownloadRequest(
        url="https://youtu.be/dQw4w9WgXcQ",
        kind=MediaKind.AUDIO,
        quality="1080p",
        container="mp4",
        output_dir=tmp_path,
    ).normalized()
    assert request.quality == "192"
    assert request.container == "mp3"


# ── Locating the final file ──────────────────────────────────────────────


def test_finds_the_file_yt_dlp_reported(tmp_path: Path, request_: DownloadRequest) -> None:
    file = tmp_path / "Video.mp4"
    file.write_bytes(b"x")
    info = {"requested_downloads": [{"filepath": str(file)}]}
    assert Downloader._resolve_output_file(info, tmp_path, request_) == file


def test_follows_the_extension_change_after_conversion(tmp_path: Path) -> None:
    """yt-dlp reports the name before post-processing; after conversion the
    extension changes and the original path no longer exists."""
    request = DownloadRequest(
        url="https://youtu.be/x",
        kind=MediaKind.AUDIO,
        quality="192",
        container="mp3",
        output_dir=tmp_path,
    )
    converted = tmp_path / "Song.mp3"
    converted.write_bytes(b"x")
    info = {"requested_downloads": [{"filepath": str(tmp_path / "Song.webm")}]}
    assert Downloader._resolve_output_file(info, tmp_path, request) == converted


def test_falls_back_to_the_newest_file(tmp_path: Path, request_: DownloadRequest) -> None:
    newest = tmp_path / "Other.mp4"
    newest.write_bytes(b"x")
    assert Downloader._resolve_output_file({}, tmp_path, request_) == newest


def test_returns_nothing_when_there_is_no_file(tmp_path: Path, request_: DownloadRequest) -> None:
    assert Downloader._resolve_output_file({}, tmp_path, request_) is None


# ── Validation and preconditions ─────────────────────────────────────────


@pytest.mark.parametrize("url", ["", "not a url", "file:///C:/Windows", "javascript:alert(1)"])
def test_lookup_rejects_invalid_addresses(url: str) -> None:
    with pytest.raises(DownloaderError):
        Downloader().fetch_info(url)


def test_video_without_ffmpeg_fails_before_downloading(
    monkeypatch: pytest.MonkeyPatch, request_: DownloadRequest
) -> None:
    """Merging video and audio needs FFmpeg. Better to say so now than to
    download hundreds of megabytes and fail at the end."""
    monkeypatch.setattr(ffmpeg_module, "is_available", lambda: False)
    with pytest.raises(FFmpegMissingError):
        Downloader().download(request_)


def test_cancelling_before_the_start_downloads_nothing(
    monkeypatch: pytest.MonkeyPatch, request_: DownloadRequest
) -> None:
    monkeypatch.setattr(ffmpeg_module, "is_available", lambda: True)
    cancelled = threading.Event()
    cancelled.set()

    from ytdownloader.core.errors import DownloadCancelled

    with pytest.raises(DownloadCancelled):
        Downloader().download(request_, cancel_event=cancelled)
