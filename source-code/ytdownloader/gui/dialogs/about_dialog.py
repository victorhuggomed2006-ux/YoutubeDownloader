"""The About window: credits and licence information."""

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


class AboutDialog(QDialog):
    """Shows the version, credits and licence details."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("About {app}").format(app=__app_name__))
        self.setMinimumSize(560, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(6)

        title = QLabel(__app_name__)
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        version = QLabel(
            self.tr("Version {version}  ·  {copyright}").format(
                version=__version__, copyright=__copyright__
            )
        )
        version.setObjectName("AppSubtitle")
        layout.addWidget(version)

        ffmpeg_path = ffmpeg_module.ffmpeg_path()
        ffmpeg_state = self.tr("bundled") if ffmpeg_path else self.tr("missing")
        components = QLabel(f"yt-dlp {updater.current_version()}  ·  FFmpeg {ffmpeg_state}")
        components.setObjectName("Muted")
        layout.addWidget(components)

        data_dir = QLabel(self.tr("Application data: {folder}").format(folder=paths.app_data_dir()))
        data_dir.setObjectName("Muted")
        data_dir.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        data_dir.setWordWrap(True)
        layout.addWidget(data_dir)

        layout.addSpacing(8)

        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setHtml(self._credits_html())
        layout.addWidget(body, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(self.tr("Close"))
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _credits_html(self) -> str:
        """Built at runtime so the text follows the selected language."""
        return f"""
<p><b>{self.tr("Built by {author}").format(author=__author__)}</b><br>
<span style="color:#949bab">{__author_title__}</span></p>

<p><b>{self.tr("Licence:")}</b> {
            self.tr(
                "MIT — the code is free to use, study, modify and redistribute, as long as "
                "the copyright notice is kept."
            )
        }</p>

<p><b>{self.tr("Repository:")}</b> <a href="{__url__}">{__url__}</a></p>
<hr>
<p><b>{self.tr("Built on:")}</b></p>
<ul>
  <li><a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a> — {
            self.tr("extraction and download (Unlicense)")
        }</li>
  <li><a href="https://www.qt.io/qt-for-python">PySide6 / Qt</a> — {
            self.tr("graphical interface (LGPLv3)")
        }</li>
  <li><a href="https://ffmpeg.org">FFmpeg</a> — {
            self.tr("conversion and stream merging (LGPLv2.1+)")
        }</li>
</ul>
<hr>
<p><b>{self.tr("Responsible use:")}</b> {
            self.tr(
                "download only what you have the right to keep — your own material, public "
                "domain works, openly licensed content, or media you have permission to "
                "save. Respect each site's terms of service and the copyright law that "
                "applies to you."
            )
        }</p>
"""
