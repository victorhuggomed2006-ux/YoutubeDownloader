"""Generates the application icon as .ico and .png.

The drawing is done with Qt itself, so there is no dependency on external
editors or extra image libraries. Run it with:

    python packaging/make_icon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

# Sizes Windows uses in different contexts (taskbar, program list, desktop,
# high-density displays).
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)

GRADIENT_START = QColor("#ff8551")
GRADIENT_END = QColor("#e8551f")
ARROW_COLOR = QColor("#ffffff")


def render(size: int) -> QPixmap:
    """Draw the icon: an orange rounded square with a download arrow."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, GRADIENT_START)
    gradient.setColorAt(1.0, GRADIENT_END)

    radius = size * 0.22
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(gradient))
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    # A downward arrow, with a solid base underneath.
    painter.setBrush(QBrush(ARROW_COLOR))

    shaft_width = size * 0.16
    shaft_top = size * 0.22
    shaft_bottom = size * 0.50
    painter.drawRoundedRect(
        QRectF((size - shaft_width) / 2, shaft_top, shaft_width, shaft_bottom - shaft_top),
        shaft_width * 0.35,
        shaft_width * 0.35,
    )

    head = QPainterPath()
    head.moveTo(QPointF(size * 0.28, size * 0.46))
    head.lineTo(QPointF(size * 0.72, size * 0.46))
    head.lineTo(QPointF(size * 0.50, size * 0.72))
    head.closeSubpath()
    painter.drawPath(head)

    base_width = size * 0.46
    base_height = max(1.0, size * 0.075)
    painter.drawRoundedRect(
        QRectF((size - base_width) / 2, size * 0.78, base_width, base_height),
        base_height / 2,
        base_height / 2,
    )

    painter.end()
    return pixmap


def render_arrow(color: QColor, size: int = 24) -> QPixmap:
    """The downward arrow used in the combo boxes.

    Qt does not draw border triangles in subcontrols, so the style sheet points
    at these images instead.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(color))

    path = QPainterPath()
    path.moveTo(QPointF(size * 0.22, size * 0.40))
    path.lineTo(QPointF(size * 0.78, size * 0.40))
    path.lineTo(QPointF(size * 0.50, size * 0.66))
    path.closeSubpath()
    painter.drawPath(path)
    painter.end()
    return pixmap


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841 - Qt needs an instance

    resources_dir = REPO_ROOT / "ytdownloader" / "resources"
    assets_dir = REPO_ROOT / "packaging" / "assets"
    resources_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    largest = render(256)
    png_path = resources_dir / "icon.png"
    largest.save(str(png_path), "PNG")
    print(f"generated: {png_path}")

    # The .ico format holds several resolutions; Qt writes them from a list.
    ico_path = resources_dir / "icon.ico"
    images = [render(size) for size in ICON_SIZES]
    if not _save_ico(images, ico_path):
        return 1
    print(f"generated: {ico_path}")

    # The same icon ships with the installer, which uses it in Installed Apps.
    installer_icon = assets_dir / "icon.ico"
    installer_icon.write_bytes(ico_path.read_bytes())
    print(f"generated: {installer_icon}")

    # One arrow per theme, in the matching secondary text colour.
    for name, color in (("arrow-dark.png", "#949bab"), ("arrow-light.png", "#616874")):
        arrow_path = resources_dir / name
        render_arrow(QColor(color)).save(str(arrow_path), "PNG")
        print(f"generated: {arrow_path}")

    return 0


def _save_ico(images: list[QPixmap], destination: Path) -> bool:
    """Write a multi-resolution .ico using Qt's image writer."""
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice

    entries: list[tuple[int, bytes]] = []
    for pixmap in images:
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not pixmap.save(buffer, "PNG"):
            print(f"failed to encode size {pixmap.width()}", file=sys.stderr)
            return False
        buffer.close()
        entries.append((pixmap.width(), bytes(data)))

    # ICONDIR header: reserved, type 1 (icon), image count.
    header = bytearray()
    header += (0).to_bytes(2, "little")
    header += (1).to_bytes(2, "little")
    header += len(entries).to_bytes(2, "little")

    directory = bytearray()
    payload = bytearray()
    offset = 6 + 16 * len(entries)

    for size, png_bytes in entries:
        directory += bytes([0 if size >= 256 else size])  # width (0 means 256)
        directory += bytes([0 if size >= 256 else size])  # height
        directory += bytes([0])  # palette colours
        directory += bytes([0])  # reserved
        directory += (1).to_bytes(2, "little")  # colour planes
        directory += (32).to_bytes(2, "little")  # bits per pixel
        directory += len(png_bytes).to_bytes(4, "little")
        directory += offset.to_bytes(4, "little")
        payload += png_bytes
        offset += len(png_bytes)

    destination.write_bytes(bytes(header + directory + payload))
    return True


if __name__ == "__main__":
    raise SystemExit(main())
