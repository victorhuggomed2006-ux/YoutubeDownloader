"""The layer over yt-dlp: metadata lookups and running downloads.

This module knows nothing about Qt. The interface talks to it through
callbacks, which keeps the core testable and reusable.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Sequence
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YdlDownloadError

from . import ffmpeg as ffmpeg_module
from . import jsruntime
from .errors import DownloadCancelled, DownloaderError, FFmpegMissingError, humanize
from .formats import (
    MediaKind,
    build_audio_format,
    build_format_sort,
    build_video_format,
    needs_ffmpeg,
)
from .models import DownloadRequest, Progress, TaskStatus, VideoInfo
from .urls import parse_url

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Progress], None]

#: How many fragments are fetched in parallel per download.
CONCURRENT_FRAGMENTS = 4

#: Value that means "do not import cookies from any browser".
NO_BROWSER = "none"


class _YdlLogger:
    """Routes yt-dlp's own messages into the application log."""

    def __init__(self) -> None:
        self.last_error: str = ""

    def debug(self, msg: str) -> None:
        if msg.startswith("[debug] "):
            return
        logger.debug("yt-dlp: %s", msg)

    def info(self, msg: str) -> None:
        logger.debug("yt-dlp: %s", msg)

    def warning(self, msg: str) -> None:
        logger.warning("yt-dlp: %s", msg)

    def error(self, msg: str) -> None:
        self.last_error = str(msg)
        logger.error("yt-dlp: %s", msg)


