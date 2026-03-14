"""
config.py

Central configuration for the LPG Stock Tacker Dashboard.

Use this file for values that may change between environments:
- app title
- dataset path
- sheet names
- default selected date
- dashboard labels
- risk constants and colors
"""

from __future__ import annotations

from datetime import date
from pathlib import Path


# -------------------------------------------------------------------
# APP
# -------------------------------------------------------------------
APP_TITLE = "LPG Stock Tacker Dashboard"
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
DEFAULT_SELECTED_DATE = date(2026, 3, 17)
DEFAULT_SELECTED_RISK = ""
DEFAULT_SEARCH_TEXT = ""


# -------------------------------------------------------------------
# DASHBOARD LABELS
# -------------------------------------------------------------------
SECTION_TAB_LABEL = "01 Executive View"
EMPTY_PIVOT_MESSAGE = "Select risk category"
EXECUTIVE_VIEW_TITLE = "Executive View"


# -------------------------------------------------------------------
# RISK LOGIC
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


# -------------------------------------------------------------------
# BUSINESS RULES
# -------------------------------------------------------------------
EXCLUDE_GAIL_PNG_YES = True
EXCLUDED_GAIL_PNG_VALUES = {"yes"}
EXCLUDE_WEEKENDS_FROM_STOCK_DECAY = True


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


# -------------------------------------------------------------------
# OPTIONAL FUTURE SETTINGS
# -------------------------------------------------------------------
# Set to False later if you want production mode styling / deployment behavior.
USE_SAMPLE_FALLBACK_DATA = False
