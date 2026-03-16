"""
stock_logic.py

Core LPG stock logic for the dashboard.

This module isolates:
- weekday counting
- weekend exclusion
- live LPG day calculation
- risk category mapping
- worst-risk comparison helpers

All risk constants are imported from config.py (single source of truth).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

from config import RISK_COLORS, RISK_DISPLAY_ORDER, RISK_LEVELS


def as_date(value: Any) -> date | None:
    """Safely convert incoming values to a date object."""
    if value is None or pd.isna(value):
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def is_weekend(d: date) -> bool:
    """Return True if date is Saturday or Sunday."""
    return d.weekday() >= 5


def working_days_between(last_updated: date, selected_date: date) -> int:
    """
    Count weekdays between two dates.

    Rules:
    - last_updated is excluded
    - selected_date is excluded
    - Saturday and Sunday are excluded
    """
    if selected_date <= last_updated:
        return 0

    start = np.datetime64(last_updated + pd.Timedelta(days=1), "D")
    end = np.datetime64(selected_date, "D")
    return int(np.busday_count(start, end))


def get_live_days(days_of_stock: float | int, last_updated: date, selected_date: date) -> int:
    """
    Calculate live LPG stock days.

    Formula:
    live_days = max(0, days_of_stock - working_days_between(last_updated, selected_date))
    """
    consumed = working_days_between(last_updated, selected_date)
    return max(0, int(days_of_stock) - consumed)


def get_risk_category(live_days: int) -> str:
    """
    Map live LPG days to risk category.

    Rules:
    - 0 -> Out of Stock
    - 1 to 2 -> Critical
    - 3 to 4 -> Moderate
    - 5+ -> Safe
    """
    if live_days == 0:
        return "Out of Stock"
    if live_days <= 2:
        return "Critical"
    if live_days <= 4:
        return "Moderate"
    return "Safe"


def get_risk_color(risk: str) -> str:
    """Return dashboard color for a risk category."""
    return RISK_COLORS.get(risk, "#334155")


def get_risk_level(risk: str) -> int:
    """Return numeric severity level for comparing risks."""
    return RISK_LEVELS.get(risk, 0)


def risk_sort_key(risk: str) -> int:
    """Return display sort order for risk categories."""
    return RISK_DISPLAY_ORDER.index(risk) if risk in RISK_DISPLAY_ORDER else 999


def compare_risk(risk_a: str, risk_b: str) -> str:
    """Return the worse of two risk categories."""
    return risk_a if get_risk_level(risk_a) >= get_risk_level(risk_b) else risk_b


def build_enriched_row(
    raw_row: dict[str, Any],
    selected_date: date,
    row_id: int | None = None,
) -> dict[str, Any] | None:
    """
    Convert one cleaned raw row into a dashboard-ready enriched row.
    """
    last_updated = as_date(raw_row.get("last_updated"))
    if last_updated is None:
        return None

    days_of_stock = int(float(raw_row.get("days_of_stock", 0) or 0))
    live_days = get_live_days(days_of_stock, last_updated, selected_date)
    risk = get_risk_category(live_days)
    consumed = working_days_between(last_updated, selected_date)

    return {
        "id": row_id,
        "vendor": str(raw_row.get("vendor", "")).strip(),
        "client": str(raw_row.get("client", "")).strip(),
        "region": str(raw_row.get("region", "")).strip(),
        "pax": float(raw_row.get("pax", 0) or 0),
        "days_of_stock": days_of_stock,
        "last_updated": last_updated.isoformat(),
        "continuity": str(raw_row.get("continuity", "")).strip(),
        "gail_png": str(raw_row.get("gail_png", "")).strip(),
        "working_days_consumed": consumed,
        "live_days": live_days,
        "risk": risk,
        "risk_level": get_risk_level(risk),
        "risk_color": get_risk_color(risk),
    }
