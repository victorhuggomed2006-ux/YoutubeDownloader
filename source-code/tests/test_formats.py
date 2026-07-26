"""Tests for the format catalogue and the selectors handed to yt-dlp."""

from __future__ import annotations

import pytest

from ytdownloader.core.formats import (
    AUDIO_QUALITIES,
    VIDEO_QUALITIES,
    MediaKind,
    build_audio_format,
    build_format_sort,
    build_video_format,
    needs_ffmpeg,
    video_quality,
)


def test_video_quality_keys_are_unique() -> None:
    keys = [option.key for option in VIDEO_QUALITIES]
    assert len(keys) == len(set(keys))


def test_audio_quality_keys_are_numeric() -> None:
    for option in AUDIO_QUALITIES:
        assert option.key.isdigit()


@pytest.mark.parametrize(("key", "height"), [("1080p", 1080), ("720p", 720), ("360p", 360)])
def test_height_limit_reaches_the_selector(key: str, height: int) -> None:
    selector = build_video_format(key, "mp4")
    assert f"[height<={height}]" in selector
    assert selector.startswith("bestvideo")


def test_best_quality_imposes_no_limit() -> None:
    selector = build_video_format("best", "mp4")
    assert "height<=" not in selector


def test_selector_has_no_repeated_alternatives() -> None:
    """Without a height limit the alternatives collide; none may repeat."""
    selector = build_video_format("best", "mkv")
    parts = selector.split("/")
    assert len(parts) == len(set(parts))


def test_unknown_quality_falls_back_to_the_default() -> None:
    assert video_quality("8000p").key == VIDEO_QUALITIES[0].key


@pytest.mark.parametrize("container", ["mp4", "mkv", "webm"])
def test_selector_always_ends_with_a_fallback(container: str) -> None:
    selector = build_video_format("1080p", container)
    assert selector.split("/")[-1] == "best"


def test_mp4_prefers_h264_for_compatibility() -> None:
    order = build_format_sort("mp4")
    assert order[0] == "vcodec:h264"
    assert "acodec:aac" in order


def test_other_containers_prioritise_resolution() -> None:
    assert build_format_sort("mkv")[0] == "res"


def test_audio_selector() -> None:
    assert build_audio_format() == "bestaudio/best"


@pytest.mark.parametrize(
    ("kind", "container", "expected"),
    [
        (MediaKind.AUDIO, "mp3", True),
        (MediaKind.AUDIO, "wav", True),
        (MediaKind.AUDIO, "m4a", False),  # native format, no conversion needed
        (MediaKind.VIDEO, "mp4", True),  # merging video and audio needs FFmpeg
        (MediaKind.VIDEO, "mkv", True),
    ],
)
def test_when_ffmpeg_is_required(kind: MediaKind, container: str, expected: bool) -> None:
    assert needs_ffmpeg(kind, container) is expected
