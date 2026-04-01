"""
components.py

Reusable Dash UI builders for the LPG Stock Tracker Dashboard.

KPI layout:
- Row 1 (2 cols): Total Vendors | Total Clients (overall, no risk dots)
- Row 2 (4 cols): Vendors with LPG (clickable, risk dots) | Clients with LPG (risk dots) |
                  Vendors with Alternative (clickable) | Clients with Alternative
"""

from __future__ import annotations

from datetime import date
from typing import Any

import plotly.graph_objects as go
from dash import dcc, html

from config import (
    ALT_TYPE_COLORS,
    ALT_TYPE_SHORT_NAMES,
    ALT_TYPE_SUBTITLES,
    MAX_SELECTABLE_DATE,
    MIN_SELECTABLE_DATE,
    RISK_COLORS,
    RISK_SUBTITLES,
)


# -------------------------------------------------------------------
# Small helpers
# -------------------------------------------------------------------
def _count_dot(color: str, value: int, label: str = "") -> html.Div:
    return html.Div(
        className="count-dot-wrap",
        title=f"{label}: {value}" if label else str(value),
        children=[
            html.Span(className="count-dot", style={"backgroundColor": color}),
            html.Span(str(value), className="count-dot-value"),
        ],
    )


def _risk_pill(risk: str) -> html.Span:
    return html.Span(
        risk,
        className="risk-pill",
        style={"backgroundColor": RISK_COLORS.get(risk, "#334155")},
    )


def _alternative_pill(is_alt: bool) -> html.Span:
    return html.Span(
        "Yes" if is_alt else "No",
        className="continuity-pill continuity-yes" if is_alt else "continuity-pill continuity-no",
    )


def _format_number(value: Any) -> str:
    try:
        number = float(value)
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _build_combined_toggle_bar(is_on: bool, toggle_btn_id: dict) -> html.Div:
    cls = "combined-toggle-btn combined-toggle-btn-on" if is_on else "combined-toggle-btn"
    return html.Div(
        className="combined-toggle-bar",
        children=[
            html.Button(
                id=toggle_btn_id,
                n_clicks=0,
                className=cls,
                title="Toggle combined LPG + Alternative view",
                children=[
                    html.Span(className="toggle-knob"),
                    html.Span("Combined View", className="toggle-label"),
                ],
            ),
        ],
    )


# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------
def build_dashboard_header(title: str, subtitle: str, selected_date: date) -> html.Div:
    return html.Div(
        className="dashboard-header",
        children=[
            html.Div(
                className="dashboard-header-inner",
                children=[
                    html.Div(
                        className="dashboard-brand-wrap",
                        children=[
                            html.Div("SMARTQ", className="dashboard-logo-block"),
                            html.Div(
                                className="dashboard-title-wrap",
                                children=[
                                    html.H1(title, className="dashboard-main-title"),
                                    html.P(subtitle, className="dashboard-subtitle"),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="dashboard-date-wrap",
                        children=[
                            html.Div(
                                className="dashboard-date-label",
                                children="Dashboard Date",
                            ),
                            dcc.Input(
                                id="selected-date-input",
                                type="date",
                                value=selected_date.isoformat(),
                                min=MIN_SELECTABLE_DATE.isoformat(),
                                max=MAX_SELECTABLE_DATE.isoformat(),
                                className="dashboard-date-input",
                            ),
                        ],
                    ),
                ],
            )
        ],
    )


# -------------------------------------------------------------------
# KPI cards
# -------------------------------------------------------------------
def _build_kpi_card_lpg_vendor(summary: dict[str, Any], is_active: bool = False) -> html.Button:
    """Clickable KPI card for Vendors with LPG — activates the LPG view."""
    cls = "kpi-card kpi-card-btn"
    if is_active:
        cls += " kpi-card-btn-active"
    risk_row = html.Div(
        className="kpi-risk-row",
        children=[
            _count_dot(RISK_COLORS["Out of Stock"], int(summary.get("out", 0)), "Out of Stock"),
            _count_dot(RISK_COLORS["Critical"], int(summary.get("critical", 0)), "Critical"),
            _count_dot(RISK_COLORS["Moderate"], int(summary.get("moderate", 0)), "Moderate"),
            _count_dot(RISK_COLORS["Safe"], int(summary.get("safe", 0)), "Safe"),
        ],
    )
    return html.Button(
        id="lpg-vendor-kpi-card",
        n_clicks=0,
        className=cls,
        title="Click to explore LPG vendor risk",
        children=[
            html.Div(str(summary.get("title", "")), className="kpi-label"),
            html.Div(_format_number(summary.get("value", 0)), className="kpi-value"),
            html.Div(str(summary.get("subtitle", "")), className="kpi-subtitle"),
            risk_row,
        ],
    )


def _build_kpi_card_with_risk(summary: dict[str, Any]) -> html.Div:
    """KPI card WITH risk dot breakdown (for LPG client card)."""
    risk_row = html.Div(
        className="kpi-risk-row",
        children=[
            _count_dot(RISK_COLORS["Out of Stock"], int(summary.get("out", 0)), "Out of Stock"),
            _count_dot(RISK_COLORS["Critical"], int(summary.get("critical", 0)), "Critical"),
            _count_dot(RISK_COLORS["Moderate"], int(summary.get("moderate", 0)), "Moderate"),
            _count_dot(RISK_COLORS["Safe"], int(summary.get("safe", 0)), "Safe"),
        ],
    )

    return html.Div(
        className="kpi-card",
        children=[
            html.Div(str(summary.get("title", "")), className="kpi-label"),
            html.Div(_format_number(summary.get("value", 0)), className="kpi-value"),
            html.Div(str(summary.get("subtitle", "")), className="kpi-subtitle"),
            risk_row,
        ],
    )


def _build_kpi_card_plain(summary: dict[str, Any], accent_color: str = "") -> html.Div:
    """KPI card WITHOUT risk dots (for overall and alternative client cards)."""
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(str(summary.get("title", "")), className="kpi-label"),
            html.Div(
                _format_number(summary.get("value", 0)),
                className="kpi-value",
                style={"color": accent_color} if accent_color else {},
            ),
            html.Div(str(summary.get("subtitle", "")), className="kpi-subtitle"),
        ],
    )


def _build_kpi_card_alt_vendor(summary: dict[str, Any], is_active: bool = False) -> html.Button:
    """Clickable KPI card for Vendors with Alternative — toggles the alt coverage view."""
    cls = "kpi-card kpi-card-btn"
    if is_active:
        cls += " kpi-card-btn-active"
    return html.Button(
        id="alt-vendor-kpi-card",
        n_clicks=0,
        className=cls,
        title="Click to explore alternative vendor coverage",
        children=[
            html.Div(str(summary.get("title", "")), className="kpi-label"),
            html.Div(
                _format_number(summary.get("value", 0)),
                className="kpi-value",
                style={"color": "#4ade80"},
            ),
            html.Div(str(summary.get("subtitle", "")), className="kpi-subtitle"),
        ],
    )


def build_kpi_section(
    overall_vendor: dict[str, Any],
    overall_client: dict[str, Any],
    lpg_vendor: dict[str, Any],
    lpg_client: dict[str, Any],
    alt_vendor: dict[str, Any],
    alt_client: dict[str, Any],
    alt_view_open: bool = False,
) -> html.Div:
    """
    Build the full KPI section with two rows:
    Row 1: Total Vendors | Total Clients (overall, plain)
    Row 2: LPG Vendors (clickable, risk) | LPG Clients (risk) |
           Alt Vendors (clickable) | Alt Clients (plain)

    LPG vendor card is active when alt_view_open=False.
    Alt vendor card is active when alt_view_open=True.
    """
    return html.Div(
        className="kpi-section",
        children=[
            # Row 1: Overall totals
            html.Div(
                className="kpi-card-row kpi-row-overall",
                children=[
                    _build_kpi_card_plain(overall_vendor),
                    _build_kpi_card_plain(overall_client),
                ],
            ),
            # Row 2: LPG + Alternative split
            html.Div(
                className="kpi-card-row kpi-row-detail",
                children=[
                    _build_kpi_card_lpg_vendor(lpg_vendor, is_active=not alt_view_open),
                    _build_kpi_card_with_risk(lpg_client),
                    _build_kpi_card_alt_vendor(alt_vendor, is_active=alt_view_open),
                    _build_kpi_card_plain(alt_client, accent_color="#77a5ff"),
                ],
            ),
        ],
    )


# -------------------------------------------------------------------
# Region cards
# -------------------------------------------------------------------
def build_region_card_grid(region_cards: list[dict[str, Any]], selected_city: str) -> html.Div:
    if not region_cards:
        return html.Div(
            className="region-card-grid",
            children=[
                html.Div("No regions available", className="pivot-no-records"),
            ],
        )

    return html.Div(
        className="region-card-grid",
        children=[
            html.Button(
                id={"type": "region-card", "index": str(card["region"])},
                n_clicks=0,
                className="region-card region-card-active" if card["region"] == selected_city else "region-card",
                title=f"Select {card['region']}",
                **{"aria-label": f"Select region {card['region']}, {card.get('total_vendors', 0)} vendors"},
                children=[
                    html.Div(str(card["region"]), className="region-card-title"),
                    html.Div(f"{_format_number(card.get('total_vendors', 0))} vendors", className="region-card-subtitle"),
                    html.Div(
                        className="region-card-risk-row",
                        children=[
                            _count_dot(RISK_COLORS["Out of Stock"], int(card.get("out", 0)), "Out of Stock"),
                            _count_dot(RISK_COLORS["Critical"], int(card.get("critical", 0)), "Critical"),
                            _count_dot(RISK_COLORS["Moderate"], int(card.get("moderate", 0)), "Moderate"),
                            _count_dot(RISK_COLORS["Safe"], int(card.get("safe", 0)), "Safe"),
                        ],
                    ),
                ],
            )
            for card in region_cards
        ],
    )


# -------------------------------------------------------------------
# Section tabs
# -------------------------------------------------------------------
def build_section_tabs(active_label: str) -> html.Div:
    return html.Div(
        className="section-tabs-wrap",
        children=[
            html.Div(active_label, className="section-tab-active"),
        ],
    )


# -------------------------------------------------------------------
# Executive donut (with legend)
# -------------------------------------------------------------------
def _build_donut_legend(donut_data: list[dict[str, Any]]) -> html.Div:
    items = []
    for item in donut_data:
        name = str(item.get("name", ""))
        value = int(item.get("value", 0))
        color = str(item.get("color", "#334155"))
        items.append(
            html.Div(
                className="donut-legend-item",
                children=[
                    html.Span(className="donut-legend-swatch", style={"backgroundColor": color}),
                    html.Span(name, className="donut-legend-label"),
                    html.Span(str(value), className="donut-legend-value"),
                ],
            )
        )
    return html.Div(className="donut-legend", children=items)


def build_executive_donut(donut_data: list[dict[str, Any]], total_vendors: int) -> html.Div:
    values = [int(item.get("value", 0)) for item in donut_data]
    labels = [str(item.get("name", "")) for item in donut_data]
    colors = [str(item.get("color", "#334155")) for item in donut_data]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.68,
                sort=False,
                direction="clockwise",
                marker={"colors": colors, "line": {"color": "rgba(0,0,0,0)", "width": 0}},
                textinfo="none",
                hovertemplate="%{label}: %{value}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    return html.Div(
        className="executive-donut-with-legend",
        children=[
            html.Div(
                className="executive-donut-shell",
                children=[
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False, "responsive": True},
                        className="executive-donut-graph",
                    ),
                    html.Div(
                        className="executive-donut-center",
                        children=[
                            html.Div(_format_number(total_vendors), className="executive-donut-total"),
                            html.Div("Vendors", className="executive-donut-caption"),
                        ],
                    ),
                ],
            ),
            _build_donut_legend(donut_data),
        ],
    )


