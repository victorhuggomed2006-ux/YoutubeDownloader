"""Gera o ícone do aplicativo em .ico e .png.

O desenho é feito com o próprio Qt, então não há dependência de editores
externos nem de bibliotecas de imagem adicionais. Executar:

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

# Tamanhos que o Windows usa em diferentes contextos (barra de tarefas, lista
# de programas, área de trabalho, telas de alta densidade).
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)

GRADIENT_START = QColor("#ff8551")
GRADIENT_END = QColor("#e8551f")
ARROW_COLOR = QColor("#ffffff")


def render(size: int) -> QPixmap:
    """Desenha o ícone: quadrado arredondado laranja com uma seta de download."""
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

    # Seta apontando para baixo, com a base sólida embaixo.
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
    """Seta para baixo usada nos seletores.

    O Qt não desenha triângulos via borda em subcontroles, então a folha de
    estilo aponta para estas imagens.
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
    app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841 - o Qt exige uma instância

    resources_dir = REPO_ROOT / "ytdownloader" / "resources"
    assets_dir = REPO_ROOT / "packaging" / "assets"
    resources_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    largest = render(256)
    png_path = resources_dir / "icon.png"
    largest.save(str(png_path), "PNG")
    print(f"gerado: {png_path}")

    # O formato .ico guarda várias resoluções; o Qt grava a partir de uma lista.
    ico_path = resources_dir / "icon.ico"
    images = [render(size) for size in ICON_SIZES]
    if not _save_ico(images, ico_path):
        return 1
    print(f"gerado: {ico_path}")

    # O mesmo ícone acompanha o instalador, que o usa em Aplicativos Instalados.
    installer_icon = assets_dir / "icon.ico"
    installer_icon.write_bytes(ico_path.read_bytes())
    print(f"gerado: {installer_icon}")

    # Uma seta para cada tema, na cor do texto secundário correspondente.
    for name, color in (("arrow-dark.png", "#949bab"), ("arrow-light.png", "#616874")):
        arrow_path = resources_dir / name
        render_arrow(QColor(color)).save(str(arrow_path), "PNG")
        print(f"gerado: {arrow_path}")

    return 0


def _save_ico(images: list[QPixmap], destination: Path) -> bool:
    """Grava um .ico com várias resoluções usando o escritor de imagens do Qt."""
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice

    entries: list[tuple[int, bytes]] = []
    for pixmap in images:
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not pixmap.save(buffer, "PNG"):
            print(f"falha ao codificar o tamanho {pixmap.width()}", file=sys.stderr)
            return False
        buffer.close()
        entries.append((pixmap.width(), bytes(data)))

    # Cabeçalho ICONDIR: reservado, tipo 1 (ícone), quantidade de imagens.
    header = bytearray()
    header += (0).to_bytes(2, "little")
    header += (1).to_bytes(2, "little")
    header += len(entries).to_bytes(2, "little")

    directory = bytearray()
    payload = bytearray()
    offset = 6 + 16 * len(entries)

    for size, png_bytes in entries:
        directory += bytes([0 if size >= 256 else size])  # largura (0 significa 256)
        directory += bytes([0 if size >= 256 else size])  # altura
        directory += bytes([0])  # cores da paleta
        directory += bytes([0])  # reservado
        directory += (1).to_bytes(2, "little")  # planos de cor
        directory += (32).to_bytes(2, "little")  # bits por pixel
        directory += len(png_bytes).to_bytes(4, "little")
        directory += offset.to_bytes(4, "little")
        payload += png_bytes
        offset += len(png_bytes)

    destination.write_bytes(bytes(header + directory + payload))
    return True


if __name__ == "__main__":
    raise SystemExit(main())
