"""Tradução da interface.

O código-fonte é escrito em português, e é o português que serve de chave para
as traduções — é a convenção do Qt: a string escrita no código é o texto de
origem, e cada idioma traduzido é um arquivo à parte.

O núcleo (``ytdownloader.core``) não importa nada do Qt, então suas mensagens
não podem chamar ``tr()`` diretamente. Elas são declaradas aqui, em
``_declarar_mensagens_do_nucleo``, para que a ferramenta de extração as
encontre, e traduzidas em tempo de execução por :func:`traduzir_do_nucleo`.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QTranslator

from ..core import paths

logger = logging.getLogger(__name__)

#: Contexto usado nas mensagens que nascem no núcleo.
CONTEXTO_NUCLEO = "Nucleo"

#: Idiomas oferecidos. A chave é o código usado nos arquivos de tradução.
IDIOMAS: dict[str, str] = {
    "auto": "Igual ao Windows",
    "pt_BR": "Português (Brasil)",
    "en": "English",
}

_tradutores: list[QTranslator] = []


def traduzir_do_nucleo(mensagem: str) -> str:
    """Traduz uma mensagem vinda do núcleo, se houver tradução para ela."""
    if not mensagem:
        return mensagem
    return QCoreApplication.translate(CONTEXTO_NUCLEO, mensagem)


def idioma_efetivo(preferencia: str) -> str:
    """Resolve ``auto`` para o idioma do sistema."""
    if preferencia in IDIOMAS and preferencia != "auto":
        return preferencia

    sistema = QLocale.system().name()  # por exemplo "pt_BR" ou "en_US"
    if sistema.startswith("pt"):
        return "pt_BR"
    return "en"


def instalar(app: QCoreApplication, preferencia: str = "auto") -> str:
    """Instala o tradutor do idioma escolhido e devolve o idioma em uso.

    O português é o idioma de origem: não há arquivo a carregar, as strings do
    código já estão nele.
    """
    global _tradutores

    for tradutor in _tradutores:
        app.removeTranslator(tradutor)
    _tradutores = []

    idioma = idioma_efetivo(preferencia)
    if idioma == "pt_BR":
        return idioma

    arquivo = paths.resource_path("i18n", f"ytdownloader_{idioma}.qm")
    if not arquivo.is_file():
        logger.warning("Tradução para %s não encontrada em %s", idioma, arquivo)
        return "pt_BR"

    tradutor = QTranslator()
    if not tradutor.load(str(arquivo)):
        logger.warning("Não foi possível carregar a tradução %s", arquivo)
        return "pt_BR"

    app.installTranslator(tradutor)
    _tradutores.append(tradutor)

    # Traduz também os textos próprios do Qt (botões de diálogo, menus de
    # contexto dos campos de texto), que têm catálogo pronto.
    qt_tradutor = QTranslator()
    caminho_qt = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if qt_tradutor.load(QLocale(idioma), "qtbase", "_", caminho_qt):
        app.installTranslator(qt_tradutor)
        _tradutores.append(qt_tradutor)

    logger.info("Idioma da interface: %s", idioma)
    return idioma


def _declarar_mensagens_do_nucleo() -> None:
    """Torna visíveis à ferramenta de extração as mensagens do núcleo.

    Esta função nunca é chamada. Ela existe para que ``pyside6-lupdate``
    encontre as mensagens que o núcleo produz e as inclua no arquivo de
    tradução — sem ela, seria preciso mantê-las à mão.
    """
    # Erros de download (core/errors.py)
    QCoreApplication.translate("Nucleo", "O YouTube pediu verificação de conta para este vídeo.")
    QCoreApplication.translate(
        "Nucleo",
        "Em Configurações, ative a importação de cookies do seu navegador e tente de novo.",
    )
    QCoreApplication.translate("Nucleo", "Este vídeo é privado.")
    QCoreApplication.translate("Nucleo", "Só o dono do canal consegue acessá-lo.")
    QCoreApplication.translate("Nucleo", "Este vídeo é exclusivo para membros do canal.")
    QCoreApplication.translate("Nucleo", "É preciso ser membro e usar os cookies da sua conta.")
    QCoreApplication.translate("Nucleo", "Este vídeo tem restrição de idade.")
    QCoreApplication.translate(
        "Nucleo", "Ative a importação de cookies do navegador em Configurações."
    )
    QCoreApplication.translate("Nucleo", "Vídeo indisponível ou removido.")
    QCoreApplication.translate("Nucleo", "Este vídeo está bloqueado na sua região.")
    QCoreApplication.translate("Nucleo", "A transmissão ainda não começou.")
    QCoreApplication.translate("Nucleo", "Tente novamente quando o vídeo estiver disponível.")
    QCoreApplication.translate(
        "Nucleo", "Não é possível baixar uma transmissão ao vivo em andamento."
    )
    QCoreApplication.translate("Nucleo", "Espere a live terminar e baixe a gravação.")
    QCoreApplication.translate(
        "Nucleo", "A qualidade escolhida não está disponível para este vídeo."
    )
    QCoreApplication.translate("Nucleo", 'Escolha outra qualidade ou use "Máxima disponível".')
    QCoreApplication.translate("Nucleo", "Falha de conexão com o YouTube.")
    QCoreApplication.translate("Nucleo", "Verifique sua internet e tente novamente.")
    QCoreApplication.translate("Nucleo", "Falha ao processar o arquivo com o FFmpeg.")
    QCoreApplication.translate("Nucleo", "Reinstale o aplicativo para restaurar os componentes.")
    QCoreApplication.translate("Nucleo", "Este link não é um vídeo do YouTube.")
    QCoreApplication.translate("Nucleo", "Sem permissão para gravar na pasta escolhida.")
    QCoreApplication.translate("Nucleo", "Escolha outra pasta de destino.")
    QCoreApplication.translate("Nucleo", "Espaço insuficiente em disco.")
    QCoreApplication.translate("Nucleo", "Libere espaço e tente novamente.")
    QCoreApplication.translate("Nucleo", "Não foi possível concluir o download.")
    QCoreApplication.translate("Nucleo", "Download cancelado.")
    QCoreApplication.translate("Nucleo", "FFmpeg não encontrado.")
    QCoreApplication.translate(
        "Nucleo", "Reinstale o aplicativo ou instale o FFmpeg e adicione-o ao PATH."
    )
    QCoreApplication.translate("Nucleo", "Este endereço não é um link de vídeo válido.")
    QCoreApplication.translate("Nucleo", "Este endereço não é um link válido.")
    QCoreApplication.translate("Nucleo", "Não foi possível ler as informações do vídeo.")
    QCoreApplication.translate("Nucleo", "Esta playlist está vazia ou é privada.")
    QCoreApplication.translate("Nucleo", "Não foi possível ler a lista de vídeos.")
    QCoreApplication.translate("Nucleo", "Este endereço aponta para um vídeo único, não uma lista.")
    QCoreApplication.translate("Nucleo", "O download não produziu nenhum arquivo.")
    QCoreApplication.translate("Nucleo", "O arquivo baixado não foi encontrado no disco.")

    # Situações de uma tarefa (core/models.py)
    QCoreApplication.translate("Nucleo", "Na fila")
    QCoreApplication.translate("Nucleo", "Consultando")
    QCoreApplication.translate("Nucleo", "Baixando")
    QCoreApplication.translate("Nucleo", "Convertendo")
    QCoreApplication.translate("Nucleo", "Concluído")
    QCoreApplication.translate("Nucleo", "Falhou")
    QCoreApplication.translate("Nucleo", "Cancelado")

    # Andamento do processamento (core/downloader.py)
    QCoreApplication.translate("Nucleo", "Consultando o vídeo...")
    QCoreApplication.translate("Nucleo", "Finalizando arquivo...")
    QCoreApplication.translate("Nucleo", "Convertendo o áudio...")
    QCoreApplication.translate("Nucleo", "Juntando vídeo e áudio...")
    QCoreApplication.translate("Nucleo", "Convertendo o vídeo...")
    QCoreApplication.translate("Nucleo", "Aplicando a capa...")
    QCoreApplication.translate("Nucleo", "Gravando as informações...")
    QCoreApplication.translate("Nucleo", "Incorporando as legendas...")
    QCoreApplication.translate("Nucleo", "Salvando na pasta de destino...")
    QCoreApplication.translate("Nucleo", "Processando o arquivo...")

    # Qualidades e formatos (core/formats.py). Rótulos como "Full HD · 1080p"
    # não entram: são iguais em qualquer idioma.
    QCoreApplication.translate("Nucleo", "Baixa · 360p")
    QCoreApplication.translate("Nucleo", "Máxima disponível")
    QCoreApplication.translate("Nucleo", "Melhor resolução que o vídeo oferecer")
    QCoreApplication.translate("Nucleo", "Arquivos bem grandes")
    QCoreApplication.translate("Nucleo", "Alta qualidade")
    QCoreApplication.translate("Nucleo", "Melhor equilíbrio entre qualidade e tamanho")
    QCoreApplication.translate("Nucleo", "Leve e compatível com tudo")
    QCoreApplication.translate("Nucleo", "Economiza espaço")
    QCoreApplication.translate("Nucleo", "Menor arquivo possível")
    QCoreApplication.translate("Nucleo", "Qualidade máxima de áudio")
    QCoreApplication.translate("Nucleo", "Padrão recomendado")
    QCoreApplication.translate("Nucleo", "Arquivo menor")
