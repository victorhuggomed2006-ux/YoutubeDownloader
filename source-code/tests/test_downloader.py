"""Testes do motor de download.

Nada aqui toca a rede: o que se verifica é como as opções são montadas antes de
entregá-las ao yt-dlp e como o arquivo final é localizado depois.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from ytdownloader.core import ffmpeg as ffmpeg_module
from ytdownloader.core.downloader import Downloader
from ytdownloader.core.errors import DownloaderError, FFmpegMissingError
from ytdownloader.core.formats import MediaKind
from ytdownloader.core.models import DownloadRequest


@pytest.fixture
def pedido(tmp_path: Path) -> DownloadRequest:
    return DownloadRequest(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        kind=MediaKind.VIDEO,
        quality="1080p",
        container="mp4",
        output_dir=tmp_path,
    )


def _opcoes(downloader: Downloader, pedido: DownloadRequest) -> dict:
    return downloader._download_options(pedido, lambda _: None, lambda _: None)


# ── Montagem das opções ──────────────────────────────────────────────────


def test_modelo_de_nome_e_relativo(pedido: DownloadRequest) -> None:
    """Regressão: com outtmpl absoluto, o corte de nome longo truncava o caminho
    inteiro e o arquivo saía com um pedaço do diretório como nome."""
    opcoes = _opcoes(Downloader(), pedido)
    assert opcoes["outtmpl"] == "%(title)s.%(ext)s"
    assert not Path(opcoes["outtmpl"]).is_absolute()
    assert opcoes["paths"]["home"] == str(pedido.output_dir)


def test_limite_de_nome_convive_com_o_diretorio(pedido: DownloadRequest) -> None:
    opcoes = _opcoes(Downloader(), pedido)
    assert opcoes["trim_file_name"] == 120
    assert opcoes["windowsfilenames"] is True


def test_video_pede_h264_para_compatibilidade(pedido: DownloadRequest) -> None:
    opcoes = _opcoes(Downloader(), pedido)
    assert opcoes["format_sort"][0] == "vcodec:h264"
    assert opcoes["merge_output_format"] == "mp4"
    assert "[height<=1080]" in opcoes["format"]


def test_audio_converte_para_o_codec_escolhido(pedido: DownloadRequest) -> None:
    pedido = DownloadRequest(
        url=pedido.url,
        kind=MediaKind.AUDIO,
        quality="320",
        container="mp3",
        output_dir=pedido.output_dir,
    )
    opcoes = _opcoes(Downloader(), pedido)

    extratores = [p for p in opcoes["postprocessors"] if p["key"] == "FFmpegExtractAudio"]
    assert len(extratores) == 1
    assert extratores[0]["preferredcodec"] == "mp3"
    assert extratores[0]["preferredquality"] == "320"
    assert "format_sort" not in opcoes  # só faz sentido para vídeo


def test_audio_em_m4a_nao_reconverte(pedido: DownloadRequest) -> None:
    """M4A já é o formato nativo entregue pelo YouTube; reconverter só perde
    qualidade e tempo."""
    pedido = DownloadRequest(
        url=pedido.url,
        kind=MediaKind.AUDIO,
        quality="192",
        container="m4a",
        output_dir=pedido.output_dir,
    )
    opcoes = _opcoes(Downloader(), pedido)
    chaves = [p["key"] for p in opcoes.get("postprocessors", [])]
    assert "FFmpegExtractAudio" not in chaves


def test_legendas_so_entram_quando_pedidas(pedido: DownloadRequest) -> None:
    assert "writesubtitles" not in _opcoes(Downloader(), pedido)

    com_legenda = DownloadRequest(
        url=pedido.url,
        kind=MediaKind.VIDEO,
        quality="720p",
        container="mp4",
        output_dir=pedido.output_dir,
        write_subtitles=True,
    )
    opcoes = _opcoes(Downloader(), com_legenda)
    assert opcoes["writesubtitles"] is True
    assert "FFmpegEmbedSubtitle" in [p["key"] for p in opcoes["postprocessors"]]


def test_cookies_so_vao_quando_um_navegador_e_escolhido(pedido: DownloadRequest) -> None:
    assert "cookiesfrombrowser" not in _opcoes(Downloader("nenhum"), pedido)
    assert _opcoes(Downloader("firefox"), pedido)["cookiesfrombrowser"] == ("firefox",)


def test_qualidade_incoerente_com_o_tipo_e_corrigida(tmp_path: Path) -> None:
    """Trocar de vídeo para áudio não pode deixar '1080p' como taxa de bits."""
    pedido = DownloadRequest(
        url="https://youtu.be/dQw4w9WgXcQ",
        kind=MediaKind.AUDIO,
        quality="1080p",
        container="mp4",
        output_dir=tmp_path,
    ).normalized()
    assert pedido.quality == "192"
    assert pedido.container == "mp3"


# ── Localização do arquivo final ─────────────────────────────────────────


def test_encontra_o_arquivo_informado_pelo_ytdlp(tmp_path: Path, pedido: DownloadRequest) -> None:
    arquivo = tmp_path / "Video.mp4"
    arquivo.write_bytes(b"x")
    info = {"requested_downloads": [{"filepath": str(arquivo)}]}
    assert Downloader._resolve_output_file(info, tmp_path, pedido) == arquivo


def test_acompanha_a_troca_de_extensao_apos_conversao(tmp_path: Path) -> None:
    """O yt-dlp informa o nome antes do pós-processamento; depois da conversão
    a extensão muda e o caminho original deixa de existir."""
    pedido = DownloadRequest(
        url="https://youtu.be/x",
        kind=MediaKind.AUDIO,
        quality="192",
        container="mp3",
        output_dir=tmp_path,
    )
    convertido = tmp_path / "Musica.mp3"
    convertido.write_bytes(b"x")
    info = {"requested_downloads": [{"filepath": str(tmp_path / "Musica.webm")}]}
    assert Downloader._resolve_output_file(info, tmp_path, pedido) == convertido


def test_recorre_ao_arquivo_mais_recente_quando_o_caminho_falha(
    tmp_path: Path, pedido: DownloadRequest
) -> None:
    recente = tmp_path / "Outro.mp4"
    recente.write_bytes(b"x")
    assert Downloader._resolve_output_file({}, tmp_path, pedido) == recente


def test_devolve_nada_quando_nao_ha_arquivo(tmp_path: Path, pedido: DownloadRequest) -> None:
    assert Downloader._resolve_output_file({}, tmp_path, pedido) is None


# ── Validação e pré-condições ────────────────────────────────────────────


@pytest.mark.parametrize("url", ["", "não é url", "file:///C:/Windows", "javascript:alert(1)"])
def test_consulta_recusa_endereco_invalido(url: str) -> None:
    with pytest.raises(DownloaderError):
        Downloader().fetch_info(url)


def test_video_sem_ffmpeg_falha_antes_de_baixar(
    monkeypatch: pytest.MonkeyPatch, pedido: DownloadRequest
) -> None:
    """Juntar vídeo e áudio exige FFmpeg. Melhor avisar na hora do que baixar
    centenas de megabytes para falhar no fim."""
    monkeypatch.setattr(ffmpeg_module, "is_available", lambda: False)
    with pytest.raises(FFmpegMissingError):
        Downloader().download(pedido)


def test_cancelamento_antes_de_comecar_nao_baixa_nada(
    monkeypatch: pytest.MonkeyPatch, pedido: DownloadRequest
) -> None:
    monkeypatch.setattr(ffmpeg_module, "is_available", lambda: True)
    cancelado = threading.Event()
    cancelado.set()

    from ytdownloader.core.errors import DownloadCancelled

    with pytest.raises(DownloadCancelled):
        Downloader().download(pedido, cancel_event=cancelado)
