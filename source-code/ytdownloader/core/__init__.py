"""The application core: download rules, independent of any interface."""

from .errors import DownloadCancelled, DownloaderError, FFmpegMissingError
from .formats import MediaKind
from .models import (
    DownloadRequest,
    DownloadTask,
    HistoryEntry,
    Progress,
    TaskStatus,
    VideoInfo,
)

__all__ = [
    "DownloadCancelled",
    "DownloadRequest",
    "DownloadTask",
    "DownloaderError",
    "FFmpegMissingError",
    "HistoryEntry",
    "MediaKind",
    "Progress",
    "TaskStatus",
    "VideoInfo",
]
