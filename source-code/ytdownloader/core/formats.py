"""The catalogue of formats and qualities offered to the user."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MediaKind(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


@dataclass(frozen=True)
class QualityOption:
    """A quality choice as shown in the interface."""

    key: str
    label: str
    description: str
    max_height: int | None = None


VIDEO_QUALITIES: tuple[QualityOption, ...] = (
    QualityOption("best", "Best available", "The highest resolution the video offers"),
    QualityOption("2160p", "4K · 2160p", "Very large files", 2160),
    QualityOption("1440p", "QHD · 1440p", "High quality", 1440),
    QualityOption("1080p", "Full HD · 1080p", "Best balance of quality and size", 1080),
    QualityOption("720p", "HD · 720p", "Light and plays everywhere", 720),
    QualityOption("480p", "SD · 480p", "Saves space", 480),
    QualityOption("360p", "Low · 360p", "Smallest possible file", 360),
)

AUDIO_QUALITIES: tuple[QualityOption, ...] = (
    QualityOption("320", "320 kbps", "Top audio quality"),
    QualityOption("256", "256 kbps", "High quality"),
    QualityOption("192", "192 kbps", "Recommended default"),
    QualityOption("128", "128 kbps", "Smaller file"),
)

AUDIO_CONTAINERS: tuple[str, ...] = ("mp3", "m4a", "opus", "wav", "flac")
VIDEO_CONTAINERS: tuple[str, ...] = ("mp4", "mkv", "webm")

DEFAULT_VIDEO_QUALITY = "1080p"
DEFAULT_AUDIO_QUALITY = "192"
DEFAULT_AUDIO_CONTAINER = "mp3"
DEFAULT_VIDEO_CONTAINER = "mp4"


def video_quality(key: str) -> QualityOption:
    for option in VIDEO_QUALITIES:
        if option.key == key:
            return option
    return VIDEO_QUALITIES[0]


def audio_quality(key: str) -> QualityOption:
    for option in AUDIO_QUALITIES:
        if option.key == key:
            return option
    return audio_quality_default()


def audio_quality_default() -> QualityOption:
    for option in AUDIO_QUALITIES:
        if option.key == DEFAULT_AUDIO_QUALITY:
            return option
    return AUDIO_QUALITIES[0]


def build_video_format(quality_key: str, container: str = DEFAULT_VIDEO_CONTAINER) -> str:
    """Build the yt-dlp format selector for a video download.

    The chain tries, in order: separate streams in the preferred container,
    separate streams in any container, and finally an already-merged file. That
    way the download does not fail when a video lacks the ideal combination.
    """
    option = video_quality(quality_key)
    height = option.max_height

    limit = "" if height is None else f"[height<={height}]"

    if container == "mp4":
        preferred = f"bestvideo{limit}[ext=mp4]+bestaudio[ext=m4a]"
    elif container == "webm":
        preferred = f"bestvideo{limit}[ext=webm]+bestaudio[ext=webm]"
    else:  # mkv takes any combination
        preferred = f"bestvideo{limit}+bestaudio"

    chain = [preferred, f"bestvideo{limit}+bestaudio", f"best{limit}", "best"]

    # Without a height limit the alternatives collide; keep the first of each.
    unique: list[str] = []
    for item in chain:
        if item not in unique:
            unique.append(item)
    return "/".join(unique)


def build_format_sort(container: str) -> list[str]:
    """Tie-breakers between otherwise equivalent formats.

    MP4 prefers H.264 and AAC: YouTube usually offers AV1 at the same
    resolution, which produces smaller files but does not play on older devices
    and TVs. MKV and WebM do not carry that constraint, so the best available
    compression wins there.
    """
    if container == "mp4":
        return ["vcodec:h264", "acodec:aac", "res", "fps"]
    return ["res", "fps"]


def build_audio_format() -> str:
    """The yt-dlp format selector for an audio-only download."""
    return "bestaudio/best"


def needs_ffmpeg(kind: MediaKind, container: str) -> bool:
    """Whether the chosen combination requires FFmpeg.

    Audio always goes through conversion, except for ``m4a``, which is usually
    the native format the site already delivers. Video needs FFmpeg to merge
    the separate picture and sound streams.
    """
    if kind is MediaKind.AUDIO:
        return container != "m4a"
    return True
