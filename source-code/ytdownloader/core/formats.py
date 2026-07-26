"""Catálogo de formatos e qualidades oferecidos ao usuário."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MediaKind(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


@dataclass(frozen=True)
class QualityOption:
    """Uma opção de qualidade exibida na interface."""

    key: str
    label: str
    description: str
    max_height: int | None = None


VIDEO_QUALITIES: tuple[QualityOption, ...] = (
    QualityOption("best", "Máxima disponível", "Melhor resolução que o vídeo oferecer"),
    QualityOption("2160p", "4K · 2160p", "Arquivos bem grandes", 2160),
    QualityOption("1440p", "QHD · 1440p", "Alta qualidade", 1440),
    QualityOption("1080p", "Full HD · 1080p", "Melhor equilíbrio entre qualidade e tamanho", 1080),
    QualityOption("720p", "HD · 720p", "Leve e compatível com tudo", 720),
    QualityOption("480p", "SD · 480p", "Economiza espaço", 480),
    QualityOption("360p", "Baixa · 360p", "Menor arquivo possível", 360),
)

AUDIO_QUALITIES: tuple[QualityOption, ...] = (
    QualityOption("320", "320 kbps", "Qualidade máxima de áudio"),
    QualityOption("256", "256 kbps", "Alta qualidade"),
    QualityOption("192", "192 kbps", "Padrão recomendado"),
    QualityOption("128", "128 kbps", "Arquivo menor"),
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
    """Monta o seletor de formato do yt-dlp para download de vídeo.

    A cadeia tenta, em ordem: faixas separadas no container preferido, faixas
    separadas em qualquer container e, por fim, um arquivo já combinado. Assim o
    download não falha quando o vídeo não oferece a combinação ideal.
    """
    option = video_quality(quality_key)
    height = option.max_height

    limit = "" if height is None else f"[height<={height}]"

    if container == "mp4":
        preferred = f"bestvideo{limit}[ext=mp4]+bestaudio[ext=m4a]"
    elif container == "webm":
        preferred = f"bestvideo{limit}[ext=webm]+bestaudio[ext=webm]"
    else:  # mkv aceita qualquer combinação
        preferred = f"bestvideo{limit}+bestaudio"

    chain = [preferred, f"bestvideo{limit}+bestaudio", f"best{limit}", "best"]

    # Sem limite de altura as alternativas se repetem; mantém só a primeira ocorrência.
    unique: list[str] = []
    for item in chain:
        if item not in unique:
            unique.append(item)
    return "/".join(unique)


def build_format_sort(container: str) -> list[str]:
    """Critérios de desempate entre formatos equivalentes.

    Para MP4 damos preferência a H.264 e AAC: o YouTube costuma oferecer AV1 na
    mesma resolução, que gera arquivos menores mas não abre em players e TVs
    mais antigos. Em MKV e WebM não há esse problema, então vale a melhor
    compressão disponível.
    """
    if container == "mp4":
        return ["vcodec:h264", "acodec:aac", "res", "fps"]
    return ["res", "fps"]


def build_audio_format() -> str:
    """Seletor de formato do yt-dlp para download somente de áudio."""
    return "bestaudio/best"


def needs_ffmpeg(kind: MediaKind, container: str) -> bool:
    """Indica se a combinação escolhida exige FFmpeg.

    Áudio sempre passa por conversão, exceto quando o usuário pede ``m4a``, que
    normalmente já é o formato nativo entregue pelo YouTube. Vídeo precisa de
    FFmpeg para juntar as faixas separadas de imagem e som.
    """
    if kind is MediaKind.AUDIO:
        return container != "m4a"
    return True
