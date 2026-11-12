"""
Visual theme for Cardiac Rhythm Analysis System, matched to the provided
design mockups: deep navy background, slightly lighter navy cards, a
coral-red accent, and light cream/white text.
"""

import os

BACKGROUND = "#0B0F19"
SURFACE = "#141A2A"
SURFACE_2 = "#1B2236"
ACCENT = "#EF4444"
ACCENT_2 = "#7F1D1D"
TEXT = "#F1F3F8"
MUTED = "#8B93A7"
BORDER = "#2A3245"
GOOD = "#22C55E"
WARN = "#EAB308"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "assets", "icons")


def icon(name):
    return os.path.join(ICONS_DIR, f"{name}.png")


STYLESHEET = f"""
QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}}

#Sidebar {{
    background-color: {SURFACE};
    border-right: 1px solid {BORDER};
}}

#SidebarTitle {{
    font-size: 17px;
    font-weight: 700;
    padding: 22px 20px 2px 20px;
    color: {TEXT};
}}

#SidebarSubtitle {{
    font-size: 10px;
    letter-spacing: 2px;
    color: {MUTED};
    padding: 0px 20px 18px 20px;
}}

QPushButton#NavButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    text-align: left;
    padding: 11px 18px;
    margin: 2px 10px;
    color: {TEXT};
    font-size: 13px;
}}
QPushButton#NavButton:hover {{
    background-color: {ACCENT_2};
}}
QPushButton#NavButton[active="true"] {{
    background-color: {ACCENT};
    color: white;
    font-weight: 600;
}}

#Card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}

#PageTitle {{
    font-size: 21px;
    font-weight: 700;
    color: {TEXT};
}}
#PageSubtitle {{
    font-size: 12px;
    color: {MUTED};
}}
#StatValue {{
    font-size: 30px;
    font-weight: 700;
    color: {ACCENT};
}}
#StatLabel {{
    font-size: 11px;
    letter-spacing: 1px;
    color: {MUTED};
}}

QLineEdit, QComboBox, QDateTimeEdit, QDateEdit, QTextEdit {{
    background-color: {BACKGROUND};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 8px 10px;
    color: {TEXT};
    selection-background-color: {ACCENT};
}}
QLineEdit:hover, QComboBox:hover {{ border: 1px solid #454f68; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}

QPushButton#PrimaryButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{ background-color: #f56565; }}
QPushButton#PrimaryButton:pressed {{ background-color: #b91c1c; }}
QPushButton#PrimaryButton:disabled {{ background-color: {SURFACE_2}; color: {MUTED}; }}

QPushButton {{
    background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 14px;
}}
QPushButton:hover {{ background-color: #232c44; border: 1px solid #454f68; }}
QPushButton:pressed {{ background-color: #0e1220; }}

QPushButton#DangerButton {{
    background-color: {SURFACE_2};
    color: #f0a3a3;
    border: 1px solid {ACCENT_2};
}}
QPushButton#DangerButton:hover {{ background-color: {ACCENT_2}; color: white; border: 1px solid {ACCENT}; }}

QTableWidget {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER};
    alternate-background-color: #171e30;
}}
QTableWidget::item {{ padding: 3px; }}
QTableWidget::item:selected {{ background-color: {ACCENT_2}; color: {TEXT}; }}

QHeaderView::section {{
    background-color: {BACKGROUND};
    color: {MUTED};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-size: 11px;
    letter-spacing: 1px;
}}

QScrollBar:vertical {{ background: {BACKGROUND}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; }}
QScrollBar::handle:vertical:hover {{ background: #454f68; }}

QComboBox::drop-down {{ border: none; width: 22px; }}

QToolTip {{
    background-color: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; padding: 4px 8px;
}}

#AlertBanner {{
    background-color: {ACCENT_2};
    border: 1px solid {ACCENT};
    border-radius: 4px;
    padding: 12px 16px;
}}
#GoodBanner {{
    background-color: #14351f;
    border: 1px solid {GOOD};
    border-radius: 4px;
    padding: 12px 16px;
}}

QRadioButton, QCheckBox {{ spacing: 8px; }}
"""