# -------------------------------------------------------------------
# Executive risk cards
# -------------------------------------------------------------------
def build_executive_cards(city_summary: dict[str, Any], selected_risk: str) -> list[html.Button]:
    card_meta = [
        {"key": "Out of Stock", "value": city_summary.get("out", 0), "pct": city_summary.get("out_pct", 0)},
        {"key": "Critical", "value": city_summary.get("critical", 0), "pct": city_summary.get("critical_pct", 0)},
        {"key": "Moderate", "value": city_summary.get("moderate", 0), "pct": city_summary.get("moderate_pct", 0)},
        {"key": "Safe", "value": city_summary.get("safe", 0), "pct": city_summary.get("safe_pct", 0)},
    ]

    cards: list[html.Button] = []
    for item in card_meta:
        risk = item["key"]
        active = selected_risk == risk
        subtitle = RISK_SUBTITLES.get(risk, "")
        cards.append(
            html.Button(
                id={"type": "risk-card", "index": risk},
                n_clicks=0,
                className="executive-risk-card executive-risk-card-active" if active else "executive-risk-card",
                title=f"Filter by {risk}",
                **{"aria-label": f"{risk}: {item['value']} vendors, {item['pct']}%"},
                children=[
                    html.Div(
                        _format_number(item["value"]),
                        className="executive-risk-value",
                        style={"color": RISK_COLORS[risk]},
                    ),
                    html.Div(risk, className="executive-risk-title"),
                    html.Div(f"{_format_number(item['pct'])}% · {subtitle}", className="executive-risk-subtitle"),
                    html.Div(className="executive-risk-underline", style={"backgroundColor": RISK_COLORS[risk]}),
                ],
            )
        )

    return cards


