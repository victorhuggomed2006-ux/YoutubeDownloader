"""Testes do catálogo de formatos e dos seletores enviados ao yt-dlp."""

from __future__ import annotations

import pytest

from ytdownloader.core.formats import (
    AUDIO_QUALITIES,
    VIDEO_QUALITIES,
    MediaKind,
    build_audio_format,
    build_format_sort,
    build_video_format,
    needs_ffmpeg,
    video_quality,
)


def test_qualidades_de_video_tem_chaves_unicas() -> None:
    chaves = [option.key for option in VIDEO_QUALITIES]
    assert len(chaves) == len(set(chaves))


def test_qualidades_de_audio_sao_numericas() -> None:
    for option in AUDIO_QUALITIES:
        assert option.key.isdigit()


@pytest.mark.parametrize(("chave", "altura"), [("1080p", 1080), ("720p", 720), ("360p", 360)])
def test_limite_de_altura_entra_no_seletor(chave: str, altura: int) -> None:
    seletor = build_video_format(chave, "mp4")
    assert f"[height<={altura}]" in seletor
    assert seletor.startswith("bestvideo")


def test_qualidade_maxima_nao_impoe_limite() -> None:
    seletor = build_video_format("best", "mp4")
    assert "height<=" not in seletor


def test_seletor_nao_repete_alternativas() -> None:
    """Sem limite de altura as alternativas colidem; não pode haver repetição."""
    seletor = build_video_format("best", "mkv")
    partes = seletor.split("/")
    assert len(partes) == len(set(partes))


def test_qualidade_desconhecida_cai_no_padrao() -> None:
    assert video_quality("8000p").key == VIDEO_QUALITIES[0].key


@pytest.mark.parametrize("container", ["mp4", "mkv", "webm"])
def test_seletor_sempre_tem_alternativa_final(container: str) -> None:
    seletor = build_video_format("1080p", container)
    assert seletor.split("/")[-1] == "best"


def test_mp4_prefere_h264_para_compatibilidade() -> None:
    ordem = build_format_sort("mp4")
    assert ordem[0] == "vcodec:h264"
    assert "acodec:aac" in ordem


def test_outros_containers_priorizam_resolucao() -> None:
    assert build_format_sort("mkv")[0] == "res"


def test_seletor_de_audio() -> None:
    assert build_audio_format() == "bestaudio/best"


@pytest.mark.parametrize(
    ("kind", "container", "esperado"),
    [
        (MediaKind.AUDIO, "mp3", True),
        (MediaKind.AUDIO, "wav", True),
        (MediaKind.AUDIO, "m4a", False),  # formato nativo, não precisa converter
        (MediaKind.VIDEO, "mp4", True),  # juntar vídeo e áudio exige FFmpeg
        (MediaKind.VIDEO, "mkv", True),
    ],
)
def test_quando_o_ffmpeg_e_necessario(kind: MediaKind, container: str, esperado: bool) -> None:
    assert needs_ffmpeg(kind, container) is esperado
