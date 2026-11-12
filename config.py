"""
Central configuration for Cardiac Rhythm Analysis System.

MySQL connection details live here. If you're running this against your
own MySQL server (e.g. XAMPP's MySQL, MySQL Workbench, a cloud DB), just
edit the values below - nothing else in the app needs to change.
"""

import os

DB_CONFIG = {
    "host": os.environ.get("CRA_DB_HOST", "localhost"),
    "port": int(os.environ.get("CRA_DB_PORT", "3306")),
    "user": os.environ.get("CRA_DB_USER", "root"),
    "password": os.environ.get("CRA_DB_PASSWORD", ""),
    "database": os.environ.get("CRA_DB_NAME", "cardiac_rhythm_analysis"),
}

APP_NAME = "Cardiac Rhythm Analysis System"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
REPORT_CHARTS_DIR = os.path.join(BASE_DIR, "report_charts")

# Clinical thresholds used by the Medical Rule Engine (utils/ecg_processing.py)
NORMAL_RANGES = {
    "heart_rate": (60, 100),        # bpm
    "pr_interval": (0.12, 0.20),    # seconds
    "qrs_duration": (0.06, 0.10),   # seconds
    "qt_interval": (0.30, 0.44),    # seconds (rough adult resting range)
    "qtc_interval": (0.36, 0.44),   # seconds (Bazett-corrected)
}
