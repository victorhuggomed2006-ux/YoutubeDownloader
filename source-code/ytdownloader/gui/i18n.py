"""Interface translation.

The source code is written in English, and English is what serves as the key
for translations — that is the Qt convention: the string written in the code is
the source text, and each translated language is a separate catalogue.

The core (``ytdownloader.core``) imports nothing from Qt, so its messages
cannot call ``tr()`` directly. They are declared here, in
``_declare_core_messages``, so the extraction tool finds them, and translated at
runtime by :func:`translate_core`.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QTranslator

from ..core import paths

logger = logging.getLogger(__name__)

#: Context used for messages that originate in the core.
CORE_CONTEXT = "Core"

#: Languages on offer. The key is the code used in the translation files.
LANGUAGES: dict[str, str] = {
    "auto": "Same as Windows",
    "en": "English",
    "pt_BR": "Português (Brasil)",
    "es": "Español",
}

_translators: list[QTranslator] = []


def translate_core(message: str) -> str:
    """Translate a message coming from the core, if a translation exists."""
    if not message:
        return message
    return QCoreApplication.translate(CORE_CONTEXT, message)


def match_language(tags: list[str]) -> str:
    """Pick the first tag we have a catalogue for, in the order Windows ranks them.

    Tags arrive in BCP 47 form and may carry a script: ``pt-Latn-BR``, ``es-419``.
    Only the primary subtag is needed to choose between the three catalogues.
    """
    for tag in tags:
        primary = tag.replace("_", "-").split("-", 1)[0].lower()
        if primary == "pt":
            return "pt_BR"
        if primary == "es":
            return "es"
        if primary == "en":
            return "en"
    return "en"


def effective_language(preference: str) -> str:
    """Resolve ``auto`` to the Windows display language."""
    if preference in LANGUAGES and preference != "auto":
        return preference

    # uiLanguages(), not name(): the latter follows the regional *format*
    # setting, which on a Brazilian machine with an English keyboard layout
    # reports en_US while the interface is in Portuguese.
    system = QLocale.system()
    return match_language([*system.uiLanguages(), system.name()])


def install(app: QCoreApplication, preference: str = "auto") -> str:
    """Install the chosen language and return the one in use.

    English is the source language: there is no catalogue to load, since the
    strings in the code are already in it.
    """
    global _translators

    for translator in _translators:
        app.removeTranslator(translator)
    _translators = []

    language = effective_language(preference)
    if language == "en":
        return language

    catalogue = paths.resource_path("i18n", f"ytdownloader_{language}.qm")
    if not catalogue.is_file():
        logger.warning("Translation for %s not found at %s", language, catalogue)
        return "en"

    translator = QTranslator()
    if not translator.load(str(catalogue)):
        logger.warning("Could not load the translation %s", catalogue)
        return "en"

    app.installTranslator(translator)
    _translators.append(translator)

    # Also translate Qt's own text — dialog buttons, text field context menus —
    # which ships with ready-made catalogues.
    qt_translator = QTranslator()
    qt_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if qt_translator.load(QLocale(language), "qtbase", "_", qt_path):
        app.installTranslator(qt_translator)
        _translators.append(qt_translator)

    logger.info("Interface language: %s", language)
    return language


def _declare_core_messages() -> None:
    """Expose the core's messages to the extraction tool.

    This function is never called. It exists so ``pyside6-lupdate`` finds the
    messages the core produces and includes them in the translation files —
    without it, they would have to be maintained by hand.
    """
    # Download errors (core/errors.py)
    QCoreApplication.translate("Core", "The site asked for account verification on this video.")
    QCoreApplication.translate("Core", "In Settings, turn on browser cookie import and try again.")
    QCoreApplication.translate("Core", "This video is private.")
    QCoreApplication.translate("Core", "Only the channel owner can access it.")
    QCoreApplication.translate("Core", "This video is for channel members only.")
    QCoreApplication.translate("Core", "You need to be a member and use your account cookies.")
    QCoreApplication.translate("Core", "This video is age-restricted.")
    QCoreApplication.translate("Core", "Turn on browser cookie import in Settings.")
    QCoreApplication.translate("Core", "Video unavailable or removed.")
    QCoreApplication.translate("Core", "This video is blocked in your region.")
    QCoreApplication.translate("Core", "The stream has not started yet.")
    QCoreApplication.translate("Core", "Try again once the video is available.")
    QCoreApplication.translate("Core", "A live stream in progress cannot be downloaded.")
    QCoreApplication.translate("Core", "Wait for the stream to end and download the recording.")
    QCoreApplication.translate("Core", "The selected quality is not available for this video.")
    QCoreApplication.translate("Core", 'Pick another quality or use "Best available".')
    QCoreApplication.translate("Core", "Connection failed.")
    QCoreApplication.translate("Core", "Check your internet connection and try again.")
    QCoreApplication.translate("Core", "FFmpeg failed to process the file.")
    QCoreApplication.translate("Core", "Reinstall the app to restore its components.")
    QCoreApplication.translate("Core", "This site is not supported.")
    QCoreApplication.translate("Core", "No permission to write to the selected folder.")
    QCoreApplication.translate("Core", "Choose a different destination folder.")
    QCoreApplication.translate("Core", "Not enough disk space.")
    QCoreApplication.translate("Core", "Free up some space and try again.")
    QCoreApplication.translate("Core", "The download could not be completed.")
    QCoreApplication.translate("Core", "Download cancelled.")
    QCoreApplication.translate("Core", "FFmpeg not found.")
    QCoreApplication.translate(
        "Core", "Reinstall the app, or install FFmpeg and add it to your PATH."
    )
    QCoreApplication.translate("Core", "This address is not a valid video link.")
    QCoreApplication.translate("Core", "This address is not a valid link.")
    QCoreApplication.translate("Core", "Could not read the video details.")
    QCoreApplication.translate("Core", "This playlist is empty or private.")
    QCoreApplication.translate("Core", "Could not read the video list.")
    QCoreApplication.translate("Core", "This address points to a single video, not a list.")
    QCoreApplication.translate("Core", "The download produced no file.")
    QCoreApplication.translate("Core", "The downloaded file was not found on disk.")

    # Task states (core/models.py)
    QCoreApplication.translate("Core", "Queued")
    QCoreApplication.translate("Core", "Looking up")
    QCoreApplication.translate("Core", "Downloading")
    QCoreApplication.translate("Core", "Converting")
    QCoreApplication.translate("Core", "Done")
    QCoreApplication.translate("Core", "Failed")
    QCoreApplication.translate("Core", "Cancelled")
    QCoreApplication.translate("Core", "Untitled")

    # Processing progress (core/downloader.py)
    QCoreApplication.translate("Core", "Looking up the video...")
    QCoreApplication.translate("Core", "Finishing the file...")
    QCoreApplication.translate("Core", "Converting the audio...")
    QCoreApplication.translate("Core", "Merging video and audio...")
    QCoreApplication.translate("Core", "Converting the video...")
    QCoreApplication.translate("Core", "Applying the cover art...")
    QCoreApplication.translate("Core", "Writing the metadata...")
    QCoreApplication.translate("Core", "Embedding the subtitles...")
    QCoreApplication.translate("Core", "Saving to the destination folder...")
    QCoreApplication.translate("Core", "Processing the file...")

    # Qualities and formats (core/formats.py). Labels such as "Full HD · 1080p"
    # are left out: they read the same in any language.
    QCoreApplication.translate("Core", "Best available")
    QCoreApplication.translate("Core", "Low · 360p")
    QCoreApplication.translate("Core", "The highest resolution the video offers")
    QCoreApplication.translate("Core", "Very large files")
    QCoreApplication.translate("Core", "High quality")
    QCoreApplication.translate("Core", "Best balance of quality and size")
    QCoreApplication.translate("Core", "Light and plays everywhere")
    QCoreApplication.translate("Core", "Saves space")
    QCoreApplication.translate("Core", "Smallest possible file")
    QCoreApplication.translate("Core", "Top audio quality")
    QCoreApplication.translate("Core", "Recommended default")
    QCoreApplication.translate("Core", "Smaller file")
