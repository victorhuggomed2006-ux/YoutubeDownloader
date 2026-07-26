"""Janela "Sobre", com os créditos e a licença do projeto."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
)

from ... import (
    __app_name__,
    __author__,
    __author_title__,
    __copyright__,
    __url__,
    __version__,
)
from ...core import ffmpeg as ffmpeg_module
from ...core import paths, updater

CREDITS_HTML = f"""
<p><b>Feito por {__author__}</b><br>
<span style="color:#949bab">{__author_title__}</span></p>
<p><b>Licença:</b> MIT — o código é livre para usar, estudar, modificar e
distribuir, mantendo o aviso de copyright.</p>
<p><b>Repositório:</b> <a href="{__url__}">{__url__}</a></p>
<hr>
<p><b>Construído sobre:</b></p>
<ul>
  <li><a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a> — extração e download (licença Unlicense)</li>
  <li><a href="https://www.qt.io/qt-for-python">PySide6 / Qt</a> — interface gráfica (licença LGPLv3)</li>
  <li><a href="https://ffmpeg.org">FFmpeg</a> — conversão e junção das faixas (licença LGPLv2.1+)</li>
</ul>
<hr>
<p><b>Uso responsável:</b> baixe apenas conteúdo que você tem o direito de
guardar — material próprio, de domínio público, com licença aberta ou com
autorização de quem publicou. Respeite os termos de serviço de cada site e a
legislação de direitos autorais do seu país.</p>
"""


class AboutDialog(QDialog):
    """Mostra versão, créditos e informações de licença."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Sobre o {__app_name__}")
        self.setMinimumSize(560, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(6)

        title = QLabel(__app_name__)
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        version = QLabel(f"Versão {__version__}  ·  {__copyright__}")
        version.setObjectName("AppSubtitle")
        layout.addWidget(version)

        ffmpeg_path = ffmpeg_module.ffmpeg_path()
        components = QLabel(
            f"yt-dlp {updater.current_version()}  ·  "
            f"FFmpeg {'incluído' if ffmpeg_path else 'ausente'}"
        )
        components.setObjectName("Muted")
        layout.addWidget(components)

        data_dir = QLabel(f"Dados do aplicativo: {paths.app_data_dir()}")
        data_dir.setObjectName("Muted")
        data_dir.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        data_dir.setWordWrap(True)
        layout.addWidget(data_dir)

        layout.addSpacing(8)

        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml(CREDITS_HTML)
        layout.addWidget(body, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(self.tr("Fechar"))
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
