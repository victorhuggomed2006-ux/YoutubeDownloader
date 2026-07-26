"""Data structures shared between the core and the interface."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from .formats import (
    DEFAULT_AUDIO_CONTAINER,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_VIDEO_CONTAINER,
    DEFAULT_VIDEO_QUALITY,
    MediaKind,
)

UNTITLED = "Untitled"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    FETCHING = "fetching"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_final(self) -> bool:
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    @property
    def label(self) -> str:
        return {
            TaskStatus.QUEUED: "Queued",
            TaskStatus.FETCHING: "Looking up",
            TaskStatus.DOWNLOADING: "Downloading",
            TaskStatus.CONVERTING: "Converting",
            TaskStatus.COMPLETED: "Done",
            TaskStatus.FAILED: "Failed",
            TaskStatus.CANCELLED: "Cancelled",
        }[self]


@dataclass
class VideoInfo:
    """Video metadata, fetched before the download starts."""

    video_id: str = ""
    title: str = UNTITLED
    uploader: str = ""
    duration: float = 0.0
    thumbnail: str = ""
    webpage_url: str = ""
    is_live: bool = False
    view_count: int | None = None
    filesize_approx: int | None = None

    @classmethod
    def from_ydl(cls, info: dict) -> VideoInfo:
        """Build from the dictionary yt-dlp returns."""
        return cls(
            video_id=info.get("id") or "",
            title=info.get("title") or UNTITLED,
            uploader=info.get("uploader") or info.get("channel") or "",
            duration=float(info.get("duration") or 0),
            thumbnail=info.get("thumbnail") or "",
            webpage_url=info.get("webpage_url") or info.get("original_url") or "",
            is_live=bool(info.get("is_live")),
            view_count=info.get("view_count"),
            filesize_approx=info.get("filesize") or info.get("filesize_approx"),
        )


@dataclass
class DownloadRequest:
    """What the user asked to download."""

    url: str
    kind: MediaKind = MediaKind.VIDEO
    quality: str = DEFAULT_VIDEO_QUALITY
    container: str = DEFAULT_VIDEO_CONTAINER
    output_dir: Path = field(default_factory=Path.cwd)
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    write_subtitles: bool = False
    subtitle_languages: tuple[str, ...] = ("en", "pt", "pt-BR", "es")

    def normalized(self) -> DownloadRequest:
        """Make sure quality and container match the media kind.

        Switching between video and audio would otherwise leave "1080p" as a
        bitrate, or "mp4" as an audio container.
        """
        if self.kind is MediaKind.AUDIO:
            quality = self.quality if self.quality.isdigit() else DEFAULT_AUDIO_QUALITY
            container = (
                self.container
                if self.container in ("mp3", "m4a", "opus", "wav", "flac")
                else DEFAULT_AUDIO_CONTAINER
            )
        else:
            quality = self.quality if not self.quality.isdigit() else DEFAULT_VIDEO_QUALITY
            container = (
                self.container
                if self.container in ("mp4", "mkv", "webm")
                else DEFAULT_VIDEO_CONTAINER
            )
        return DownloadRequest(
            url=self.url,
            kind=self.kind,
            quality=quality,
            container=container,
            output_dir=self.output_dir,
            embed_thumbnail=self.embed_thumbnail,
            embed_metadata=self.embed_metadata,
            write_subtitles=self.write_subtitles,
            subtitle_languages=self.subtitle_languages,
        )


@dataclass
class Progress:
    """A snapshot of how a download is going."""

    percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    status: TaskStatus = TaskStatus.QUEUED
    detail: str = ""


@dataclass
class DownloadTask:
    """One entry in the download queue."""

    request: DownloadRequest
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    info: VideoInfo | None = None
    status: TaskStatus = TaskStatus.QUEUED
    progress: Progress = field(default_factory=Progress)
    output_file: Path | None = None
    error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None

    @property
    def display_title(self) -> str:
        if self.info and self.info.title:
            return self.info.title
        return self.request.url


@dataclass
class HistoryEntry:
    """A stored record of a finished download."""

    title: str
    url: str
    kind: str
    quality: str
    container: str
    status: str
    file_path: str = ""
    size_bytes: int = 0
    error: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "kind": self.kind,
            "quality": self.quality,
            "container": self.container,
            "status": self.status,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "error": self.error,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> HistoryEntry:
        return cls(
            title=data.get("title") or UNTITLED,
            url=data.get("url") or "",
            kind=data.get("kind") or "video",
            quality=data.get("quality") or "",
            container=data.get("container") or "",
            status=data.get("status") or "completed",
            file_path=data.get("file_path") or "",
            size_bytes=int(data.get("size_bytes") or 0),
            error=data.get("error") or "",
            timestamp=data.get("timestamp") or "",
        )

    @classmethod
    def from_task(cls, task: DownloadTask) -> HistoryEntry:
        size = 0
        if task.output_file and task.output_file.exists():
            size = task.output_file.stat().st_size
        elif task.progress.downloaded_bytes:
            size = task.progress.downloaded_bytes
        return cls(
            title=task.display_title,
            url=task.request.url,
            kind=task.request.kind.value,
            quality=task.request.quality,
            container=task.request.container,
            status=task.status.value,
            file_path=str(task.output_file) if task.output_file else "",
            size_bytes=size,
            error=task.error,
        )
