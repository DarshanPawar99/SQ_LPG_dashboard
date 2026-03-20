"""
aggregations.py

Dashboard logic/summary layer.

KPI structure:
- Row 1: Total Vendors (all) | Total Clients (all)
- Row 2: Vendors with LPG (risk dots) | Clients with LPG (risk dots) |
         Vendors with Alternative (no risk dots) | Clients with Alternative (no risk dots)

"Alternative" = vendor where GAIL/PNG == Yes OR Electrical Equipment Availability == Yes
"LPG" = all other vendors (is_alternative == False)

Region cards, executive view, donut, and pivot all operate on LPG rows only.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from config import RISK_COLORS, RISK_LEVELS
from stock_logic import (
    as_date,
    get_live_days,
    get_risk_category,
    get_risk_color,
    get_risk_level,
    risk_sort_key,
    working_days_between,
)


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------
def _count_by_risk(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "out": sum(1 for row in rows if row.get("risk") == "Out of Stock"),
        "critical": sum(1 for row in rows if row.get("risk") == "Critical"),
        "moderate": sum(1 for row in rows if row.get("risk") == "Moderate"),
        "safe": sum(1 for row in rows if row.get("risk") == "Safe"),
    }


def _worst_risk_group(rows: list[dict[str, Any]], key_field: str) -> list[dict[str, Any]]:
    """Collapse rows to one record per key_field using worst vendor risk."""
    grouped: dict[str, dict[str, Any]] = {}

    for row in rows:
        key = str(row.get(key_field, "")).strip()
        if not key:
            continue

        risk = str(row.get("risk", "Safe"))
        level = RISK_LEVELS.get(risk, 0)
        current = grouped.get(key)

        if current is None or level > current["risk_level"]:
            grouped[key] = {
                key_field: key,
                "risk": risk,
                "risk_level": level,
            }

    return list(grouped.values())


def _unique_count(rows: list[dict[str, Any]], key_field: str) -> int:
    """Count unique non-empty values for a key field."""
    return len({str(row.get(key_field, "")).strip() for row in rows if str(row.get(key_field, "")).strip()})


# -------------------------------------------------------------------
# Enrich
# -------------------------------------------------------------------
def enrich_dashboard_rows(df: pd.DataFrame, selected_date: date) -> list[dict[str, Any]]:
    """Convert cleaned DataFrame rows into enriched dashboard rows.

    All rows are enriched (both LPG and alternative).
    The is_alternative flag is preserved for downstream filtering.
    """
    if df.empty:
        return []

    rows: list[dict[str, Any]] = []

    for idx, row in df.reset_index(drop=True).iterrows():
        last_updated = as_date(row.get("last_updated"))
        if last_updated is None:
            continue

        is_alt = bool(row.get("is_alternative", False))
        days_of_stock = int(float(row.get("days_of_stock", 0) or 0))
        live_days = get_live_days(days_of_stock, last_updated, selected_date)
        risk = get_risk_category(live_days)

        rows.append(
            {
                "id": int(idx) + 1,
                "vendor": str(row.get("vendor", "")).strip(),
                "client": str(row.get("client", "")).strip(),
                "region": str(row.get("region", "")).strip(),
                "pax": float(row.get("pax", 0) or 0),
                "days_of_stock": days_of_stock,
                "last_updated": last_updated.isoformat(),
                "continuity": str(row.get("continuity", "")).strip(),
                "gail_png": str(row.get("gail_png", "")).strip(),
                "is_alternative": is_alt,
                "working_days_consumed": working_days_between(last_updated, selected_date),
                "live_days": live_days,
                "risk": risk,
                "risk_level": get_risk_level(risk),
                "risk_color": get_risk_color(risk),
            }
        )

    return rows


# -------------------------------------------------------------------
# Split helpers
# -------------------------------------------------------------------
def _lpg_rows(enriched_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in enriched_rows if not r.get("is_alternative", False)]


def _alt_rows(enriched_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in enriched_rows if r.get("is_alternative", False)]


# -------------------------------------------------------------------
# KPI Row 1: Overall totals (no filtering, no risk dots)
# -------------------------------------------------------------------
def build_overall_vendor_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Total unique vendors across ALL rows (LPG + alternative). No risk dots."""
    return {
        "title": "Total Vendors",
        "value": _unique_count(enriched_rows, "vendor"),
        "subtitle": "All vendors including LPG & alternative",
    }


def build_overall_client_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Total unique clients across ALL rows (LPG + alternative). No risk dots."""
    return {
        "title": "Total Clients",
        "value": _unique_count(enriched_rows, "client"),
        "subtitle": "All clients including LPG & alternative",
    }


# -------------------------------------------------------------------
# KPI Row 2: LPG (with risk dots)
# -------------------------------------------------------------------
def build_vendor_risk_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Unique LPG vendor KPI summary with risk breakdown."""
    lpg = _lpg_rows(enriched_rows)
    vendors = _worst_risk_group(lpg, "vendor")
    counts = _count_by_risk(vendors)

    return {
        "title": "Vendors with LPG",
        "value": len(vendors),
        "subtitle": "Vendors without GAIL/PNG or Elec. Equipment",
        **counts,
    }


