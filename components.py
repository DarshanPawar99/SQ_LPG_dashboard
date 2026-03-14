"""
components.py

Reusable Dash UI builders for the LPG Stock Tacker Dashboard.

This module keeps presentation separate from:
- data loading
- stock/risk logic
- aggregations

All functions return Dash components.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import plotly.graph_objects as go
from dash import dcc, html


RISK_COLORS = {
    "Out of Stock": "#ef4444",
    "Critical": "#f97316",
    "Moderate": "#eab308",
    "Safe": "#22c55e",
}

RISK_ORDER = ["Out of Stock", "Critical", "Moderate", "Safe"]


# -------------------------------------------------------------------
# Small helpers
# -------------------------------------------------------------------
def _count_dot(color: str, value: int) -> html.Div:
    return html.Div(
        className="count-dot-wrap",
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



def _continuity_pill(value: str) -> html.Span:
    normalized = str(value or "").strip().lower()
    is_yes = normalized == "yes"
    return html.Span(
        "Yes" if is_yes else "No",
        className="continuity-pill continuity-yes" if is_yes else "continuity-pill continuity-no",
    )



def _format_number(value: Any) -> str:
    try:
        number = float(value)
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.2f}"
    except (TypeError, ValueError):
        return str(value)


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
                            dcc.DatePickerSingle(
                                id="selected-date-input",
                                date=selected_date,
                                display_format="DD MMM YYYY",
                                className="dashboard-date-picker",
                            ),
                            html.Div(
                                selected_date.strftime("%d %b %Y").upper(),
                                className="dashboard-date-pill",
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
def build_single_kpi_card(summary: dict[str, Any]) -> html.Div:
    risk_row = html.Div(
        className="kpi-risk-row",
        children=[
            _count_dot(RISK_COLORS["Out of Stock"], int(summary.get("out", 0))),
            _count_dot(RISK_COLORS["Critical"], int(summary.get("critical", 0))),
            _count_dot(RISK_COLORS["Moderate"], int(summary.get("moderate", 0))),
            _count_dot(RISK_COLORS["Safe"], int(summary.get("safe", 0))),
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



def build_kpi_cards(vendor_summary: dict[str, Any], client_summary: dict[str, Any]) -> list[html.Div]:
    return [
        build_single_kpi_card(vendor_summary),
        build_single_kpi_card(client_summary),
    ]


# -------------------------------------------------------------------
# Region cards
# -------------------------------------------------------------------
def build_region_card_grid(region_cards: list[dict[str, Any]], selected_city: str) -> html.Div:
    return html.Div(
        className="region-card-grid",
        children=[
            html.Button(
                id={"type": "region-card", "index": str(card["region"])},
                n_clicks=0,
                className="region-card region-card-active" if card["region"] == selected_city else "region-card",
                children=[
                    html.Div(str(card["region"]), className="region-card-title"),
                    html.Div(f"{_format_number(card.get('total_vendors', 0))} vendors", className="region-card-subtitle"),
                    html.Div(
                        className="region-card-risk-row",
                        children=[
                            _count_dot(RISK_COLORS["Out of Stock"], int(card.get("out", 0))),
                            _count_dot(RISK_COLORS["Critical"], int(card.get("critical", 0))),
                            _count_dot(RISK_COLORS["Moderate"], int(card.get("moderate", 0))),
                            _count_dot(RISK_COLORS["Safe"], int(card.get("safe", 0))),
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
            html.Div(
                active_label,
                className="section-tab-active",
            )
        ],
    )


# -------------------------------------------------------------------
# Executive donut
# -------------------------------------------------------------------
def build_executive_donut(donut_data: list[dict[str, Any]], total_vendors: int) -> html.Div:
    values = [int(item.get("value", 0)) for item in donut_data]
    labels = [str(item.get("name", "")) for item in donut_data]
    colors = [str(item.get("color", RISK_COLORS.get(item.get("name", "Safe"), "#334155"))) for item in donut_data]

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
    )


# -------------------------------------------------------------------
# Executive risk cards
# -------------------------------------------------------------------
def build_executive_cards(city_summary: dict[str, Any], selected_risk: str) -> list[html.Button]:
    card_meta = [
        {
            "key": "Out of Stock",
            "value": city_summary.get("out", 0),
            "pct": city_summary.get("out_pct", 0),
            "subtitle": "Immediate Action",
        },
        {
            "key": "Critical",
            "value": city_summary.get("critical", 0),
            "pct": city_summary.get("critical_pct", 0),
            "subtitle": "1 to 2 Live Days",
        },
        {
            "key": "Moderate",
            "value": city_summary.get("moderate", 0),
            "pct": city_summary.get("moderate_pct", 0),
            "subtitle": "3 to 4 Live Days",
        },
        {
            "key": "Safe",
            "value": city_summary.get("safe", 0),
            "pct": city_summary.get("safe_pct", 0),
            "subtitle": "5+ Live Days",
        },
    ]

    cards: list[html.Button] = []
    for item in card_meta:
        risk = item["key"]
        active = selected_risk == risk
        cards.append(
            html.Button(
                id={"type": "risk-card", "index": risk},
                n_clicks=0,
                className="executive-risk-card executive-risk-card-active" if active else "executive-risk-card",
                children=[
                    html.Div(
                        _format_number(item["value"]),
                        className="executive-risk-value",
                        style={"color": RISK_COLORS[risk]},
                    ),
                    html.Div(risk, className="executive-risk-title"),
                    html.Div(f"{_format_number(item['pct'])}% · {item['subtitle']}", className="executive-risk-subtitle"),
                    html.Div(
                        className="executive-risk-underline",
                        style={"backgroundColor": RISK_COLORS[risk]},
                    ),
                ],
            )
        )

    return cards


# -------------------------------------------------------------------
# Empty pivot state
# -------------------------------------------------------------------
def build_empty_pivot_state() -> html.Div:
    return html.Div(
        className="pivot-empty-state",
        children=[
            html.Div("Select risk category", className="pivot-empty-title"),
        ],
    )


# -------------------------------------------------------------------
# Pivot table section
# -------------------------------------------------------------------
def build_city_pivot_table(
    selected_city: str,
    selected_risk: str,
    pivot_groups: list[dict[str, Any]],
    search_text: str = "",
) -> html.Div:
    table_rows: list[html.Tr] = []

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
            table_rows.append(
                html.Tr(
                    className="pivot-data-row",
                    children=[
                        html.Td(client if idx == 0 else "", className="pivot-cell pivot-cell-dim"),
                        html.Td(str(row.get("vendor", "")), className="pivot-cell pivot-cell-strong"),
                        html.Td(_risk_pill(str(row.get("risk", ""))), className="pivot-cell"),
                        html.Td(_format_number(row.get("live_days", 0)), className="pivot-cell"),
                        html.Td(str(row.get("last_updated", "")), className="pivot-cell pivot-cell-dim"),
                        html.Td(_format_number(row.get("pax", 0)), className="pivot-cell"),
                        html.Td(_continuity_pill(str(row.get("continuity", ""))), className="pivot-cell"),
                    ],
                )
            )

    if not table_rows:
        table_rows.append(
            html.Tr(
                children=[
                    html.Td(
                        "No records found for the selected filters.",
                        colSpan=7,
                        className="pivot-no-records",
                    )
                ]
            )
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
                            html.Div(f"{selected_city} · Client Vendor Pivot", className="pivot-section-title"),
                            html.Div(
                                [
                                    "Expanded for ",
                                    html.Span(selected_risk, className="pivot-selected-risk-text"),
                                    ". One client can have multiple vendors.",
                                ],
                                className="pivot-section-subtitle",
                            ),
                        ],
                    ),
                    html.Div(
                        className="pivot-search-wrap",
                        children=[
                            dcc.Input(
                                id={"type": "pivot-search-input", "index": "main"},
                                value=search_text,
                                type="text",
                                placeholder="Search client or vendor",
                                className="pivot-search-input",
                                debounce=False,
                            )
                        ],
                    ),
                ],
            ),
            html.Div(
                className="pivot-table-wrap",
                children=[
                    html.Table(
                        className="pivot-table",
                        children=[
                            html.Thead(
                                html.Tr(
                                    children=[
                                        html.Th("Client", className="pivot-th"),
                                        html.Th("Vendor", className="pivot-th"),
                                        html.Th("Risk Category", className="pivot-th"),
                                        html.Th("Live LPG Days", className="pivot-th"),
                                        html.Th("Last Updated", className="pivot-th"),
                                        html.Th("Pax", className="pivot-th"),
                                        html.Th("Continuity", className="pivot-th"),
                                    ]
                                )
                            ),
                            html.Tbody(table_rows),
                        ],
                    )
                ],
            ),
        ],
    )
