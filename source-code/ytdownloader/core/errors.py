"""Exceções do aplicativo e tradução de erros do yt-dlp para linguagem clara."""

from __future__ import annotations

import re


class DownloaderError(Exception):
    """Erro de download já formatado para ser exibido ao usuário."""

    def __init__(self, message: str, *, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message} {self.hint}"
        return self.message


class DownloadCancelled(DownloaderError):
    """Levantada quando o usuário cancela o download em andamento."""

    def __init__(self, message: str = "Download cancelado.") -> None:
        super().__init__(message)


class FFmpegMissingError(DownloaderError):
    """Levantada quando a conversão exige FFmpeg e ele não foi encontrado."""

    def __init__(self) -> None:
        super().__init__(
            "FFmpeg não encontrado.",
            hint="Reinstale o aplicativo ou instale o FFmpeg e adicione-o ao PATH.",
        )


# Padrões do yt-dlp mapeados para mensagens em português.
_ERROR_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        r"sign in to confirm|not a bot|confirm your age.*sign in",
        "O YouTube pediu verificação de conta para este vídeo.",
        "Em Configurações, ative a importação de cookies do seu navegador e tente de novo.",
    ),
    (
        r"private video|this video is private",
        "Este vídeo é privado.",
        "Só o dono do canal consegue acessá-lo.",
    ),
    (
        r"members[- ]only|join this channel",
        "Este vídeo é exclusivo para membros do canal.",
        "É preciso ser membro e usar os cookies da sua conta.",
    ),
    (
        r"age[- ]restricted|inappropriate for some users|confirm your age",
        "Este vídeo tem restrição de idade.",
        "Ative a importação de cookies do navegador em Configurações.",
    ),
    (
        r"video unavailable|has been removed|no longer available|removed by the uploader",
        "Vídeo indisponível ou removido.",
        "",
    ),
    (
        # O YouTube usa "has not made this video available in your country",
        # além das variações com "blocked" e "geo-restricted".
        r"available in your country|blocked it in your country|geo.?(block|restrict)",
        "Este vídeo está bloqueado na sua região.",
        "",
    ),
    (
        r"live event will begin|premieres in|is not yet available",
        "A transmissão ainda não começou.",
        "Tente novamente quando o vídeo estiver disponível.",
    ),
    (
        r"live.*not.*download|is live",
        "Não é possível baixar uma transmissão ao vivo em andamento.",
        "Espere a live terminar e baixe a gravação.",
    ),
    (
        r"requested format is not available|no video formats found",
        "A qualidade escolhida não está disponível para este vídeo.",
        'Escolha outra qualidade ou use "Máxima disponível".',
    ),
    (
        r"unable to download|urlopen error|timed out|connection|network|getaddrinfo|resolve",
        "Falha de conexão com o YouTube.",
        "Verifique sua internet e tente novamente.",
    ),
    (
        r"ffmpeg|ffprobe",
        "Falha ao processar o arquivo com o FFmpeg.",
        "Reinstale o aplicativo para restaurar os componentes.",
    ),
    (
        r"unsupported url|is not a valid url",
        "Este link não é um vídeo do YouTube.",
        "",
    ),
    (
        r"permission denied|access is denied|errno 13",
        "Sem permissão para gravar na pasta escolhida.",
        "Escolha outra pasta de destino.",
    ),
    (
        r"no space left|errno 28|disk full",
        "Espaço insuficiente em disco.",
        "Libere espaço e tente novamente.",
    ),
)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_PREFIX_RE = re.compile(r"^\s*(ERROR|WARNING):\s*", re.IGNORECASE)


def clean_message(raw: str) -> str:
    """Remove códigos de cor e prefixos técnicos da mensagem do yt-dlp."""
    text = _ANSI_RE.sub("", str(raw or "")).strip()
    text = _PREFIX_RE.sub("", text)
    text = re.sub(r"\[[a-zA-Z0-9:_-]+\]\s*", "", text, count=1)
    return text.strip()


def humanize(raw: str | BaseException) -> DownloaderError:
    """Converte um erro cru do yt-dlp em um ``DownloaderError`` legível."""
    if isinstance(raw, DownloaderError):
        return raw

    text = clean_message(str(raw))
    lowered = text.lower()

    for pattern, message, hint in _ERROR_PATTERNS:
        if re.search(pattern, lowered):
            return DownloaderError(message, hint=hint)

    if not text:
        return DownloaderError("Não foi possível concluir o download.")

    # Mantém no máximo a primeira frase para não poluir a interface.
    first_line = text.splitlines()[0]
    if len(first_line) > 220:
        first_line = first_line[:217] + "..."
    return DownloaderError(first_line)
