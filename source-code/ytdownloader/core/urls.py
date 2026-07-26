"""Validação e normalização das URLs aceitas pelo aplicativo.

O yt-dlp extrai vídeo de mais de mil sites, então a validação aceita qualquer
endereço http/https. O YouTube continua recebendo tratamento especial — extração
de identificador, detecção de playlist e miniatura previsível — porque é o caso
de uso principal e permite mostrar a prévia antes mesmo de consultar a rede.
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

#: Sites com nome conhecido, apenas para exibição na interface.
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

# IDs de vídeo do YouTube têm exatamente 11 caracteres do alfabeto base64-url.
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{2,}$")

# Caminhos do YouTube que carregam o identificador no próprio path.
PATH_PREFIXES = ("/shorts/", "/embed/", "/live/", "/v/")

SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
HOST_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)+$"
)


@dataclass(frozen=True)
class ParsedUrl:
    """Resultado da análise de um endereço colado pelo usuário."""

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
        """Playlist a ser expandida: só quando não há um vídeo específico."""
        return self.playlist_id is not None and self.video_id is None

    @property
    def canonical(self) -> str:
        """Endereço limpo, sem parâmetros de rastreamento.

        Fora do YouTube o endereço é devolvido como veio: cada site tem sua
        própria convenção e reescrevê-lo por conta própria quebraria links.
        """
        if self.video_id:
            return f"https://www.youtube.com/watch?v={self.video_id}"
        if self.playlist_id and self.is_youtube:
            return f"https://www.youtube.com/playlist?list={self.playlist_id}"
        return _with_scheme(self.original)

    @property
    def thumbnail_url(self) -> str | None:
        """Miniatura previsível do YouTube, exibida antes da consulta à rede."""
        if not self.video_id:
            return None
        return f"https://i.ytimg.com/vi/{self.video_id}/hqdefault.jpg"

    @property
    def site_name(self) -> str:
        """Nome do site para exibição, ou o próprio domínio."""
        if self.is_youtube:
            return "YouTube"
        host = self.host.removeprefix("www.")
        for domain, name in KNOWN_SITES.items():
            if host == domain or host.endswith("." + domain):
                return name
        return host


def _with_scheme(url: str) -> str:
    """Completa o esquema quando o usuário cola o endereço sem ele."""
    url = (url or "").strip()
    if not url:
        return ""
    if not SCHEME_RE.match(url):
        url = "https://" + url
    return url


def parse_url(url: str) -> ParsedUrl:
    """Analisa o endereço e extrai o que for possível."""
    raw = (url or "").strip()
    cleaned = _with_scheme(raw)
    if not cleaned:
        return ParsedUrl(original=raw)

    try:
        parsed = urlparse(cleaned)
    except ValueError:
        return ParsedUrl(original=raw)

    # Apenas http e https: file://, javascript: e afins não têm o que fazer aqui.
    if parsed.scheme not in ("http", "https"):
        return ParsedUrl(original=raw)

    host = (parsed.hostname or "").lower()
    if not host or not HOST_RE.match(host):
        return ParsedUrl(original=raw)

    is_youtube = host in YOUTUBE_HOSTS
    if not is_youtube:
        # Qualquer outro site fica a cargo do yt-dlp, que sabe quais suporta.
        return ParsedUrl(original=raw, host=host, is_supported=True)

    query = parse_qs(parsed.query)
    path = parsed.path or "/"

    video_id = _extract_video_id(host, path, query)
    playlist_id = _extract_playlist_id(query)

    # O endereço do YouTube só serve se apontar para um vídeo ou uma playlist.
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
    # "RD..." são mixes infinitos gerados pelo YouTube, não playlists reais.
    if values[0].startswith("RD"):
        return None
    return values[0]


def is_supported_url(url: str) -> bool:
    """Atalho booleano usado na validação enquanto o usuário digita."""
    return parse_url(url).is_supported


def format_duration(seconds: float | int | None) -> str:
    """Formata uma duração em segundos como ``mm:ss`` ou ``h:mm:ss``."""
    if not seconds or seconds < 0:
        return "--:--"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_size(num_bytes: float | int | None) -> str:
    """Formata um tamanho em bytes de forma legível."""
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
