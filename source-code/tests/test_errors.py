"""Testes da tradução de erros do yt-dlp para mensagens ao usuário."""

from __future__ import annotations

import pytest

from ytdownloader.core.errors import (
    DownloadCancelled,
    DownloaderError,
    FFmpegMissingError,
    clean_message,
    humanize,
)


def test_remove_prefixos_e_cores() -> None:
    bruto = "\x1b[0;31mERROR:\x1b[0m [youtube] abc: Video unavailable"
    assert clean_message(bruto) == "abc: Video unavailable"


@pytest.mark.parametrize(
    ("bruto", "trecho_esperado"),
    [
        ("ERROR: Sign in to confirm you're not a bot", "verificação de conta"),
        ("ERROR: Private video. Sign in if you've been granted access", "privado"),
        ("ERROR: Video unavailable", "indisponível"),
        ("ERROR: This video has been removed by the uploader", "indisponível"),
        ("ERROR: This video is age-restricted", "restrição de idade"),
        ("ERROR: Join this channel to get access to members-only content", "membros"),
        ("ERROR: The uploader has not made this video available in your country", "região"),
        ("ERROR: Requested format is not available", "qualidade escolhida"),
        ("ERROR: unable to download video data: timed out", "conexão"),
        ("ERROR: ffprobe/ffmpeg not found", "FFmpeg"),
        ("[Errno 13] Permission denied: 'C:/x'", "permissão"),
        ("OSError: [Errno 28] No space left on device", "espaço"),
    ],
)
def test_traduz_erros_conhecidos(bruto: str, trecho_esperado: str) -> None:
    erro = humanize(bruto)
    assert isinstance(erro, DownloaderError)
    assert trecho_esperado.lower() in str(erro).lower()


def test_bloqueio_de_bot_sugere_cookies() -> None:
    erro = humanize("ERROR: Sign in to confirm you're not a bot")
    assert "cookies" in erro.hint.lower()


def test_erro_desconhecido_vira_mensagem_curta() -> None:
    erro = humanize("ERROR: algo muito específico deu errado\nlinha extra ignorada")
    assert "linha extra" not in str(erro)
    assert "algo muito específico" in str(erro)


def test_mensagem_vazia_tem_texto_padrao() -> None:
    assert str(humanize("")) == "Não foi possível concluir o download."


def test_texto_gigante_e_truncado() -> None:
    assert len(str(humanize("x" * 900))) <= 230


def test_erro_ja_tratado_passa_direto() -> None:
    original = DownloaderError("mensagem pronta")
    assert humanize(original) is original


def test_cancelamento_e_erro_de_ffmpeg_tem_mensagem_propria() -> None:
    assert "cancelado" in str(DownloadCancelled()).lower()
    assert "ffmpeg" in str(FFmpegMissingError()).lower()
