"""Janela de configurações."""

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
from ..i18n import IDIOMAS

THEME_LABELS = (("Escuro", "dark"), ("Claro", "light"))


class SettingsDialog(QDialog):
    """Permite ajustar pasta de destino, aparência e comportamento."""

    def __init__(self, store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self.setWindowTitle(self.tr("Configurações"))
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
        browse = QPushButton(self.tr("Escolher..."))
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self._choose_folder)
        folder_row.addWidget(browse)
        downloads_form.addRow(self.tr("Pasta de destino"), folder_row)

        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 5)
        self._concurrent_spin.setValue(max(1, min(settings.max_concurrent_downloads, 5)))
        downloads_form.addRow(self.tr("Downloads ao mesmo tempo"), self._concurrent_spin)

        self._open_folder_check = QCheckBox(self.tr("Abrir a pasta quando o download terminar"))
        self._open_folder_check.setChecked(settings.open_folder_when_done)
        downloads_form.addRow("", self._open_folder_check)

        layout.addWidget(downloads_group)

        # ── Arquivo gerado ───────────────────────────────────────────────
        file_group = QGroupBox(self.tr("Arquivo gerado"))
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(9)

        self._thumbnail_check = QCheckBox(self.tr("Incorporar a miniatura como capa"))
        self._thumbnail_check.setChecked(settings.embed_thumbnail)
        file_layout.addWidget(self._thumbnail_check)

        self._metadata_check = QCheckBox(self.tr("Gravar título e canal nos metadados"))
        self._metadata_check.setChecked(settings.embed_metadata)
        file_layout.addWidget(self._metadata_check)

        self._subtitles_check = QCheckBox(self.tr("Incluir legendas nos vídeos, quando existirem"))
        self._subtitles_check.setChecked(settings.write_subtitles)
        file_layout.addWidget(self._subtitles_check)

        layout.addWidget(file_group)

        # ── Acesso aos sites ─────────────────────────────────────────────
        access_group = QGroupBox(self.tr("Acesso aos sites"))
        access_form = QFormLayout(access_group)
        access_form.setSpacing(11)

        self._cookies_combo = QComboBox()
        for browser in COOKIE_BROWSERS:
            label = self.tr("Não usar") if browser == "nenhum" else browser.capitalize()
            self._cookies_combo.addItem(label, browser)
        index = self._cookies_combo.findData(settings.cookies_from_browser)
        self._cookies_combo.setCurrentIndex(index if index >= 0 else 0)
        access_form.addRow(self.tr("Usar cookies do navegador"), self._cookies_combo)

        cookies_hint = QLabel(
            self.tr(
                "Usar os cookies do navegador em que você já está logado resolve os pedidos "
                'de "confirme que você não é um robô" e libera vídeos com restrição de idade. '
                "Feche o navegador antes de baixar para que ele libere o arquivo de cookies."
            )
        )
        cookies_hint.setObjectName("FieldHint")
        cookies_hint.setWordWrap(True)
        access_form.addRow("", cookies_hint)

        layout.addWidget(access_group)

        # ── Aparência e componentes ──────────────────────────────────────
        app_group = QGroupBox(self.tr("Aparência e componentes"))
        app_form = QFormLayout(app_group)
        app_form.setSpacing(11)

        self._language_combo = QComboBox()
        for codigo, nome in IDIOMAS.items():
            rotulo = self.tr("Igual ao Windows") if codigo == "auto" else nome
            self._language_combo.addItem(rotulo, codigo)
        idioma_index = self._language_combo.findData(settings.language)
        self._language_combo.setCurrentIndex(idioma_index if idioma_index >= 0 else 0)
        self._idioma_inicial = settings.language
        app_form.addRow(self.tr("Idioma"), self._language_combo)

        self._theme_combo = QComboBox()
        for label, value in THEME_LABELS:
            self._theme_combo.addItem(self.tr(label), value)
        theme_index = self._theme_combo.findData(settings.theme)
        self._theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        app_form.addRow(self.tr("Tema"), self._theme_combo)

        self._updates_check = QCheckBox(
            self.tr("Procurar atualizações do motor de download ao abrir")
        )
        self._updates_check.setChecked(settings.check_ytdlp_updates)
        app_form.addRow("", self._updates_check)

        ffmpeg_path = ffmpeg_module.ffmpeg_path()
        status = str(ffmpeg_path) if ffmpeg_path else self.tr("não encontrado")
        components = QLabel(
            self.tr("Motor de download: yt-dlp {versao}\nFFmpeg: {ffmpeg}").format(
                versao=updater.current_version(), ffmpeg=status
            )
        )
        components.setObjectName("FieldHint")
        components.setWordWrap(True)
        app_form.addRow(self.tr("Componentes"), components)

        layout.addWidget(app_group)
        layout.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self.tr("Salvar"))
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("PrimaryButton")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancelar"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, self.tr("Escolha a pasta de destino"), self._folder_edit.text()
        )
        if chosen:
            self._folder_edit.setText(chosen)

    @property
    def language_changed(self) -> bool:
        """Indica se o idioma escolhido difere do que estava salvo."""
        return self._language_combo.currentData() != self._idioma_inicial

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
