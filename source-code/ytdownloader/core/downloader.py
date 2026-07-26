"""Camada sobre o yt-dlp: consulta de metadados e execução dos downloads.

Este módulo não conhece Qt. A interface conversa com ele por callbacks, o que
mantém o núcleo testável e reaproveitável.
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

#: Quantidade de fragmentos baixados em paralelo por download.
CONCURRENT_FRAGMENTS = 4


class _YdlLogger:
    """Redireciona as mensagens do yt-dlp para o logging do aplicativo."""

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
    """Executa consultas e downloads usando o yt-dlp."""

    def __init__(self, cookies_from_browser: str = "nenhum") -> None:
        self.cookies_from_browser = cookies_from_browser

    # ── Opções ───────────────────────────────────────────────────────────

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
            # Aplicado apenas ao nome do arquivo, já que o diretório vai em "paths".
            "trim_file_name": 120,
            "logger": _YdlLogger(),
        }

        runtimes = jsruntime.detect()
        if runtimes:
            options["js_runtimes"] = runtimes

        browser = (self.cookies_from_browser or "nenhum").strip().lower()
        if browser and browser != "nenhum":
            # O yt-dlp espera uma tupla (navegador, perfil, keyring, container).
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
                # O modelo precisa ser relativo: o diretório vem de "paths", e é
                # isso que faz o corte de nome longo agir só sobre o nome.
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

    # ── Consultas ────────────────────────────────────────────────────────

    def fetch_info(self, url: str) -> VideoInfo:
        """Obtém os metadados de um único vídeo."""
        parsed = parse_url(url)
        if not parsed.is_supported:
            raise DownloaderError("Este endereço não é um link de vídeo válido.")

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
            raise DownloaderError("Não foi possível ler as informações do vídeo.")

        if raw.get("_type") == "playlist":
            entries = [e for e in (raw.get("entries") or []) if e]
            if not entries:
                raise DownloaderError("Esta playlist está vazia ou é privada.")
            raw = entries[0]

        return VideoInfo.from_ydl(raw)

    def fetch_playlist(self, url: str, limit: int = 200) -> list[VideoInfo]:
        """Lista os vídeos de uma playlist ou coleção, sem baixar nada.

        Fora do YouTube não dá para saber pelo endereço se ele aponta para uma
        coleção; quem decide é o próprio yt-dlp ao extrair.
        """
        parsed = parse_url(url)
        if not parsed.is_supported:
            raise DownloaderError("Este endereço não é um link válido.")

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
            raise DownloaderError("Não foi possível ler a lista de vídeos.")

        if raw.get("_type") != "playlist":
            raise DownloaderError("Este endereço aponta para um vídeo único, não uma lista.")

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
            raise DownloaderError("Esta playlist está vazia ou é privada.")
        return videos

    # ── Download ─────────────────────────────────────────────────────────

    def download(
        self,
        request: DownloadRequest,
        on_progress: ProgressCallback | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Path:
        """Baixa o vídeo ou áudio pedido e devolve o caminho do arquivo final.

        ``cancel_event`` permite interromper o download entre fragmentos.
        """
        request = request.normalized()

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
                        detail="Finalizando arquivo...",
                    )
                )

        def postprocessor_hook(data: dict) -> None:
            check_cancelled()
            if data.get("status") != "started":
                return
            name = str(data.get("postprocessor") or "")
            detail = {
                "FFmpegExtractAudio": "Convertendo o áudio...",
                "FFmpegMerger": "Juntando vídeo e áudio...",
                "FFmpegVideoConvertor": "Convertendo o vídeo...",
                "EmbedThumbnail": "Aplicando a capa...",
                "FFmpegMetadata": "Gravando as informações...",
                "FFmpegEmbedSubtitle": "Incorporando as legendas...",
                "MoveFiles": "Salvando na pasta de destino...",
            }.get(name, "Processando o arquivo...")
            report(Progress(percent=100.0, status=TaskStatus.CONVERTING, detail=detail))

        options = self._download_options(request, progress_hook, postprocessor_hook)
        ydl_logger = options["logger"]

        report(Progress(status=TaskStatus.FETCHING, detail="Consultando o vídeo..."))
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
            raise DownloaderError("O download não produziu nenhum arquivo.")

        output_file = self._resolve_output_file(info, output_dir, request)
        if output_file is None:
            raise DownloaderError("O arquivo baixado não foi encontrado no disco.")

        report(
            Progress(
                percent=100.0,
                downloaded_bytes=output_file.stat().st_size,
                total_bytes=output_file.stat().st_size,
                status=TaskStatus.COMPLETED,
                detail="Concluído",
            )
        )
        return output_file

    # ── Auxiliares ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve_output_file(info: dict, output_dir: Path, request: DownloadRequest) -> Path | None:
        """Descobre o caminho do arquivo final a partir do retorno do yt-dlp."""
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
            # Após a conversão a extensão muda, mas o nome base continua igual.
            converted = path.with_suffix(f".{request.container}")
            if converted.is_file():
                return converted

        return Downloader._newest_matching_file(output_dir, request, candidates)

    @staticmethod
    def _newest_matching_file(
        output_dir: Path, request: DownloadRequest, candidates: Sequence[str]
    ) -> Path | None:
        """Último recurso: procura na pasta o arquivo mais recente do tipo pedido."""
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
