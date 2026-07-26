"""Temas claro e escuro aplicados via folha de estilo do Qt."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Cores de um tema."""

    window: str
    surface: str
    surface_alt: str
    surface_hover: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_text: str
    success: str
    warning: str
    danger: str
    track: str


DARK = Palette(
    window="#0f1115",
    surface="#171a21",
    surface_alt="#1e222b",
    surface_hover="#252a35",
    border="#2a2f3a",
    border_strong="#3a4150",
    text="#e8eaed",
    text_muted="#949bab",
    accent="#ff6b35",
    accent_hover="#ff8551",
    accent_pressed="#e85520",
    accent_text="#ffffff",
    success="#3ecf8e",
    warning="#f5a524",
    danger="#f0526d",
    track="#252a35",
)

LIGHT = Palette(
    window="#f4f5f8",
    surface="#ffffff",
    surface_alt="#eef0f4",
    surface_hover="#e4e7ee",
    border="#d9dce4",
    border_strong="#c2c7d2",
    text="#1a1d23",
    text_muted="#616874",
    accent="#e8551f",
    accent_hover="#ff6b35",
    accent_pressed="#c94514",
    accent_text="#ffffff",
    success="#1f9d63",
    warning="#c77a06",
    danger="#d13a52",
    track="#e0e3ea",
)

THEMES = {"dark": DARK, "light": LIGHT}


def palette_for(name: str) -> Palette:
    return THEMES.get(name, DARK)


def _arrow_url(theme: str) -> str:
    """Caminho da seta dos seletores, no formato aceito pela folha de estilo."""
    from ..core import paths  # importado aqui para o tema não depender do núcleo

    filename = "arrow-light.png" if theme == "light" else "arrow-dark.png"
    path = paths.resource_path(filename)
    if not path.is_file():
        return ""
    return path.as_posix()


