"""Testes de validação e normalização de endereços."""

from __future__ import annotations

import pytest

from ytdownloader.core.urls import (
    format_duration,
    format_eta,
    format_size,
    format_speed,
    is_supported_url,
    parse_url,
)

VIDEO_ID = "dQw4w9WgXcQ"


# ── YouTube ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com/watch?v={VIDEO_ID}",
        f"http://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://music.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?t=42",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}",
        f"youtube.com/watch?v={VIDEO_ID}",  # sem esquema, como se costuma colar
        f"  https://youtu.be/{VIDEO_ID}  ",  # com espaços em volta
    ],
)
def test_extrai_id_de_video(url: str) -> None:
    parsed = parse_url(url)
    assert parsed.is_supported
    assert parsed.is_youtube
    assert parsed.video_id == VIDEO_ID
    assert parsed.canonical == f"https://www.youtube.com/watch?v={VIDEO_ID}"


def test_playlist_pura() -> None:
    parsed = parse_url("https://www.youtube.com/playlist?list=PLabc123def")
    assert parsed.is_supported
    assert parsed.is_playlist
    assert parsed.playlist_id == "PLabc123def"
    assert parsed.video_id is None
    assert parsed.canonical == "https://www.youtube.com/playlist?list=PLabc123def"


def test_video_dentro_de_playlist_baixa_apenas_o_video() -> None:
    parsed = parse_url(f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PLabc123")
    assert parsed.video_id == VIDEO_ID
    assert parsed.playlist_id == "PLabc123"
    assert not parsed.is_playlist  # o vídeo tem prioridade sobre a lista


def test_mix_gerado_pelo_youtube_nao_conta_como_playlist() -> None:
    parsed = parse_url(f"https://www.youtube.com/watch?v={VIDEO_ID}&list=RD{VIDEO_ID}")
    assert parsed.video_id == VIDEO_ID
    assert parsed.playlist_id is None


def test_url_da_miniatura_so_existe_para_o_youtube() -> None:
    assert parse_url(f"https://youtu.be/{VIDEO_ID}").thumbnail_url == (
        f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg"
    )
    assert parse_url("https://vimeo.com/123456").thumbnail_url is None


def test_endereco_do_youtube_sem_video_nao_serve() -> None:
    """A home e a busca do YouTube não apontam para nada baixável."""
    assert not parse_url("https://www.youtube.com/").is_supported
    assert not parse_url("https://www.youtube.com/results?search_query=teste").is_supported
    assert not parse_url("https://www.youtube.com/watch?v=curto").is_supported


# ── Outros sites ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("url", "nome"),
    [
        ("https://vimeo.com/123456", "Vimeo"),
        ("https://www.twitch.tv/videos/123", "Twitch"),
        ("https://soundcloud.com/artista/faixa", "SoundCloud"),
        ("https://www.dailymotion.com/video/x8abc", "Dailymotion"),
        ("https://x.com/usuario/status/123", "X"),
        ("https://www.reddit.com/r/videos/comments/abc/titulo/", "Reddit"),
        ("https://artista.bandcamp.com/track/musica", "Bandcamp"),
    ],
)
def test_aceita_outros_sites_e_reconhece_o_nome(url: str, nome: str) -> None:
    parsed = parse_url(url)
    assert parsed.is_supported
    assert not parsed.is_youtube
    assert parsed.site_name == nome


def test_site_desconhecido_e_aceito_com_o_dominio_como_nome() -> None:
    """Quem decide se sabe extrair é o yt-dlp, não esta validação."""
    parsed = parse_url("https://www.site-de-video-obscuro.com.br/assistir/123")
    assert parsed.is_supported
    assert parsed.site_name == "site-de-video-obscuro.com.br"


def test_endereco_de_outro_site_nao_e_reescrito() -> None:
    """Cada site tem sua convenção; reescrever o endereço quebraria o link."""
    url = "https://vimeo.com/123456?parametro=importante"
    assert parse_url(url).canonical == url


def test_endereco_sem_esquema_recebe_https() -> None:
    assert parse_url("vimeo.com/123456").canonical == "https://vimeo.com/123456"


# ── Recusas ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "não é uma url",
        "javascript:alert(1)",
        "file:///C:/Windows/System32/config/SAM",
        "ftp://exemplo.com/video.mp4",
        "data:text/html,<script>alert(1)</script>",
        "http://",
        "https://semdominio",  # sem ponto: não é um host público
        "https://-invalido-.com",
    ],
)
def test_recusa_enderecos_invalidos_ou_perigosos(url: str) -> None:
    assert not parse_url(url).is_supported
    assert not is_supported_url(url)


def test_recusa_esquemas_que_nao_sejam_http() -> None:
    """Só http e https: os demais não têm o que fazer num downloader."""
    for esquema in ("file", "ftp", "javascript", "data", "smb"):
        assert not is_supported_url(f"{esquema}://exemplo.com/coisa")


# ── Formatação ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("segundos", "esperado"),
    [
        (None, "--:--"),
        (0, "--:--"),
        (-5, "--:--"),
        (45, "00:45"),
        (60, "01:00"),
        (599, "09:59"),
        (3600, "1:00:00"),
        (3725, "1:02:05"),
        (86399, "23:59:59"),
    ],
)
def test_formata_duracao(segundos, esperado: str) -> None:
    assert format_duration(segundos) == esperado


@pytest.mark.parametrize(
    ("bytes_", "esperado"),
    [
        (None, "--"),
        (0, "--"),
        (512, "512 B"),
        (2048, "2 KB"),
        (15 * 1024 * 1024, "15.0 MB"),
        (3 * 1024 * 1024 * 1024, "3.0 GB"),
    ],
)
def test_formata_tamanho(bytes_, esperado: str) -> None:
    assert format_size(bytes_) == esperado


def test_formata_velocidade_e_tempo_restante() -> None:
    assert format_speed(1024 * 1024) == "1.0 MB/s"
    assert format_speed(None) == "--"
    assert format_eta(90) == "01:30"
    assert format_eta(None) == "--"