class Downloader:
    """Runs lookups and downloads through yt-dlp."""

    def __init__(self, cookies_from_browser: str = NO_BROWSER) -> None:
        self.cookies_from_browser = cookies_from_browser

    # ── Options ──────────────────────────────────────────────────────────

    def _base_options(self) -> dict:
        options: dict = {
            "quiet": True,
            "no_warnings": False,
            "noprogress": True,
            "noplaylist": True,
            "ignoreerrors": False,
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
            "extractor_retries": 3,
            "skip_unavailable_fragments": True,
            "windowsfilenames": True,
            # Applies to the file name alone, since the directory goes in "paths".
            "trim_file_name": 120,
            "logger": _YdlLogger(),
        }

        runtimes = jsruntime.detect()
        if runtimes:
            options["js_runtimes"] = runtimes

        browser = (self.cookies_from_browser or NO_BROWSER).strip().lower()
        if browser and browser != NO_BROWSER:
            # yt-dlp expects a (browser, profile, keyring, container) tuple.
            options["cookiesfrombrowser"] = (browser,)

        location = ffmpeg_module.ffmpeg_location()
        if location:
            options["ffmpeg_location"] = location

        return options

    def _download_options(
        self,
        request: DownloadRequest,
        progress_hook: Callable[[dict], None],
        postprocessor_hook: Callable[[dict], None],
    ) -> dict:
        request = request.normalized()
        options = self._base_options()

        output_dir = Path(request.output_dir)
        options.update(
            {
                # The template must be relative: the directory comes from
                # "paths", and that is what makes the long-name trim apply to
                # the file name instead of chopping the directory too.
                "outtmpl": "%(title)s.%(ext)s",
                "paths": {"home": str(output_dir)},
                "progress_hooks": [progress_hook],
                "postprocessor_hooks": [postprocessor_hook],
                "concurrent_fragment_downloads": CONCURRENT_FRAGMENTS,
                "overwrites": False,
                "continuedl": True,
            }
        )

        postprocessors: list[dict] = []

        if request.kind is MediaKind.AUDIO:
            options["format"] = build_audio_format()
            if request.container != "m4a":
                postprocessors.append(
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": request.container,
                        "preferredquality": request.quality,
                    }
                )
        else:
            options["format"] = build_video_format(request.quality, request.container)
            options["merge_output_format"] = request.container
            options["format_sort"] = build_format_sort(request.container)

        if request.embed_metadata:
            postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

        if request.embed_thumbnail:
            options["writethumbnail"] = True
            postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

        if request.write_subtitles and request.kind is MediaKind.VIDEO:
            options.update(
                {
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": list(request.subtitle_languages),
                    "subtitlesformat": "srt/best",
                }
            )
            postprocessors.append({"key": "FFmpegEmbedSubtitle", "already_have_subtitle": False})

        if postprocessors:
            options["postprocessors"] = postprocessors

        return options

    # ── Lookups ──────────────────────────────────────────────────────────

    def fetch_info(self, url: str) -> VideoInfo:
        """Fetch the metadata of a single video."""
        parsed = parse_url(url)
        if not parsed.is_supported:
            raise DownloaderError("This address is not a valid video link.")

        target = parsed.canonical
        options = self._base_options()
        options["skip_download"] = True

        try:
            with YoutubeDL(options) as ydl:
                raw = ydl.extract_info(target, download=False)
        except YdlDownloadError as exc:
            raise humanize(exc) from exc
        except Exception as exc:
            raise humanize(exc) from exc

        if raw is None:
            raise DownloaderError("Could not read the video details.")

        if raw.get("_type") == "playlist":
            entries = [e for e in (raw.get("entries") or []) if e]
            if not entries:
                raise DownloaderError("This playlist is empty or private.")
            raw = entries[0]

        return VideoInfo.from_ydl(raw)

    def fetch_playlist(self, url: str, limit: int = 200) -> list[VideoInfo]:
        """List the videos in a playlist or collection, downloading nothing.

        Outside YouTube there is no way to tell from the address alone whether
        it points at a collection; yt-dlp decides that while extracting.
        """
        parsed = parse_url(url)
        if not parsed.is_supported:
            raise DownloaderError("This address is not a valid link.")

        options = self._base_options()
        options.update(
            {
                "skip_download": True,
                "noplaylist": False,
                "extract_flat": "in_playlist",
                "playlistend": limit,
            }
        )

        try:
            with YoutubeDL(options) as ydl:
                raw = ydl.extract_info(parsed.canonical, download=False)
        except Exception as exc:
            raise humanize(exc) from exc

        if not raw:
            raise DownloaderError("Could not read the video list.")

        if raw.get("_type") != "playlist":
            raise DownloaderError("This address points to a single video, not a list.")

        videos: list[VideoInfo] = []
        for entry in raw.get("entries") or []:
            if not entry:
                continue
            info = VideoInfo.from_ydl(entry)
            if not info.webpage_url and info.video_id:
                info.webpage_url = f"https://www.youtube.com/watch?v={info.video_id}"
            if not info.thumbnail and info.video_id:
                info.thumbnail = f"https://i.ytimg.com/vi/{info.video_id}/hqdefault.jpg"
            videos.append(info)

        if not videos:
            raise DownloaderError("This playlist is empty or private.")
        return videos

    # ── Download ─────────────────────────────────────────────────────────

    def download(
        self,
        request: DownloadRequest,
        on_progress: ProgressCallback | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Path:
        """Download what was requested and return the final file path.

        ``cancel_event`` interrupts the download between fragments.
        """
        request = request.normalized()

        # Merging video with audio needs FFmpeg. Better to say so now than to
        # download hundreds of megabytes and fail at the end.
        if needs_ffmpeg(request.kind, request.container) and not ffmpeg_module.is_available():
            raise FFmpegMissingError()

        output_dir = Path(request.output_dir)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise humanize(exc) from exc

        def check_cancelled() -> None:
            if cancel_event is not None and cancel_event.is_set():
                raise DownloadCancelled()

        def report(progress: Progress) -> None:
            if on_progress is not None:
                on_progress(progress)

        def progress_hook(data: dict) -> None:
            check_cancelled()
            status = data.get("status")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes") or 0
                percent = (downloaded / total * 100) if total else 0.0
                report(
                    Progress(
                        percent=min(percent, 100.0),
                        downloaded_bytes=int(downloaded),
                        total_bytes=int(total) if total else None,
                        speed=data.get("speed"),
                        eta=data.get("eta"),
                        status=TaskStatus.DOWNLOADING,
                    )
                )
            elif status == "finished":
                report(
                    Progress(
                        percent=100.0,
                        downloaded_bytes=int(data.get("downloaded_bytes") or 0),
                        total_bytes=data.get("total_bytes"),
                        status=TaskStatus.CONVERTING,
                        detail="Finishing the file...",
                    )
                )

        def postprocessor_hook(data: dict) -> None:
            check_cancelled()
            if data.get("status") != "started":
                return
            name = str(data.get("postprocessor") or "")
            detail = {
                "FFmpegExtractAudio": "Converting the audio...",
                "FFmpegMerger": "Merging video and audio...",
                "FFmpegVideoConvertor": "Converting the video...",
                "EmbedThumbnail": "Applying the cover art...",
                "FFmpegMetadata": "Writing the metadata...",
                "FFmpegEmbedSubtitle": "Embedding the subtitles...",
                "MoveFiles": "Saving to the destination folder...",
            }.get(name, "Processing the file...")
            report(Progress(percent=100.0, status=TaskStatus.CONVERTING, detail=detail))

        options = self._download_options(request, progress_hook, postprocessor_hook)
        ydl_logger = options["logger"]

        report(Progress(status=TaskStatus.FETCHING, detail="Looking up the video..."))
        check_cancelled()

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(request.url, download=True)
        except DownloadCancelled:
            raise
        except YdlDownloadError as exc:
            raise humanize(ydl_logger.last_error or exc) from exc
        except Exception as exc:
            raise humanize(exc) from exc

        if info is None:
            raise DownloaderError("The download produced no file.")

        output_file = self._resolve_output_file(info, output_dir, request)
        if output_file is None:
            raise DownloaderError("The downloaded file was not found on disk.")

        report(
            Progress(
                percent=100.0,
                downloaded_bytes=output_file.stat().st_size,
                total_bytes=output_file.stat().st_size,
                status=TaskStatus.COMPLETED,
                detail="Done",
            )
        )
        return output_file

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_output_file(info: dict, output_dir: Path, request: DownloadRequest) -> Path | None:
        """Work out the final file path from what yt-dlp returned."""
        candidates: list[str] = []

        for entry in info.get("requested_downloads") or []:
            for key in ("filepath", "_filename", "filename"):
                value = entry.get(key)
                if value:
                    candidates.append(value)

        for key in ("filepath", "_filename"):
            value = info.get(key)
            if value:
                candidates.append(value)

        for candidate in candidates:
            path = Path(candidate)
            if path.is_file():
                return path
            # Post-processing changes the extension, but the stem stays.
            converted = path.with_suffix(f".{request.container}")
            if converted.is_file():
                return converted

        return Downloader._newest_matching_file(output_dir, request, candidates)

    @staticmethod
    def _newest_matching_file(
        output_dir: Path, request: DownloadRequest, candidates: Sequence[str]
    ) -> Path | None:
        """Last resort: the newest file of the requested type in the folder."""
        if not output_dir.is_dir():
            return None

        stems = {Path(c).stem for c in candidates if c}
        matches = [
            path
            for path in output_dir.glob(f"*.{request.container}")
            if path.is_file() and (not stems or path.stem in stems)
        ]
        if not matches:
            matches = [p for p in output_dir.glob(f"*.{request.container}") if p.is_file()]
        if not matches:
            return None
        return max(matches, key=lambda p: p.stat().st_mtime)