# -------------------------------------------------------------------
# Alternative coverage: city cards
# -------------------------------------------------------------------
def build_alt_city_card_grid(alt_city_cards: list[dict[str, Any]], selected_city: str) -> html.Div:
    if not alt_city_cards:
        return html.Div(
            className="region-card-grid",
            children=[html.Div("No alternative vendor regions available", className="pivot-no-records")],
        )

    return html.Div(
        className="region-card-grid",
        children=[
            html.Button(
                id={"type": "alt-city-card", "index": str(card["region"])},
                n_clicks=0,
                className="region-card region-card-active" if card["region"] == selected_city else "region-card",
                title=f"Filter by {card['region']}",
                **{"aria-label": f"Select region {card['region']}, {card.get('total_vendors', 0)} alt vendors"},
                children=[
                    html.Div(str(card["region"]), className="region-card-title"),
                    html.Div(f"{_format_number(card.get('total_vendors', 0))} alt vendors", className="region-card-subtitle"),
                    html.Div(
                        className="region-card-risk-row",
                        children=[
                            _count_dot(ALT_TYPE_COLORS["GAIL/PNG at Vendor"], int(card.get("gail", 0)), "GAIL/PNG at Vendor"),
                            _count_dot(ALT_TYPE_COLORS["Electrical Equipment Availability"], int(card.get("elec", 0)), "Electrical Equipment"),
                            _count_dot(ALT_TYPE_COLORS["Both"], int(card.get("both", 0)), "Both"),
                        ],
                    ),
                ],
            )
            for card in alt_city_cards
        ],
    )


# -------------------------------------------------------------------
# Alternative coverage: type cards (GAIL / Elec / Both)
# -------------------------------------------------------------------
def build_alt_type_cards(type_summary: dict[str, Any], selected_type: str) -> list[html.Button]:
    card_meta = [
        {"key": "GAIL/PNG at Vendor", "value": type_summary.get("gail", 0), "pct": type_summary.get("gail_pct", 0)},
        {"key": "Electrical Equipment Availability", "value": type_summary.get("elec", 0), "pct": type_summary.get("elec_pct", 0)},
        {"key": "Both", "value": type_summary.get("both", 0), "pct": type_summary.get("both_pct", 0)},
    ]

    cards: list[html.Button] = []
    for item in card_meta:
        key = item["key"]
        active = selected_type == key
        short_name = ALT_TYPE_SHORT_NAMES.get(key, key)
        subtitle = ALT_TYPE_SUBTITLES.get(key, "")
        color = ALT_TYPE_COLORS[key]
        cards.append(
            html.Button(
                id={"type": "alt-type-card", "index": key},
                n_clicks=0,
                className="executive-risk-card executive-risk-card-active" if active else "executive-risk-card",
                title=f"Filter by {key}",
                children=[
                    html.Div(_format_number(item["value"]), className="executive-risk-value", style={"color": color}),
                    html.Div(short_name, className="executive-risk-title"),
                    html.Div(f"{_format_number(item['pct'])}% · {subtitle}", className="executive-risk-subtitle"),
                    html.Div(className="executive-risk-underline", style={"backgroundColor": color}),
                ],
            )
        )

    return cards


