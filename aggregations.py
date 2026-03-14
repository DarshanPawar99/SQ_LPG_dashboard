"""
aggregations.py

This module is the dashboard's logic/summary layer.

It is responsible for:
- enriching raw cleaned data with live LPG days and risk category
- building KPI summaries
- building region cards
- building selected-city executive view summaries
- building donut input data
- building grouped client-vendor pivot rows

Design goals:
- keep UI code simple
- keep summary logic reusable
- make future refactoring to stock_logic.py easy
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from stock_logic import (
    RISK_COLORS,
    RISK_LEVELS,
    as_date,
    get_live_days,
    get_risk_category,
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
    """
    Collapse rows to one record per key_field using worst vendor risk.

    Example:
    - per vendor KPI summary
    - per client KPI summary using worst vendor risk
    - per city vendor summary
    """
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


# -------------------------------------------------------------------
# Public functions used by app.py
# -------------------------------------------------------------------
def enrich_dashboard_rows(df: pd.DataFrame, selected_date: date) -> list[dict[str, Any]]:
    """
    Convert cleaned DataFrame rows into enriched dashboard rows.

    Required input columns:
    - vendor
    - client
    - region
    - pax
    - days_of_stock
    - last_updated
    - gail_png
    Optional:
    - continuity
    """
    if df.empty:
        return []

    rows: list[dict[str, Any]] = []

    for idx, row in df.reset_index(drop=True).iterrows():
        last_updated = as_date(row.get("last_updated"))
        if last_updated is None:
            continue

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
                "working_days_consumed": working_days_between(last_updated, selected_date),
                "live_days": live_days,
                "risk": risk,
                "risk_level": RISK_LEVELS[risk],
                "risk_color": RISK_COLORS[risk],
            }
        )

    return rows



def build_vendor_risk_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Unique vendor KPI summary.

    Uses worst risk per vendor.
    """
    vendors = _worst_risk_group(enriched_rows, "vendor")
    counts = _count_by_risk(vendors)

    return {
        "title": "Total Vendors",
        "value": len(vendors),
        "subtitle": "Unique vendors across dashboard",
        **counts,
    }



def build_client_worst_risk_summary(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Unique client KPI summary.

    Uses worst vendor risk per client.
    """
    clients = _worst_risk_group(enriched_rows, "client")
    counts = _count_by_risk(clients)

    return {
        "title": "Total Clients",
        "value": len(clients),
        "subtitle": "Worst vendor risk mapped per client",
        **counts,
    }



def build_region_cards(enriched_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Build region tiles/cards using unique vendors and worst vendor risk.
    """
    if not enriched_rows:
        return []

    regions = sorted({str(row["region"]).strip() for row in enriched_rows if row.get("region")})
    cards: list[dict[str, Any]] = []

    for region in regions:
        region_rows = [row for row in enriched_rows if row.get("region") == region]
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



def build_city_vendor_summary(enriched_rows: list[dict[str, Any]], selected_city: str) -> dict[str, Any]:
    """
    Build executive summary for selected city using unique vendors.
    """
    city_rows = [row for row in enriched_rows if row.get("region") == selected_city]
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
    """
    Donut chart input for selected city.

    Uses unique vendors in that city.
    """
    summary = build_city_vendor_summary(enriched_rows, selected_city)

    return [
        {"name": "Out of Stock", "value": summary["out"], "color": RISK_COLORS["Out of Stock"]},
        {"name": "Critical", "value": summary["critical"], "color": RISK_COLORS["Critical"]},
        {"name": "Moderate", "value": summary["moderate"], "color": RISK_COLORS["Moderate"]},
        {"name": "Safe", "value": summary["safe"], "color": RISK_COLORS["Safe"]},
    ]



def build_client_pivot_groups(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_risk: str,
    search_text: str = "",
) -> list[dict[str, Any]]:
    """
    Build grouped client-vendor pivot rows.

    Rules:
    - filter to selected city
    - filter to selected risk (mandatory when pivot is shown)
    - search over client/vendor
    - group by client
    - preserve vendor rows under each client
    """
    city_rows = [row for row in enriched_rows if row.get("region") == selected_city]

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
