"""Application exceptions, and yt-dlp errors turned into plain language."""

from __future__ import annotations

import re


class DownloaderError(Exception):
    """A download error already phrased for the person using the app."""

    def __init__(self, message: str, *, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message} {self.hint}"
        return self.message


class DownloadCancelled(DownloaderError):
    """Raised when the user cancels a download in progress."""

    def __init__(self, message: str = "Download cancelled.") -> None:
        super().__init__(message)


class FFmpegMissingError(DownloaderError):
    """Raised when a conversion needs FFmpeg and it could not be found."""

    def __init__(self) -> None:
        super().__init__(
            "FFmpeg not found.",
            hint="Reinstall the app, or install FFmpeg and add it to your PATH.",
        )


# yt-dlp output patterns mapped to messages a non-programmer can act on.
_ERROR_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        r"sign in to confirm|not a bot|confirm your age.*sign in",
        "The site asked for account verification on this video.",
        "In Settings, turn on browser cookie import and try again.",
    ),
    (
        r"private video|this video is private",
        "This video is private.",
        "Only the channel owner can access it.",
    ),
    (
        r"members[- ]only|join this channel",
        "This video is for channel members only.",
        "You need to be a member and use your account cookies.",
    ),
    (
        r"age[- ]restricted|inappropriate for some users|confirm your age",
        "This video is age-restricted.",
        "Turn on browser cookie import in Settings.",
    ),
    (
        r"video unavailable|has been removed|no longer available|removed by the uploader",
        "Video unavailable or removed.",
        "",
    ),
    (
        # YouTube says "has not made this video available in your country",
        # alongside the "blocked" and "geo-restricted" variants.
        r"available in your country|blocked it in your country|geo.?(block|restrict)",
        "This video is blocked in your region.",
        "",
    ),
    (
        r"live event will begin|premieres in|is not yet available",
        "The stream has not started yet.",
        "Try again once the video is available.",
    ),
    (
        r"live.*not.*download|is live",
        "A live stream in progress cannot be downloaded.",
        "Wait for the stream to end and download the recording.",
    ),
    (
        r"requested format is not available|no video formats found",
        "The selected quality is not available for this video.",
        'Pick another quality or use "Best available".',
    ),
    (
        r"unable to download|urlopen error|timed out|connection|network|getaddrinfo|resolve",
        "Connection failed.",
        "Check your internet connection and try again.",
    ),
    (
        r"ffmpeg|ffprobe",
        "FFmpeg failed to process the file.",
        "Reinstall the app to restore its components.",
    ),
    (
        r"unsupported url|is not a valid url",
        "This site is not supported.",
        "",
    ),
    (
        r"permission denied|access is denied|errno 13",
        "No permission to write to the selected folder.",
        "Choose a different destination folder.",
    ),
    (
        r"no space left|errno 28|disk full",
        "Not enough disk space.",
        "Free up some space and try again.",
    ),
)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_PREFIX_RE = re.compile(r"^\s*(ERROR|WARNING):\s*", re.IGNORECASE)


def clean_message(raw: str) -> str:
    """Strip colour codes and technical prefixes from a yt-dlp message."""
    text = _ANSI_RE.sub("", str(raw or "")).strip()
    text = _PREFIX_RE.sub("", text)
    text = re.sub(r"\[[a-zA-Z0-9:_-]+\]\s*", "", text, count=1)
    return text.strip()


def humanize(raw: str | BaseException) -> DownloaderError:
    """Turn a raw yt-dlp error into a readable ``DownloaderError``."""
    if isinstance(raw, DownloaderError):
        return raw

    text = clean_message(str(raw))
    lowered = text.lower()

    for pattern, message, hint in _ERROR_PATTERNS:
        if re.search(pattern, lowered):
            return DownloaderError(message, hint=hint)

    if not text:
        return DownloaderError("The download could not be completed.")

    # Keep the first line at most, so the interface stays readable.
    first_line = text.splitlines()[0]
    if len(first_line) > 220:
        first_line = first_line[:217] + "..."
    return DownloaderError(first_line)
