"""Validation and normalisation of the addresses the application accepts.

yt-dlp extracts video from over a thousand sites, so validation accepts any
http/https address. YouTube still gets dedicated handling — identifier
extraction, playlist detection and a predictable thumbnail — because it is the
common case and lets the preview show up before the network is even touched.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "gaming.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}

#: Sites with a known name, for display purposes only.
KNOWN_SITES = {
    "vimeo.com": "Vimeo",
    "twitch.tv": "Twitch",
    "soundcloud.com": "SoundCloud",
    "dailymotion.com": "Dailymotion",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "twitter.com": "X",
    "x.com": "X",
    "reddit.com": "Reddit",
    "bandcamp.com": "Bandcamp",
    "bitchute.com": "BitChute",
    "odysee.com": "Odysee",
    "rumble.com": "Rumble",
    "globoplay.globo.com": "Globoplay",
}

# YouTube video IDs are exactly 11 characters from the base64-url alphabet.
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{2,}$")

# YouTube paths that carry the identifier in the path itself.
PATH_PREFIXES = ("/shorts/", "/embed/", "/live/", "/v/")

SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
HOST_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)+$"
)


@dataclass(frozen=True)
class ParsedUrl:
    """The result of parsing an address the user pasted."""

    original: str
    host: str = ""
    video_id: str | None = None
    playlist_id: str | None = None
    is_youtube: bool = False
    is_supported: bool = False

    @property
    def is_valid(self) -> bool:
        return self.is_supported

    @property
    def is_playlist(self) -> bool:
        """A playlist to expand: only when no specific video was given."""
        return self.playlist_id is not None and self.video_id is None

    @property
    def canonical(self) -> str:
        """The address stripped of tracking parameters.

        Outside YouTube the address comes back as it went in: every site has
        its own conventions, and rewriting it here would break links.
        """
        if self.video_id:
            return f"https://www.youtube.com/watch?v={self.video_id}"
        if self.playlist_id and self.is_youtube:
            return f"https://www.youtube.com/playlist?list={self.playlist_id}"
        return _with_scheme(self.original)

    @property
    def thumbnail_url(self) -> str | None:
        """YouTube's predictable thumbnail, shown before the network call."""
        if not self.video_id:
            return None
        return f"https://i.ytimg.com/vi/{self.video_id}/hqdefault.jpg"

    @property
    def site_name(self) -> str:
        """The site name for display, or the domain itself."""
        if self.is_youtube:
            return "YouTube"
        host = self.host.removeprefix("www.")
        for domain, name in KNOWN_SITES.items():
            if host == domain or host.endswith("." + domain):
                return name
        return host


def _with_scheme(url: str) -> str:
    """Fill in the scheme when the user pastes an address without one."""
    url = (url or "").strip()
    if not url:
        return ""
    if not SCHEME_RE.match(url):
        url = "https://" + url
    return url


def parse_url(url: str) -> ParsedUrl:
    """Parse the address and extract whatever is available."""
    raw = (url or "").strip()
    cleaned = _with_scheme(raw)
    if not cleaned:
        return ParsedUrl(original=raw)

    try:
        parsed = urlparse(cleaned)
    except ValueError:
        return ParsedUrl(original=raw)

    # http and https only: file://, javascript: and friends have no business here.
    if parsed.scheme not in ("http", "https"):
        return ParsedUrl(original=raw)

    host = (parsed.hostname or "").lower()
    if not host or not HOST_RE.match(host):
        return ParsedUrl(original=raw)

    is_youtube = host in YOUTUBE_HOSTS
    if not is_youtube:
        # Any other site is left to yt-dlp, which knows what it supports.
        return ParsedUrl(original=raw, host=host, is_supported=True)

    query = parse_qs(parsed.query)
    path = parsed.path or "/"

    video_id = _extract_video_id(host, path, query)
    playlist_id = _extract_playlist_id(query)

    # A YouTube address is only useful if it points at a video or a playlist.
    supported = bool(video_id or playlist_id)

    return ParsedUrl(
        original=raw,
        host=host,
        video_id=video_id,
        playlist_id=playlist_id,
        is_youtube=True,
        is_supported=supported,
    )


def _extract_video_id(host: str, path: str, query: dict[str, list[str]]) -> str | None:
    values = query.get("v") or []
    if values and VIDEO_ID_RE.match(values[0]):
        return values[0]

    if host.endswith("youtu.be"):
        candidate = path.lstrip("/").split("/")[0]
        if VIDEO_ID_RE.match(candidate):
            return candidate

    for prefix in PATH_PREFIXES:
        if path.startswith(prefix):
            candidate = path[len(prefix) :].split("/")[0]
            if VIDEO_ID_RE.match(candidate):
                return candidate
            break

    return None


def _extract_playlist_id(query: dict[str, list[str]]) -> str | None:
    values = query.get("list") or []
    if not values or not PLAYLIST_ID_RE.match(values[0]):
        return None
    # "RD..." are endless mixes generated by YouTube, not real playlists.
    if values[0].startswith("RD"):
        return None
    return values[0]


def is_supported_url(url: str) -> bool:
    """Boolean shortcut used while the user is typing."""
    return parse_url(url).is_supported


def format_duration(seconds: float | int | None) -> str:
    """Format a duration in seconds as ``mm:ss`` or ``h:mm:ss``."""
    if not seconds or seconds < 0:
        return "--:--"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_size(num_bytes: float | int | None) -> str:
    """Format a size in bytes in a readable way."""
    if not num_bytes or num_bytes <= 0:
        return "--"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            precision = 0 if unit in ("B", "KB") else 1
            return f"{size:.{precision}f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_speed(bytes_per_second: float | int | None) -> str:
    if not bytes_per_second or bytes_per_second <= 0:
        return "--"
    return f"{format_size(bytes_per_second)}/s"


def format_eta(seconds: float | int | None) -> str:
    if seconds is None or seconds < 0:
        return "--"
    return format_duration(seconds)
