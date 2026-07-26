"""The Settings window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ...core import ffmpeg as ffmpeg_module
from ...core import updater
from ...core.settings import COOKIE_BROWSERS, SettingsStore
from ..i18n import LANGUAGES

THEME_KEYS = ("dark", "light")


class SettingsDialog(QDialog):
    """Lets the user adjust destination, appearance and behaviour."""

    def __init__(self, store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self.setWindowTitle(self.tr("Settings"))
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(14)

        settings = store.settings

        # ── Downloads ────────────────────────────────────────────────────
        downloads_group = QGroupBox(self.tr("Downloads"))
        downloads_form = QFormLayout(downloads_group)
        downloads_form.setSpacing(11)
        downloads_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit(str(settings.resolved_output_dir()))
        self._folder_edit.setReadOnly(True)
        folder_row.addWidget(self._folder_edit, 1)
        browse = QPushButton(self.tr("Browse..."))
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self._choose_folder)
        folder_row.addWidget(browse)
        downloads_form.addRow(self.tr("Destination folder"), folder_row)

        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 5)
        self._concurrent_spin.setValue(max(1, min(settings.max_concurrent_downloads, 5)))
        downloads_form.addRow(self.tr("Simultaneous downloads"), self._concurrent_spin)

        self._open_folder_check = QCheckBox(self.tr("Open the folder when the download finishes"))
        self._open_folder_check.setChecked(settings.open_folder_when_done)
        downloads_form.addRow("", self._open_folder_check)

        layout.addWidget(downloads_group)

        # ── Output file ──────────────────────────────────────────────────
        file_group = QGroupBox(self.tr("Output file"))
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(9)

        self._thumbnail_check = QCheckBox(self.tr("Embed the thumbnail as cover art"))
        self._thumbnail_check.setChecked(settings.embed_thumbnail)
        file_layout.addWidget(self._thumbnail_check)

        self._metadata_check = QCheckBox(self.tr("Write title and channel into the metadata"))
        self._metadata_check.setChecked(settings.embed_metadata)
        file_layout.addWidget(self._metadata_check)

        self._subtitles_check = QCheckBox(self.tr("Include subtitles in videos, when available"))
        self._subtitles_check.setChecked(settings.write_subtitles)
        file_layout.addWidget(self._subtitles_check)

        layout.addWidget(file_group)

        # ── Site access ──────────────────────────────────────────────────
        access_group = QGroupBox(self.tr("Site access"))
        access_form = QFormLayout(access_group)
        access_form.setSpacing(11)

        self._cookies_combo = QComboBox()
        for browser in COOKIE_BROWSERS:
            label = self.tr("Do not use") if browser == "none" else browser.capitalize()
            self._cookies_combo.addItem(label, browser)
        index = self._cookies_combo.findData(settings.cookies_from_browser)
        self._cookies_combo.setCurrentIndex(index if index >= 0 else 0)
        access_form.addRow(self.tr("Use cookies from browser"), self._cookies_combo)

        cookies_hint = QLabel(
            self.tr(
                "Using cookies from a browser where you are already signed in clears the "
                '"confirm you are not a bot" prompts and unlocks age-restricted videos. '
                "Close that browser before downloading so it releases the cookie file."
            )
        )
        cookies_hint.setObjectName("FieldHint")
        cookies_hint.setWordWrap(True)
        access_form.addRow("", cookies_hint)

        layout.addWidget(access_group)

        # ── Appearance and components ────────────────────────────────────
        app_group = QGroupBox(self.tr("Appearance and components"))
        app_form = QFormLayout(app_group)
        app_form.setSpacing(11)

        self._language_combo = QComboBox()
        for code, name in LANGUAGES.items():
            label = self.tr("Same as Windows") if code == "auto" else name
            self._language_combo.addItem(label, code)
        language_index = self._language_combo.findData(settings.language)
        self._language_combo.setCurrentIndex(language_index if language_index >= 0 else 0)
        self._initial_language = settings.language
        app_form.addRow(self.tr("Language"), self._language_combo)

        self._theme_combo = QComboBox()
        theme_labels = {"dark": self.tr("Dark"), "light": self.tr("Light")}
        for key in THEME_KEYS:
            self._theme_combo.addItem(theme_labels[key], key)
        theme_index = self._theme_combo.findData(settings.theme)
        self._theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        app_form.addRow(self.tr("Theme"), self._theme_combo)

        self._updates_check = QCheckBox(self.tr("Check for download engine updates on startup"))
        self._updates_check.setChecked(settings.check_ytdlp_updates)
        app_form.addRow("", self._updates_check)

        ffmpeg_path = ffmpeg_module.ffmpeg_path()
        status = str(ffmpeg_path) if ffmpeg_path else self.tr("not found")
        components = QLabel(
            self.tr("Download engine: yt-dlp {version}\nFFmpeg: {ffmpeg}").format(
                version=updater.current_version(), ffmpeg=status
            )
        )
        components.setObjectName("FieldHint")
        components.setWordWrap(True)
        app_form.addRow(self.tr("Components"), components)

        layout.addWidget(app_group)
        layout.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self.tr("Save"))
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("PrimaryButton")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, self.tr("Choose the destination folder"), self._folder_edit.text()
        )
        if chosen:
            self._folder_edit.setText(chosen)

    @property
    def language_changed(self) -> bool:
        """Whether the chosen language differs from the stored one."""
        return self._language_combo.currentData() != self._initial_language

    def accept(self) -> None:
        self._store.update(
            output_dir=self._folder_edit.text(),
            max_concurrent_downloads=self._concurrent_spin.value(),
            open_folder_when_done=self._open_folder_check.isChecked(),
            embed_thumbnail=self._thumbnail_check.isChecked(),
            embed_metadata=self._metadata_check.isChecked(),
            write_subtitles=self._subtitles_check.isChecked(),
            cookies_from_browser=self._cookies_combo.currentData(),
            theme=self._theme_combo.currentData(),
            language=self._language_combo.currentData(),
            check_ytdlp_updates=self._updates_check.isChecked(),
        )
        super().accept()
