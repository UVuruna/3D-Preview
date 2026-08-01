"""Theme — DESIGN.md tokens and the stylesheet built from them.

Single source for every colour, radius and spacing value in the demo app
(root Rule #4); no component hardcodes a literal.
"""

from pathlib import Path

# ═══════════════════════════ FONT ═══════════════════════════

FONT_FILE = Path(__file__).parent.parent / "assets" / "fonts" / "Inter.ttf"

# ═══════════════════════════ THEME TOKENS ═══════════════════════════

# DESIGN.md dark surfaces with one indigo accent.
THEME = {
    "surface_0": "#121218",
    "surface_1": "#1E1E26",
    "surface_2": "#24242E",
    "surface_hover": "#2C2C38",
    "border": "rgba(255, 255, 255, 0.10)",
    "text_primary": "#F5F5F5",
    "text_secondary": "#A8A8B3",
    "text_muted": "#6E6E7E",
    "accent": "#818CF8",
    "accent_strong": "#6366F1",
    "radius_control": "8px",
    "radius_small": "6px",
    "radius_card": "14px",
    "space_s": 8,
    "space_m": 16,
    "space_l": 24,
}


# ═══════════════════════════ STYLESHEET ═══════════════════════════


def build_qss(theme: dict) -> str:
    return f"""
    QWidget {{
        background: {theme["surface_0"]};
        color: {theme["text_primary"]};
        font-family: Inter;
        font-size: 14px;
    }}
    /* A QLabel inherits the QWidget rule above and would paint the window
       surface over whatever card it sits on — every label is transparent
       unless it explicitly styles itself (the legend key pill below). */
    QLabel {{ background: transparent; }}
    QLabel#Title {{ font-size: 22px; font-weight: 700; }}
    QLabel#Subtitle {{ color: {theme["text_secondary"]}; font-size: 13px; }}
    QLabel#SectionLabel {{
        color: {theme["text_secondary"]};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        padding-top: {theme["space_s"]}px;
    }}
    QLabel#Readout {{
        color: {theme["text_primary"]};
        font-size: 13px;
        line-height: 20px;
    }}
    QLabel#ReadoutMuted {{ color: {theme["text_muted"]}; font-size: 12px; }}
    QLabel#LegendKey {{
        background: {theme["surface_2"]};
        border: 1px solid {theme["border"]};
        border-radius: {theme["radius_small"]};
        color: {theme["text_primary"]};
        font-size: 12px;
        font-weight: 500;
        padding: 3px 8px;
    }}
    QLabel#LegendValue {{ color: {theme["text_secondary"]}; font-size: 13px; }}
    QLabel#PartName {{ font-size: 13px; }}
    QLabel#PartNameGroup {{ font-size: 13px; font-weight: 600; color: {theme["accent"]}; }}

    QFrame#Card {{
        background: {theme["surface_1"]};
        border: 1px solid {theme["border"]};
        border-radius: {theme["radius_card"]};
    }}
    QFrame#Divider {{ background: {theme["border"]}; border: none; max-height: 1px; }}

    QPushButton {{
        background: {theme["surface_2"]};
        border: 1px solid {theme["border"]};
        border-radius: {theme["radius_control"]};
        font-size: 14px;
        font-weight: 500;
        padding: 10px 14px;
    }}
    QPushButton:hover {{ background: {theme["surface_hover"]}; }}
    QPushButton:checked {{ background: {theme["accent_strong"]}; border-color: transparent; }}
    QPushButton:checked:hover {{ background: {theme["accent"]}; }}
    QPushButton#Compact {{
        font-size: 12px;
        font-weight: 500;
        padding: 6px 8px;
        border-radius: {theme["radius_small"]};
    }}

    QCheckBox {{ background: transparent; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {theme["border"]};
        border-radius: 4px;
        background: {theme["surface_2"]};
    }}
    QCheckBox::indicator:checked {{
        background: {theme["accent_strong"]};
        border-color: {theme["accent"]};
    }}
    QCheckBox::indicator:hover {{ border-color: {theme["accent"]}; }}

    QSlider {{ background: transparent; }}
    QSlider::groove:horizontal {{
        height: 4px;
        border-radius: 2px;
        background: {theme["surface_hover"]};
    }}
    QSlider::sub-page:horizontal {{ background: {theme["accent_strong"]}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        width: 12px;
        margin: -5px 0;
        border-radius: 6px;
        background: {theme["text_primary"]};
    }}
    QSlider::handle:horizontal:hover {{ background: {theme["accent"]}; }}

    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
    QScrollBar::handle:vertical {{
        background: {theme["surface_hover"]};
        border-radius: 5px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {theme["accent_strong"]}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    """