def build_stylesheet(name: str) -> str:
    """Gera a folha de estilo completa para o tema pedido."""
    c = palette_for(name)
    arrow = _arrow_url(name)
    arrow_rule = f"image: url({arrow});" if arrow else "image: none;"
    return f"""
QWidget {{
    background-color: {c.window};
    color: {c.text};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
}}

QMainWindow, QDialog {{
    background-color: {c.window};
}}

/* Rótulos e caixas herdam o fundo do cartão em que estão, e não o da janela. */
QLabel, QCheckBox, QGroupBox, QRadioButton {{
    background: transparent;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

QToolTip {{
    background-color: {c.surface_alt};
    color: {c.text};
    border: 1px solid {c.border};
    padding: 6px 8px;
    border-radius: 6px;
}}

/* ── Cartões ─────────────────────────────────────────────── */
QFrame#Card {{
    background-color: {c.surface};
    border: 1px solid {c.border};
    border-radius: 14px;
}}

QFrame#PreviewCard {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border};
    border-radius: 12px;
}}

QFrame#QueueItem {{
    background-color: {c.surface};
    border: 1px solid {c.border};
    border-radius: 12px;
}}

QFrame#Separator {{
    background-color: {c.border};
    border: none;
    max-height: 1px;
}}

/* ── Tipografia ──────────────────────────────────────────── */
QLabel#AppTitle {{
    font-size: 19px;
    font-weight: 700;
    color: {c.text};
}}

QLabel#AppSubtitle, QLabel#Muted, QLabel#FieldHint {{
    color: {c.text_muted};
    font-size: 12px;
}}

QLabel#SectionLabel {{
    color: {c.text_muted};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#PreviewTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {c.text};
}}

QLabel#PreviewMeta {{
    color: {c.text_muted};
    font-size: 12px;
}}

QLabel#QueueTitle {{
    font-size: 14px;
    font-weight: 600;
}}

QLabel#QueueMeta {{
    color: {c.text_muted};
    font-size: 12px;
}}

QLabel#StatusError {{
    color: {c.danger};
    font-size: 12px;
}}

QLabel#StatusOk {{
    color: {c.success};
    font-size: 12px;
}}

QLabel#EmptyState {{
    color: {c.text_muted};
    font-size: 13px;
}}

QLabel#Thumb {{
    background-color: {c.surface_hover};
    border-radius: 8px;
}}

/* ── Campo de texto ──────────────────────────────────────── */
QLineEdit {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border};
    border-radius: 10px;
    padding: 11px 14px;
    color: {c.text};
    selection-background-color: {c.accent};
    selection-color: {c.accent_text};
}}

QLineEdit:hover {{
    border-color: {c.border_strong};
}}

QLineEdit:focus {{
    border-color: {c.accent};
    background-color: {c.surface};
}}

QLineEdit[state="valid"] {{
    border-color: {c.success};
}}

QLineEdit[state="invalid"] {{
    border-color: {c.danger};
}}

/* ── Botões ──────────────────────────────────────────────── */
QPushButton {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border};
    border-radius: 10px;
    padding: 9px 16px;
    color: {c.text};
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {c.surface_hover};
    border-color: {c.border_strong};
}}

QPushButton:pressed {{
    background-color: {c.border};
}}

QPushButton:disabled {{
    color: {c.text_muted};
    background-color: {c.surface};
    border-color: {c.border};
}}

QPushButton#PrimaryButton {{
    background-color: {c.accent};
    border: none;
    color: {c.accent_text};
    padding: 13px 24px;
    font-size: 15px;
    font-weight: 700;
    border-radius: 11px;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {c.accent_hover};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {c.accent_pressed};
}}

QPushButton#PrimaryButton:disabled {{
    background-color: {c.surface_hover};
    color: {c.text_muted};
}}

QPushButton#GhostButton {{
    background-color: transparent;
    border: 1px solid {c.border};
    padding: 7px 12px;
    font-weight: 500;
}}

QPushButton#GhostButton:hover {{
    background-color: {c.surface_hover};
}}

QPushButton#LinkButton {{
    background-color: transparent;
    border: none;
    color: {c.accent};
    padding: 4px 6px;
    font-weight: 600;
    text-align: left;
}}

QPushButton#LinkButton:hover {{
    color: {c.accent_hover};
}}

QPushButton#DangerButton {{
    background-color: transparent;
    border: 1px solid {c.border};
    color: {c.danger};
    padding: 6px 12px;
}}

QPushButton#DangerButton:hover {{
    background-color: {c.surface_hover};
    border-color: {c.danger};
}}

/* ── Seletores ───────────────────────────────────────────── */
QComboBox {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border};
    border-radius: 10px;
    padding: 9px 12px;
    color: {c.text};
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {c.border_strong};
}}

QComboBox:focus {{
    border-color: {c.accent};
}}

QComboBox::drop-down {{
    border: none;
    width: 26px;
}}

QComboBox::down-arrow {{
    {arrow_rule}
    width: 16px;
    height: 16px;
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border_strong};
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: {c.accent};
    selection-color: {c.accent_text};
}}

/* ── Alternador de formato ───────────────────────────────── */
QPushButton#SegmentLeft, QPushButton#SegmentRight {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border};
    padding: 11px 18px;
    font-weight: 600;
    color: {c.text_muted};
}}

QPushButton#SegmentLeft {{
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
}}

QPushButton#SegmentRight {{
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    border-left: none;
}}

QPushButton#SegmentLeft:checked, QPushButton#SegmentRight:checked {{
    background-color: {c.accent};
    border-color: {c.accent};
    color: {c.accent_text};
}}

QPushButton#SegmentLeft:hover:!checked, QPushButton#SegmentRight:hover:!checked {{
    background-color: {c.surface_hover};
    color: {c.text};
}}

/* ── Barra de progresso ──────────────────────────────────── */
QProgressBar {{
    background-color: {c.track};
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {c.accent};
    border-radius: 5px;
}}

QProgressBar[state="done"]::chunk {{
    background-color: {c.success};
}}

QProgressBar[state="error"]::chunk {{
    background-color: {c.danger};
}}

/* ── Abas ────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background: transparent;
}}

QTabBar::tab {{
    background: transparent;
    color: {c.text_muted};
    padding: 9px 16px;
    margin-right: 4px;
    border-radius: 9px;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: {c.surface_alt};
    color: {c.text};
}}

QTabBar::tab:selected {{
    background-color: {c.surface};
    color: {c.accent};
    border: 1px solid {c.border};
}}

/* ── Rolagem ─────────────────────────────────────────────── */
QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {c.border_strong};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c.text_muted};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
}}

QScrollBar::handle:horizontal {{
    background-color: {c.border_strong};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
    width: 0;
}}

/* ── Caixas de marcação ──────────────────────────────────── */
QCheckBox {{
    spacing: 9px;
    color: {c.text};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {c.border_strong};
    border-radius: 5px;
    background-color: {c.surface_alt};
}}

QCheckBox::indicator:hover {{
    border-color: {c.accent};
}}

QCheckBox::indicator:checked {{
    background-color: {c.accent};
    border-color: {c.accent};
    image: none;
}}

/* ── Diversos ────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {c.border};
    border-radius: 12px;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: {c.text_muted};
}}

QSpinBox {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border};
    border-radius: 8px;
    padding: 7px 10px;
    color: {c.text};
}}

QSpinBox:focus {{
    border-color: {c.accent};
}}

QMenu {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border_strong};
    border-radius: 8px;
    padding: 5px;
}}

QMenu::item {{
    padding: 7px 22px 7px 14px;
    border-radius: 6px;
}}

QMenu::item:selected {{
    background-color: {c.accent};
    color: {c.accent_text};
}}

QTextBrowser {{
    background-color: {c.surface_alt};
    border: 1px solid {c.border};
    border-radius: 10px;
    padding: 10px;
}}

/* ── Tabela do histórico ─────────────────────────────────── */
QTableWidget {{
    background-color: {c.surface};
    border: 1px solid {c.border};
    border-radius: 12px;
    gridline-color: transparent;
    outline: none;
    padding: 4px;
}}

QTableWidget::item {{
    padding: 9px 10px;
    border: none;
    color: {c.text};
}}

QTableWidget::item:selected {{
    background-color: {c.accent};
    color: {c.accent_text};
    border-radius: 6px;
}}

QHeaderView::section {{
    background-color: transparent;
    color: {c.text_muted};
    border: none;
    border-bottom: 1px solid {c.border};
    padding: 9px 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

QTableCornerButton::section {{
    background: transparent;
    border: none;
}}

/* ── Barra de status ─────────────────────────────────────── */
QStatusBar {{
    background: transparent;
    color: {c.text_muted};
    border-top: 1px solid {c.border};
}}

QStatusBar::item {{
    border: none;
}}

QMessageBox {{
    background-color: {c.surface};
}}

QMessageBox QLabel {{
    color: {c.text};
}}
"""
