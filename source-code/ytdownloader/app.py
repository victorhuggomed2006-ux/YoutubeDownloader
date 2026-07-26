"""Ponto de entrada do aplicativo.

A ordem aqui importa: a atualização do yt-dlp precisa ser ativada antes de
qualquer import do motor de download, para que a versão baixada pelo usuário
tenha prioridade sobre a que veio embutida no executável.
"""

from __future__ import annotations

import logging
import sys

from .core import logging_setup, updater

logger = logging.getLogger(__name__)


def _install_excepthook() -> None:
    """Registra falhas não tratadas no log em vez de encerrar em silêncio."""

    def handler(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Erro não tratado", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handler


def _log_components() -> None:
    """Registra o estado dos componentes externos — ajuda a diagnosticar suporte."""
    from .core import ffmpeg, jsruntime, paths

    logger.info("Instalado em: %s", paths.install_dir())
    logger.info("Dados do usuário: %s", paths.app_data_dir())
    logger.info("yt-dlp: %s", updater.current_version())
    logger.info("FFmpeg: %s", ffmpeg.ffmpeg_path() or "não encontrado")
    logger.info("Runtimes JavaScript: %s", ", ".join(jsruntime.names()) or "nenhum")


def main() -> int:
    """Inicializa e executa a aplicação. Retorna o código de saída."""
    logging_setup.configure()
    _install_excepthook()

    activated = updater.activate()
    if activated:
        logger.info("Motor de download atualizado em uso: yt-dlp %s", activated)

    _log_components()

    # Importado só agora: o Qt é pesado e depende do sys.path já ajustado.
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from . import __app_name__, __author__, __version__
    from .core import paths
    from .core.history import HistoryStore
    from .core.settings import SettingsStore
    from .gui.main_window import MainWindow

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    # Sem setApplicationDisplayName: o Qt o acrescentaria ao título da janela,
    # que já traz o nome do aplicativo.
    app.setApplicationVersion(__version__)
    app.setOrganizationName(__author__)

    for name in ("icon.ico", "icon.png"):
        candidate = paths.resource_path(name)
        if candidate.is_file():
            app.setWindowIcon(QIcon(str(candidate)))
            break

    settings_store = SettingsStore()
    history_store = HistoryStore()

    from .gui import i18n

    idioma = i18n.instalar(app, settings_store.settings.language)
    logger.info("Idioma da interface: %s", idioma)

    window = MainWindow(settings_store, history_store)
    window.show()

    logger.info("%s %s iniciado", __app_name__, __version__)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
