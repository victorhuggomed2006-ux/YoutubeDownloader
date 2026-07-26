"""Tests for turning yt-dlp errors into messages people can act on."""

from __future__ import annotations

import pytest

from ytdownloader.core.errors import (
    DownloadCancelled,
    DownloaderError,
    FFmpegMissingError,
    clean_message,
    humanize,
)


def test_strips_colour_codes_and_prefixes() -> None:
    raw = "\x1b[0;31mERROR:\x1b[0m [youtube] abc: Video unavailable"
    assert clean_message(raw) == "abc: Video unavailable"


@pytest.mark.parametrize(
    ("raw", "expected_fragment"),
    [
        ("ERROR: Sign in to confirm you're not a bot", "account verification"),
        ("ERROR: Private video. Sign in if you've been granted access", "private"),
        ("ERROR: Video unavailable", "unavailable"),
        ("ERROR: This video has been removed by the uploader", "unavailable"),
        ("ERROR: This video is age-restricted", "age-restricted"),
        ("ERROR: Join this channel to get access to members-only content", "members"),
        ("ERROR: The uploader has not made this video available in your country", "region"),
        ("ERROR: Requested format is not available", "selected quality"),
        ("ERROR: unable to download video data: timed out", "Connection failed"),
        ("ERROR: ffprobe/ffmpeg not found", "FFmpeg"),
        ("[Errno 13] Permission denied: 'C:/x'", "permission"),
        ("OSError: [Errno 28] No space left on device", "disk space"),
    ],
)
def test_translates_known_errors(raw: str, expected_fragment: str) -> None:
    error = humanize(raw)
    assert isinstance(error, DownloaderError)
    assert expected_fragment.lower() in str(error).lower()


def test_bot_check_suggests_cookies() -> None:
    error = humanize("ERROR: Sign in to confirm you're not a bot")
    assert "cookie" in error.hint.lower()


def test_unknown_error_becomes_a_short_message() -> None:
    error = humanize("ERROR: something very specific went wrong\nextra line ignored")
    assert "extra line" not in str(error)
    assert "something very specific" in str(error)


def test_empty_message_has_a_default() -> None:
    assert str(humanize("")) == "The download could not be completed."


def test_very_long_text_is_truncated() -> None:
    assert len(str(humanize("x" * 900))) <= 230


def test_already_handled_error_passes_through() -> None:
    original = DownloaderError("ready-made message")
    assert humanize(original) is original


def test_cancellation_and_ffmpeg_errors_have_their_own_message() -> None:
    assert "cancelled" in str(DownloadCancelled()).lower()
    assert "ffmpeg" in str(FFmpegMissingError()).lower()
