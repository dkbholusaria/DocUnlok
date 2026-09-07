"""
themes.py — Centralised colour/font definitions for PdfPasswordRemover.

Adding a new theme:
  1. Add an entry to THEMES dict with a ThemeColors instance.
  No other file needs to change.
"""

import sys
from dataclasses import dataclass


# ── Font stacks (platform-aware) ──────────────────────────────────────────────

if sys.platform == "win32":
    UI_FONT   = "'Segoe UI', Arial, sans-serif"
    MONO_FONT = "'Cascadia Code', 'Consolas', monospace"
elif sys.platform == "darwin":
    UI_FONT   = "'Avenir Next', Arial"
    MONO_FONT = "'Menlo', monospace"
else:
    UI_FONT   = "Arial, sans-serif"
    MONO_FONT = "monospace"

UI_FONT_NAME   = "Segoe UI"   if sys.platform == "win32" else "Avenir Next"
MONO_FONT_NAME = "Cascadia Code" if sys.platform == "win32" else "Menlo"


# ── ThemeColors dataclass ─────────────────────────────────────────────────────

@dataclass
class ThemeColors:
    name: str

    bg_window:      str
    bg_panel:       str
    bg_input:       str
    bg_input_focus: str
    bg_log:         str
    bg_log_hdr:     str
    bg_table:       str
    bg_table_alt:   str
    bg_header:      str

    text_primary:  str
    text_muted:    str
    text_disabled: str
    text_log:      str

    border:       str
    border_focus: str
    grid:         str

    accent:       str
    accent_hover: str
    accent_light: str
    accent_text:  str

    row_selected_bg: str
    row_selected_fg: str

    scrollbar_handle:       str
    scrollbar_handle_hover: str


# ── Theme definitions ─────────────────────────────────────────────────────────

THEMES: dict[str, ThemeColors] = {

    "light": ThemeColors(
        name            = "Light",

        bg_window       = "#FFFFFF",
        bg_panel        = "#FFFFFF",
        bg_input        = "#FFFFFF",
        bg_input_focus  = "#FAFBFF",
        bg_log          = "#0F172A",
        bg_log_hdr      = "#1E293B",
        bg_table        = "#FFFFFF",
        bg_table_alt    = "#F8FAFC",
        bg_header       = "#FFFFFF",

        text_primary    = "#0F172A",
        text_muted      = "#94A3B8",
        text_disabled   = "#94A3B8",
        text_log        = "#7DD3FC",

        border          = "#E2E8F0",
        border_focus    = "#3B82F6",
        grid            = "#E2E8F0",

        accent          = "#2563EB",
        accent_hover    = "#1D4ED8",
        accent_light    = "#DBEAFE",
        accent_text     = "#FFFFFF",

        row_selected_bg = "#DBEAFE",
        row_selected_fg = "#0F172A",

        scrollbar_handle       = "#CBD5E1",
        scrollbar_handle_hover = "#94A3B8",
    ),

    "dark": ThemeColors(
        name            = "Dark Navy",

        bg_window       = "#0A1628",
        bg_panel        = "#0D1F3C",
        bg_input        = "#0F2040",
        bg_input_focus  = "#0D1F3C",
        bg_log          = "#060F1E",
        bg_log_hdr      = "#0F2040",
        bg_table        = "#0A1628",
        bg_table_alt    = "#0D1F3C",
        bg_header       = "#0D1F3C",

        text_primary    = "#E2E8F0",
        text_muted      = "#94A3B8",
        text_disabled   = "#475569",
        text_log        = "#7DD3FC",

        border          = "#1E3A5F",
        border_focus    = "#3B82F6",
        grid            = "#1E3A5F",

        accent          = "#2563EB",
        accent_hover    = "#1D4ED8",
        accent_light    = "#1E3A5F",
        accent_text     = "#FFFFFF",

        row_selected_bg = "#0D1F3C",
        row_selected_fg = "#60A5FA",

        scrollbar_handle       = "#1E3A5F",
        scrollbar_handle_hover = "#2563EB",
    ),
}


# ── Stylesheet builder ────────────────────────────────────────────────────────

def build_stylesheet(t: ThemeColors) -> str:
    return f"""
QMainWindow, QDialog {{ background: {t.bg_window}; }}
QMessageBox {{ background: {t.bg_window}; }}
QMessageBox QLabel {{ color: {t.text_primary}; background: transparent; }}
QMessageBox QPushButton {{
    background: {t.accent}; color: {t.accent_text}; border: none;
    border-radius: 5px; padding: 6px 18px; font-size: 13px; min-width: 70px;
}}
QMessageBox QPushButton:hover {{ background: {t.accent_hover}; }}
QWidget {{ font-family: {UI_FONT}; font-size: 13px; color: {t.text_primary}; }}
QLabel  {{ color: {t.text_primary}; font-size: 13px; }}

QPushButton {{
    background: {t.accent};
    color: {t.accent_text};
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
    min-height: 28px;
}}
QPushButton:hover    {{ background: {t.accent_hover}; }}
QPushButton:disabled {{ background: {t.border}; color: {t.text_disabled}; }}

QLineEdit {{
    background: {t.bg_input};
    border: 1.5px solid {t.border};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 13px;
    color: {t.text_primary};
    min-height: 28px;
    selection-background-color: {t.accent_light};
}}
QLineEdit:hover  {{ border-color: {t.accent}; }}
QLineEdit:focus  {{ border: 1.5px solid {t.border_focus}; background: {t.bg_input_focus}; outline: none; }}
QLineEdit:disabled {{ background: {t.bg_window}; color: {t.text_disabled}; border-color: {t.border}; }}
QLineEdit::placeholder {{ color: {t.text_muted}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 6px; border-radius: 3px; margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {t.scrollbar_handle}; border-radius: 3px; min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {t.scrollbar_handle_hover}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QTextEdit {{
    background: {t.bg_log};
    border: 1px solid {t.border};
    border-radius: 6px;
    font-family: {MONO_FONT};
    font-size: 11px;
    color: {t.text_log};
    padding: 8px 12px;
}}

QTableWidget {{
    background: {t.bg_table};
    alternate-background-color: {t.bg_table_alt};
    border: 1px solid {t.border};
    border-radius: 6px;
    gridline-color: {t.grid};
    color: {t.text_primary};
    font-size: 12px;
    selection-background-color: {t.row_selected_bg};
    selection-color: {t.row_selected_fg};
}}
QTableWidget::item {{ padding: 4px 8px; }}
QHeaderView::section {{
    background: {t.bg_header};
    color: {t.text_muted};
    padding: 6px 8px;
    border: none;
    border-bottom: 1.5px solid {t.border};
    font-weight: 600;
    font-size: 12px;
}}
QTableCornerButton::section {{ background: {t.bg_header}; border: none; }}

QToolTip {{
    background-color: {t.bg_panel}; color: {t.text_primary};
    border: 1px solid {t.border}; border-radius: 4px;
    padding: 5px 9px; font-size: 11px;
    opacity: 255;
}}
"""


def get_theme(name: str) -> ThemeColors:
    """Return theme by name, falling back to dark if unknown."""
    return THEMES.get(name, THEMES["dark"])
