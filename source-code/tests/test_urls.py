"""Tests for address validation and normalisation."""

from __future__ import annotations

import pytest

from ytdownloader.core.urls import (
    format_duration,
    format_eta,
    format_size,
    format_speed,
    is_supported_url,
    parse_url,
)

VIDEO_ID = "dQw4w9WgXcQ"


# ── YouTube ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com/watch?v={VIDEO_ID}",
        f"http://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://music.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?t=42",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}",
        f"youtube.com/watch?v={VIDEO_ID}",  # no scheme, as people paste it
        f"  https://youtu.be/{VIDEO_ID}  ",  # surrounded by whitespace
    ],
)
def test_extracts_video_id(url: str) -> None:
    parsed = parse_url(url)
    assert parsed.is_supported
    assert parsed.is_youtube
    assert parsed.video_id == VIDEO_ID
    assert parsed.canonical == f"https://www.youtube.com/watch?v={VIDEO_ID}"


def test_plain_playlist() -> None:
    parsed = parse_url("https://www.youtube.com/playlist?list=PLabc123def")
    assert parsed.is_supported
    assert parsed.is_playlist
    assert parsed.playlist_id == "PLabc123def"
    assert parsed.video_id is None
    assert parsed.canonical == "https://www.youtube.com/playlist?list=PLabc123def"


def test_video_inside_playlist_downloads_only_the_video() -> None:
    parsed = parse_url(f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PLabc123")
    assert parsed.video_id == VIDEO_ID
    assert parsed.playlist_id == "PLabc123"
    assert not parsed.is_playlist  # the video wins over the list


def test_youtube_mix_is_not_treated_as_a_playlist() -> None:
    parsed = parse_url(f"https://www.youtube.com/watch?v={VIDEO_ID}&list=RD{VIDEO_ID}")
    assert parsed.video_id == VIDEO_ID
    assert parsed.playlist_id is None


def test_thumbnail_url_exists_only_for_youtube() -> None:
    assert parse_url(f"https://youtu.be/{VIDEO_ID}").thumbnail_url == (
        f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg"
    )
    assert parse_url("https://vimeo.com/123456").thumbnail_url is None


def test_youtube_address_without_a_video_is_useless() -> None:
    """The home page and the search page point at nothing downloadable."""
    assert not parse_url("https://www.youtube.com/").is_supported
    assert not parse_url("https://www.youtube.com/results?search_query=test").is_supported
    assert not parse_url("https://www.youtube.com/watch?v=short").is_supported


# ── Other sites ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("url", "name"),
    [
        ("https://vimeo.com/123456", "Vimeo"),
        ("https://www.twitch.tv/videos/123", "Twitch"),
        ("https://soundcloud.com/artist/track", "SoundCloud"),
        ("https://www.dailymotion.com/video/x8abc", "Dailymotion"),
        ("https://x.com/user/status/123", "X"),
        ("https://www.reddit.com/r/videos/comments/abc/title/", "Reddit"),
        ("https://artist.bandcamp.com/track/song", "Bandcamp"),
    ],
)
def test_accepts_other_sites_and_names_them(url: str, name: str) -> None:
    parsed = parse_url(url)
    assert parsed.is_supported
    assert not parsed.is_youtube
    assert parsed.site_name == name


def test_unknown_site_is_accepted_with_its_domain_as_the_name() -> None:
    """yt-dlp decides what it supports, not this validation."""
    parsed = parse_url("https://www.some-obscure-video-site.co.uk/watch/123")
    assert parsed.is_supported
    assert parsed.site_name == "some-obscure-video-site.co.uk"


def test_other_site_addresses_are_not_rewritten() -> None:
    """Every site has its own conventions; rewriting would break the link."""
    url = "https://vimeo.com/123456?parameter=matters"
    assert parse_url(url).canonical == url


def test_address_without_scheme_gets_https() -> None:
    assert parse_url("vimeo.com/123456").canonical == "https://vimeo.com/123456"


# ── Rejections ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "not a url",
        "javascript:alert(1)",
        "file:///C:/Windows/System32/config/SAM",
        "ftp://example.com/video.mp4",
        "data:text/html,<script>alert(1)</script>",
        "http://",
        "https://nodomain",  # no dot: not a public host
        "https://-invalid-.com",
    ],
)
def test_rejects_invalid_or_dangerous_addresses(url: str) -> None:
    assert not parse_url(url).is_supported
    assert not is_supported_url(url)


def test_rejects_non_http_schemes() -> None:
    """http and https only: the rest have no business in a downloader."""
    for scheme in ("file", "ftp", "javascript", "data", "smb"):
        assert not is_supported_url(f"{scheme}://example.com/thing")


# ── Formatting ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (None, "--:--"),
        (0, "--:--"),
        (-5, "--:--"),
        (45, "00:45"),
        (60, "01:00"),
        (599, "09:59"),
        (3600, "1:00:00"),
        (3725, "1:02:05"),
        (86399, "23:59:59"),
    ],
)
def test_formats_duration(seconds, expected: str) -> None:
    assert format_duration(seconds) == expected


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (None, "--"),
        (0, "--"),
        (512, "512 B"),
        (2048, "2 KB"),
        (15 * 1024 * 1024, "15.0 MB"),
        (3 * 1024 * 1024 * 1024, "3.0 GB"),
    ],
)
def test_formats_size(size, expected: str) -> None:
    assert format_size(size) == expected


def test_formats_speed_and_time_left() -> None:
    assert format_speed(1024 * 1024) == "1.0 MB/s"
    assert format_speed(None) == "--"
    assert format_eta(90) == "01:30"
    assert format_eta(None) == "--"