def build_client_worst_risk_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Unique LPG client KPI summary with worst vendor risk."""
    lpg = _lpg_rows(enriched_rows)
    clients = _worst_risk_group(lpg, "client")
    counts = _count_by_risk(clients)

    return {
        "title": "Clients with LPG",
        "value": len(clients),
        "subtitle": "Poor LPG vendor risk mapped per client",
        **counts,
    }


# -------------------------------------------------------------------
# KPI Row 2: Alternative (no risk dots)
# -------------------------------------------------------------------
def build_alternative_vendor_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Unique alternative vendor count. No risk dots."""
    alt = _alt_rows(enriched_rows)
    return {
        "title": "Vendors with Alternative",
        "value": _unique_count(alt, "vendor"),
        "subtitle": "GAIL/PNG or Elec. Equipment = Yes",
    }


def build_alternative_client_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Unique clients served by at least one alternative vendor. No risk dots."""
    alt = _alt_rows(enriched_rows)
    return {
        "title": "Clients with Alternative",
        "value": _unique_count(alt, "client"),
        "subtitle": "Clients with at least one alternative vendor",
    }


# -------------------------------------------------------------------
# Region cards (LPG only)
# -------------------------------------------------------------------
def build_region_cards(enriched_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lpg = _lpg_rows(enriched_rows)
    if not lpg:
        return []

    regions = sorted({str(row["region"]).strip() for row in lpg if row.get("region")})
    cards: list[dict[str, Any]] = []

    for region in regions:
        region_rows = [row for row in lpg if row.get("region") == region]
        vendors = _worst_risk_group(region_rows, "vendor")
        counts = _count_by_risk(vendors)

        cards.append(
            {
                "region": region,
                "total_vendors": len(vendors),
                **counts,
            }
        )

    return cards


# -------------------------------------------------------------------
# Executive view (LPG only)
# -------------------------------------------------------------------
def build_city_vendor_summary(enriched_rows: list[dict[str, Any]], selected_city: str) -> dict[str, Any]:
    lpg = _lpg_rows(enriched_rows)
    city_rows = [row for row in lpg if row.get("region") == selected_city]
    city_vendors = _worst_risk_group(city_rows, "vendor")
    counts = _count_by_risk(city_vendors)
    total_vendors = len(city_vendors)

    return {
        "city": selected_city,
        "total_vendors": total_vendors,
        "out": counts["out"],
        "critical": counts["critical"],
        "moderate": counts["moderate"],
        "safe": counts["safe"],
        "out_pct": round((counts["out"] / total_vendors) * 100) if total_vendors else 0,
        "critical_pct": round((counts["critical"] / total_vendors) * 100) if total_vendors else 0,
        "moderate_pct": round((counts["moderate"] / total_vendors) * 100) if total_vendors else 0,
        "safe_pct": round((counts["safe"] / total_vendors) * 100) if total_vendors else 0,
    }


def build_city_donut_data(enriched_rows: list[dict[str, Any]], selected_city: str) -> list[dict[str, Any]]:
    summary = build_city_vendor_summary(enriched_rows, selected_city)

    return [
        {"name": "Out of Stock", "value": summary["out"], "color": RISK_COLORS["Out of Stock"]},
        {"name": "Critical", "value": summary["critical"], "color": RISK_COLORS["Critical"]},
        {"name": "Moderate", "value": summary["moderate"], "color": RISK_COLORS["Moderate"]},
        {"name": "Safe", "value": summary["safe"], "color": RISK_COLORS["Safe"]},
    ]


# -------------------------------------------------------------------
# Pivot (LPG only)
# -------------------------------------------------------------------
def build_client_pivot_groups(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_risk: str,
    search_text: str = "",
) -> list[dict[str, Any]]:
    lpg = _lpg_rows(enriched_rows)
    city_rows = [row for row in lpg if row.get("region") == selected_city]

    filtered = [
        row
        for row in city_rows
        if (not selected_risk or row.get("risk") == selected_risk)
    ]

    if search_text:
        needle = search_text.strip().lower()
        filtered = [
            row
            for row in filtered
            if needle in str(row.get("client", "")).lower()
            or needle in str(row.get("vendor", "")).lower()
        ]

    filtered.sort(
        key=lambda row: (
            str(row.get("client", "")),
            risk_sort_key(str(row.get("risk", "Safe"))),
            str(row.get("vendor", "")),
        )
    )

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in filtered:
        client = str(row.get("client", "")).strip()
        grouped.setdefault(client, []).append(row)

    output: list[dict[str, Any]] = []
    for client, rows in grouped.items():
        output.append(
            {
                "client": client,
                "rows": rows,
                "total_pax": sum(float(r.get("pax", 0) or 0) for r in rows),
                "vendor_count": len(rows),
            }
        )

    return output
