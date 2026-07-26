"""The application entry point.

Order matters here: the yt-dlp update must be activated before anything imports
the download engine, so the version downloaded by the user takes precedence
over the one bundled in the executable.
"""

from __future__ import annotations

import logging
import sys

from .core import logging_setup, updater

logger = logging.getLogger(__name__)


def _install_excepthook() -> None:
    """Log unhandled failures instead of dying silently."""

    def handler(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Unhandled error", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handler


def _log_components() -> None:
    """Record the state of the external components — this is what makes a bug
    report actionable."""
    from .core import ffmpeg, jsruntime, paths

    logger.info("Installed at: %s", paths.install_dir())
    logger.info("User data: %s", paths.app_data_dir())
    logger.info("yt-dlp: %s", updater.current_version())
    logger.info("FFmpeg: %s", ffmpeg.ffmpeg_path() or "not found")
    logger.info("JavaScript runtimes: %s", ", ".join(jsruntime.names()) or "none")


def main() -> int:
    """Start and run the application. Returns the exit code."""
    logging_setup.configure()
    _install_excepthook()

    activated = updater.activate()
    if activated:
        logger.info("Updated download engine in use: yt-dlp %s", activated)

    _log_components()

    # Imported only now: Qt is heavy and depends on sys.path being set already.
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from . import __app_name__, __author__, __version__
    from .core import paths
    from .core.history import HistoryStore
    from .core.settings import SettingsStore
    from .gui import i18n
    from .gui.main_window import MainWindow

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    # No setApplicationDisplayName: Qt would append it to the window title,
    # which already carries the application name.
    app.setApplicationVersion(__version__)
    app.setOrganizationName(__author__)

    for name in ("icon.ico", "icon.png"):
        candidate = paths.resource_path(name)
        if candidate.is_file():
            app.setWindowIcon(QIcon(str(candidate)))
            break

    settings_store = SettingsStore()
    history_store = HistoryStore()

    # Must run before the window is built: Qt only translates widgets created
    # after the translator is installed.
    language = i18n.install(app, settings_store.settings.language)
    logger.info("Interface language: %s", language)

    window = MainWindow(settings_store, history_store)
    window.show()

    logger.info("%s %s started", __app_name__, __version__)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