# -------------------------------------------------------------------
# LPG pivot table
# -------------------------------------------------------------------
def build_city_pivot_table(
    selected_city: str,
    selected_risk: str,
    pivot_groups: list[dict[str, Any]],
    search_text: str = "",
    combined_on: bool = False,
    toggle_btn_id: dict | None = None,
) -> html.Div:
    if toggle_btn_id is None:
        toggle_btn_id = {"type": "combined-toggle", "index": "lpg"}

    table_rows: list[html.Tr] = []
    total_vendor_rows = sum(g.get("vendor_count", 0) for g in pivot_groups)
    total_pax_all = sum(g.get("total_pax", 0) for g in pivot_groups)

    for group in pivot_groups:
        client = str(group.get("client", ""))
        rows = group.get("rows", [])
        total_pax = group.get("total_pax", 0)
        vendor_count = group.get("vendor_count", len(rows))

        table_rows.append(
            html.Tr(
                className="pivot-group-row",
                children=[
                    html.Td(
                        colSpan=7,
                        className="pivot-group-cell",
                        children=html.Div(
                            className="pivot-group-header",
                            children=[
                                html.Div(
                                    className="pivot-group-title-wrap",
                                    children=[
                                        html.Span("▸", className="pivot-group-arrow"),
                                        html.Span(client, className="pivot-group-title"),
                                    ],
                                ),
                                html.Div(
                                    className="pivot-group-badges",
                                    children=[
                                        html.Span(f"{_format_number(vendor_count)} vendors", className="pivot-badge"),
                                        html.Span(f"{_format_number(total_pax)} pax", className="pivot-badge"),
                                    ],
                                ),
                            ],
                        ),
                    )
                ],
            )
        )

        for idx, row in enumerate(rows):
            risk = str(row.get("risk", ""))
            live_days_color = RISK_COLORS.get(risk, "#e2e8f0")
            table_rows.append(
                html.Tr(
                    className="pivot-data-row",
                    children=[
                        html.Td(client if idx == 0 else "", className="pivot-cell pivot-cell-dim"),
                        html.Td(str(row.get("vendor", "")), className="pivot-cell pivot-cell-strong"),
                        html.Td(_risk_pill(risk), className="pivot-cell"),
                        html.Td(
                            _format_number(row.get("live_days", 0)),
                            className="pivot-cell",
                            style={"color": live_days_color, "fontWeight": "700"},
                        ),
                        html.Td(str(row.get("last_updated", "")), className="pivot-cell pivot-cell-dim"),
                        html.Td(_format_number(row.get("pax", 0)), className="pivot-cell"),
                        html.Td(_alternative_pill(bool(row.get("is_alternative", False))), className="pivot-cell"),
                    ],
                )
            )

    if not table_rows:
        table_rows.append(
            html.Tr(children=[
                html.Td("No records found for the selected filters.", colSpan=7, className="pivot-no-records")
            ])
        )

    summary_text = (
        f"{len(pivot_groups)} clients · {_format_number(total_vendor_rows)} vendor rows · "
        f"{_format_number(total_pax_all)} total pax"
    )

    return html.Div(
        className="pivot-section",
        children=[
            html.Div(
                className="pivot-section-header",
                children=[
                    html.Div(
                        className="pivot-section-title-wrap",
                        children=[
                            html.Div(f"{selected_city} · LPG Vendor Breakdown", className="pivot-section-title"),
                            html.Div(
                                [
                                    "Showing ",
                                    html.Span(
                                        selected_risk if selected_risk else "All Categories",
                                        className="pivot-selected-risk-text",
                                        style={"color": RISK_COLORS.get(selected_risk, "#77a5ff")},
                                    ),
                                    " vendors. One client can have multiple vendors.",
                                ],
                                className="pivot-section-subtitle",
                            ),
                        ],
                    ),
                    html.Div(
                        className="pivot-controls-wrap",
                        children=[
                            _build_combined_toggle_bar(is_on=combined_on, toggle_btn_id=toggle_btn_id),
                            html.Div(
                                className="pivot-search-wrap",
                                children=[
                                    dcc.Input(
                                        id={"type": "pivot-search-input", "index": "main"},
                                        value=search_text,
                                        type="text",
                                        placeholder="Search client or vendor…",
                                        className="pivot-search-input",
                                        debounce=True,
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(className="pivot-summary-bar", children=summary_text),
            html.Div(
                className="pivot-table-wrap",
                children=[
                    html.Table(
                        className="pivot-table",
                        children=[
                            html.Thead(
                                html.Tr(children=[
                                    html.Th("Client", className="pivot-th"),
                                    html.Th("Vendor", className="pivot-th"),
                                    html.Th("Risk Category", className="pivot-th"),
                                    html.Th("Live LPG Days", className="pivot-th"),
                                    html.Th("Last Updated", className="pivot-th"),
                                    html.Th("Pax", className="pivot-th"),
                                    html.Th("Alternative Available", className="pivot-th"),
                                ])
                            ),
                            html.Tbody(table_rows),
                        ],
                    )
                ],
            ),
        ],
    )


# -------------------------------------------------------------------
# Alternative coverage: pivot table (grouped by client, then vendor rows)
# -------------------------------------------------------------------
def build_alt_pivot_table(
    selected_city: str,
    selected_type: str,
    pivot_groups: list[dict[str, Any]],
    search_text: str = "",
    combined_on: bool = False,
    toggle_btn_id: dict | None = None,
) -> html.Div:
    if toggle_btn_id is None:
        toggle_btn_id = {"type": "combined-toggle", "index": "alt"}

    table_rows: list[html.Tr] = []
    total_vendor_rows = sum(g.get("vendor_count", 0) for g in pivot_groups)
    total_pax_all = sum(g.get("total_pax", 0) for g in pivot_groups)

    for group in pivot_groups:
        client = str(group.get("client", ""))
        rows = group.get("rows", [])
        total_pax = group.get("total_pax", 0)
        vendor_count = group.get("vendor_count", len(rows))

        table_rows.append(
            html.Tr(
                className="pivot-group-row",
                children=[
                    html.Td(
                        colSpan=6,
                        className="pivot-group-cell",
                        children=html.Div(
                            className="pivot-group-header",
                            children=[
                                html.Div(className="pivot-group-title-wrap", children=[
                                    html.Span("▸", className="pivot-group-arrow"),
                                    html.Span(client, className="pivot-group-title"),
                                ]),
                                html.Div(className="pivot-group-badges", children=[
                                    html.Span(f"{_format_number(vendor_count)} vendors", className="pivot-badge"),
                                    html.Span(f"{_format_number(total_pax)} pax", className="pivot-badge"),
                                ]),
                            ],
                        ),
                    )
                ],
            )
        )

        for idx, row in enumerate(rows):
            live_days = row.get("live_days", 0)
            risk = str(row.get("risk", ""))
            live_days_color = RISK_COLORS.get(risk, "#e2e8f0")
            alt_type = str(row.get("alt_type", ""))
            type_color = ALT_TYPE_COLORS.get(alt_type, "#334155")
            table_rows.append(
                html.Tr(
                    className="pivot-data-row",
                    children=[
                        html.Td(client if idx == 0 else "", className="pivot-cell pivot-cell-dim"),
                        html.Td(str(row.get("vendor", "")), className="pivot-cell pivot-cell-strong"),
                        html.Td(
                            _format_number(live_days),
                            className="pivot-cell",
                            style={"color": live_days_color, "fontWeight": "700"},
                        ),
                        html.Td(str(row.get("last_updated", "")), className="pivot-cell pivot-cell-dim"),
                        html.Td(_format_number(row.get("pax", 0)), className="pivot-cell"),
                        html.Td(
                            html.Span(alt_type, className="alt-type-pill", style={"backgroundColor": type_color}),
                            className="pivot-cell",
                        ),
                    ],
                )
            )

    if not table_rows:
        table_rows.append(
            html.Tr(children=[
                html.Td("No records found for the selected filters.", colSpan=6, className="pivot-no-records")
            ])
        )

    summary_text = (
        f"{len(pivot_groups)} clients · {_format_number(total_vendor_rows)} vendor rows · "
        f"{_format_number(total_pax_all)} total pax"
    )
    type_color = ALT_TYPE_COLORS.get(selected_type, "#77a5ff")

    return html.Div(
        className="pivot-section",
        children=[
            html.Div(
                className="pivot-section-header",
                children=[
                    html.Div(
                        className="pivot-section-title-wrap",
                        children=[
                            html.Div(f"{selected_city} · Alternative Vendor Detail", className="pivot-section-title"),
                            html.Div(
                                [
                                    "Showing ",
                                    html.Span(
                                        ALT_TYPE_SHORT_NAMES.get(selected_type, selected_type) if selected_type else "All Coverage Types",
                                        className="pivot-selected-risk-text",
                                        style={"color": type_color if selected_type else "#77a5ff"},
                                    ),
                                    " vendors. One vendor can serve multiple clients.",
                                ],
                                className="pivot-section-subtitle",
                            ),
                        ],
                    ),
                    html.Div(
                        className="pivot-controls-wrap",
                        children=[
                            _build_combined_toggle_bar(is_on=combined_on, toggle_btn_id=toggle_btn_id),
                            html.Div(
                                className="pivot-search-wrap",
                                children=[
                                    dcc.Input(
                                        id={"type": "alt-search-input", "index": "main"},
                                        value=search_text,
                                        type="text",
                                        placeholder="Search client or vendor…",
                                        className="pivot-search-input",
                                        debounce=True,
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(className="pivot-summary-bar", children=summary_text),
            html.Div(
                className="pivot-table-wrap",
                children=[
                    html.Table(
                        className="pivot-table",
                        children=[
                            html.Thead(
                                html.Tr(children=[
                                    html.Th("Client", className="pivot-th"),
                                    html.Th("Vendor", className="pivot-th"),
                                    html.Th("Live LPG Days", className="pivot-th"),
                                    html.Th("Last Updated", className="pivot-th"),
                                    html.Th("PAX", className="pivot-th"),
                                    html.Th("Coverage Type", className="pivot-th"),
                                ])
                            ),
                            html.Tbody(table_rows),
                        ],
                    )
                ],
            ),
        ],
    )


# -------------------------------------------------------------------
# Combined pivot table (LPG + Alternative vendors merged)
# -------------------------------------------------------------------
def build_combined_pivot_table(
    selected_city: str,
    pivot_groups: list[dict[str, Any]],
    search_text: str = "",
    combined_on: bool = True,
    toggle_btn_id: dict | None = None,
) -> html.Div:
    if toggle_btn_id is None:
        toggle_btn_id = {"type": "combined-toggle", "index": "lpg"}

    search_index = str(toggle_btn_id.get("index", "lpg"))
    search_input_id = {"type": "combined-search-input", "index": search_index}

    table_rows: list[html.Tr] = []
    total_vendor_rows = sum(g.get("vendor_count", 0) for g in pivot_groups)
    total_pax_all = sum(g.get("total_pax", 0) for g in pivot_groups)

    for group in pivot_groups:
        client = str(group.get("client", ""))
        rows = group.get("rows", [])
        total_pax = group.get("total_pax", 0)
        vendor_count = group.get("vendor_count", len(rows))

        table_rows.append(
            html.Tr(
                className="pivot-group-row",
                children=[
                    html.Td(
                        colSpan=7,
                        className="pivot-group-cell",
                        children=html.Div(
                            className="pivot-group-header",
                            children=[
                                html.Div(className="pivot-group-title-wrap", children=[
                                    html.Span("▸", className="pivot-group-arrow"),
                                    html.Span(client, className="pivot-group-title"),
                                ]),
                                html.Div(className="pivot-group-badges", children=[
                                    html.Span(f"{_format_number(vendor_count)} vendors", className="pivot-badge"),
                                    html.Span(f"{_format_number(total_pax)} pax", className="pivot-badge"),
                                ]),
                            ],
                        ),
                    )
                ],
            )
        )

        for idx, row in enumerate(rows):
            risk = str(row.get("risk", ""))
            live_days_color = RISK_COLORS.get(risk, "#e2e8f0")
            is_alt = bool(row.get("is_alternative", False))
            alt_type = str(row.get("alt_type", ""))

            if is_alt:
                source_cell = html.Td(
                    html.Span(
                        alt_type or "Alternative",
                        className="alt-type-pill",
                        style={"backgroundColor": ALT_TYPE_COLORS.get(alt_type, "#334155")},
                    ),
                    className="pivot-cell",
                )
            else:
                source_cell = html.Td(
                    html.Span("No Alternative", className="source-pill-no-alt"),
                    className="pivot-cell",
                )

            table_rows.append(
                html.Tr(
                    className="pivot-data-row",
                    children=[
                        html.Td(client if idx == 0 else "", className="pivot-cell pivot-cell-dim"),
                        html.Td(str(row.get("vendor", "")), className="pivot-cell pivot-cell-strong"),
                        html.Td(_risk_pill(risk), className="pivot-cell"),
                        html.Td(
                            _format_number(row.get("live_days", 0)),
                            className="pivot-cell",
                            style={"color": live_days_color, "fontWeight": "700"},
                        ),
                        html.Td(str(row.get("last_updated", "")), className="pivot-cell pivot-cell-dim"),
                        html.Td(_format_number(row.get("pax", 0)), className="pivot-cell"),
                        source_cell,
                    ],
                )
            )

    if not table_rows:
        table_rows.append(
            html.Tr(children=[
                html.Td("No records found.", colSpan=7, className="pivot-no-records")
            ])
        )

    summary_text = (
        f"{len(pivot_groups)} clients · {_format_number(total_vendor_rows)} vendor rows · "
        f"{_format_number(total_pax_all)} total pax"
    )

    return html.Div(
        className="pivot-section",
        children=[
            html.Div(
                className="pivot-section-header",
                children=[
                    html.Div(
                        className="pivot-section-title-wrap",
                        children=[
                            html.Div(f"{selected_city} · Combined Vendor View", className="pivot-section-title"),
                            html.Div(
                                "All LPG & alternative vendors for this city.",
                                className="pivot-section-subtitle",
                            ),
                        ],
                    ),
                    html.Div(
                        className="pivot-controls-wrap",
                        children=[
                            _build_combined_toggle_bar(is_on=combined_on, toggle_btn_id=toggle_btn_id),
                            html.Div(
                                className="pivot-search-wrap",
                                children=[
                                    dcc.Input(
                                        id=search_input_id,
                                        value=search_text,
                                        type="text",
                                        placeholder="Search client or vendor…",
                                        className="pivot-search-input",
                                        debounce=True,
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(className="pivot-summary-bar", children=summary_text),
            html.Div(
                className="pivot-table-wrap",
                children=[
                    html.Table(
                        className="pivot-table",
                        children=[
                            html.Thead(
                                html.Tr(children=[
                                    html.Th("Client", className="pivot-th"),
                                    html.Th("Vendor", className="pivot-th"),
                                    html.Th("Risk", className="pivot-th"),
                                    html.Th("Live LPG Days", className="pivot-th"),
                                    html.Th("Last Updated", className="pivot-th"),
                                    html.Th("PAX", className="pivot-th"),
                                    html.Th("Source", className="pivot-th"),
                                ])
                            ),
                            html.Tbody(table_rows),
                        ],
                    )
                ],
            ),
        ],
    )
