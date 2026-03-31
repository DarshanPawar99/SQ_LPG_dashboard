"""
config.py

Central configuration for the LPG Stock Tracker Dashboard.
Single source of truth for all constants.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path


# -------------------------------------------------------------------
# APP
# -------------------------------------------------------------------
APP_TITLE = "LPG Stock Tracker Dashboard"
APP_SUBTITLE = "Live stock risk, client exposure, and vendor continuity preview"
APP_DEBUG = True


# -------------------------------------------------------------------
# DATA SOURCE
# -------------------------------------------------------------------
DATA_FILE_PATH = Path("data/lpg_stock_data.xlsx")
VENDOR_SHEET_NAME = "Master Vendor Data"
CLIENT_SHEET_NAME = "Master Client Data"


# -------------------------------------------------------------------
# DEFAULT UI STATE
# -------------------------------------------------------------------
DEFAULT_SELECTED_DATE = date.today()
MIN_SELECTABLE_DATE = date(2025, 1, 1)
MAX_SELECTABLE_DATE = date(2027, 12, 31)
DEFAULT_SELECTED_RISK = ""
DEFAULT_SEARCH_TEXT = ""


# -------------------------------------------------------------------
# DASHBOARD LABELS
# -------------------------------------------------------------------
SECTION_TAB_LABEL = "01 Executive View"
EMPTY_PIVOT_MESSAGE = "Select a risk category above to expand the client–vendor breakdown"
EXECUTIVE_VIEW_TITLE = "Executive View"


# -------------------------------------------------------------------
# RISK LOGIC (single source of truth)
# -------------------------------------------------------------------
RISK_COLORS = {
    "Out of Stock": "#ef4444",
    "Critical": "#f97316",
    "Moderate": "#eab308",
    "Safe": "#22c55e",
}

RISK_LEVELS = {
    "Safe": 1,
    "Moderate": 2,
    "Critical": 3,
    "Out of Stock": 4,
}

RISK_DISPLAY_ORDER = [
    "Out of Stock",
    "Critical",
    "Moderate",
    "Safe",
]

RISK_SUBTITLES = {
    "Out of Stock": "0–3 Live Days",
    "Critical": "4–5 Live Days",
    "Moderate": "6–7 Live Days",
    "Safe": "8+ Live Days",
}


# -------------------------------------------------------------------
# ALTERNATIVE COVERAGE TYPES
# -------------------------------------------------------------------
ALT_TYPE_COLORS = {
    "GAIL/PNG at Vendor": "#fb923c",                 # light orange
    "Electrical Equipment Availability": "#93c572",  # pistachio green
    "Both": "#06b6d4",                               # cyan
}

ALT_TYPE_SHORT_NAMES = {
    "GAIL/PNG at Vendor": "GAIL / PNG",
    "Electrical Equipment Availability": "Elec. Equipment",
    "Both": "Both",
}

ALT_TYPE_SUBTITLES = {
    "GAIL/PNG at Vendor": "Gas Pipeline Available",
    "Electrical Equipment Availability": "Elec. Backup Available",
    "Both": "Full Backup Coverage",
}

ALT_TYPE_DISPLAY_ORDER = [
    "GAIL/PNG at Vendor",
    "Electrical Equipment Availability",
    "Both",
]


# -------------------------------------------------------------------
# BUSINESS RULES
# -------------------------------------------------------------------
EXCLUDED_GAIL_PNG_VALUES = {"yes"}


# -------------------------------------------------------------------
# DASHBOARD COLUMN NAMES (canonical)
# -------------------------------------------------------------------
CANONICAL_VENDOR_ID = "vendor_id"
CANONICAL_VENDOR = "vendor"
CANONICAL_CLIENT = "client"
CANONICAL_REGION = "region"
CANONICAL_PAX = "pax"
CANONICAL_DAYS_OF_STOCK = "days_of_stock"
CANONICAL_LAST_UPDATED = "last_updated"
CANONICAL_GAIL_PNG = "gail_png"
CANONICAL_CONTINUITY = "continuity"
CANONICAL_IS_ALTERNATIVE = "is_alternative"


# -------------------------------------------------------------------
# OPTIONAL FUTURE SETTINGS
# -------------------------------------------------------------------
USE_SAMPLE_FALLBACK_DATA = False
