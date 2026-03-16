"""
Main Dash application for the LPG Stock Tacker Dashboard.

Improvements:
- Graceful startup even when data file is missing
- All magic strings replaced with config constants
- Removed duplicate date pill (redundant with date picker)
- Cleaner callback structure
"""

from __future__ import annotations

from datetime import date
from typing import Any

import dash
from dash import Dash, Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from aggregations import (
    build_city_donut_data,
    build_city_vendor_summary,
    build_client_pivot_groups,
    build_client_worst_risk_summary,
    build_region_cards,
    build_vendor_risk_summary,
    enrich_dashboard_rows,
)
from components import (
    build_city_pivot_table,
    build_dashboard_header,
    build_empty_pivot_state,
    build_executive_cards,
    build_executive_donut,
    build_kpi_cards,
    build_region_card_grid,
    build_section_tabs,
)
from config import (
    APP_SUBTITLE,
    APP_TITLE,
    DEFAULT_SELECTED_DATE,
    DEFAULT_SELECTED_RISK,
    SECTION_TAB_LABEL,
)
from data_loader import load_dashboard_data
from logger import setup_logger


logger = setup_logger(__name__)

app: Dash = Dash(
    __name__,
    title=APP_TITLE,
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)
server = app.server


# Load once at startup. data_loader returns empty DF on failure.
RAW_DF = load_dashboard_data()
logger.info("Dashboard dataset loaded at startup with %s rows", len(RAW_DF))


# -----------------------------
# Helper functions
# -----------------------------
def get_city_options(enriched_rows: list[dict[str, Any]]) -> list[str]:
    cities = {str(row["region"]).strip() for row in enriched_rows if row.get("region")}
    return sorted(cities)


# -----------------------------
# Initial precomputed state
# -----------------------------
initial_rows = enrich_dashboard_rows(RAW_DF, DEFAULT_SELECTED_DATE)
initial_cities = get_city_options(initial_rows)
initial_city = initial_cities[0] if initial_cities else ""

initial_vendor_summary = build_vendor_risk_summary(initial_rows)
initial_client_summary = build_client_worst_risk_summary(initial_rows)
initial_region_cards = build_region_cards(initial_rows)
initial_city_summary = build_city_vendor_summary(initial_rows, initial_city)
initial_city_donut = build_city_donut_data(initial_rows, initial_city)


app.layout = html.Div(
    className="page-shell",
    children=[
        dcc.Store(id="store-enriched-rows", data=initial_rows),
        dcc.Store(id="store-selected-city", data=initial_city),
        dcc.Store(id="store-selected-risk", data=DEFAULT_SELECTED_RISK),
        dcc.Store(id="store-search-text", data=""),
        dcc.Store(id="store-city-options", data=initial_cities),
        build_dashboard_header(
            title=APP_TITLE,
            subtitle=APP_SUBTITLE,
            selected_date=DEFAULT_SELECTED_DATE,
        ),
        html.Div(
            className="dashboard-body",
            children=[
                html.Div(
                    id="kpi-card-row",
                    className="kpi-card-row",
                    children=build_kpi_cards(
                        vendor_summary=initial_vendor_summary,
                        client_summary=initial_client_summary,
                    ),
                ),
                html.Div(
                    id="region-card-grid",
                    className="region-card-grid-wrapper",
                    children=build_region_card_grid(
                        region_cards=initial_region_cards,
                        selected_city=initial_city,
                    ),
                ),
                build_section_tabs(active_label=SECTION_TAB_LABEL),
                html.Div(
                    className="executive-view-section",
                    children=[
                        html.Div(
                            className="executive-view-header",
                            children=[
                                html.H2("Executive View", className="section-title"),
                                html.P(
                                    id="selected-city-label",
                                    className="section-subtitle",
                                    children=f"{initial_city} · Vendor Risk Breakdown" if initial_city else "Vendor Risk Breakdown",
                                ),
                            ],
                        ),
                        html.Div(
                            className="executive-view-card",
                            children=[
                                html.Div(
                                    id="executive-donut-container",
                                    className="executive-donut-container",
                                    children=build_executive_donut(
                                        donut_data=initial_city_donut,
                                        total_vendors=initial_city_summary["total_vendors"],
                                    ),
                                ),
                                html.Div(
                                    id="executive-cards-container",
                                    className="executive-cards-container",
                                    children=build_executive_cards(
                                        city_summary=initial_city_summary,
                                        selected_risk=DEFAULT_SELECTED_RISK,
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="pivot-section-wrapper",
                    className="pivot-section-wrapper",
                    children=build_empty_pivot_state(),
                ),
            ],
        ),
    ],
)


# -----------------------------
# Callback: selected date -> recompute
# -----------------------------
@callback(
    Output("store-enriched-rows", "data"),
    Output("store-city-options", "data"),
    Output("store-selected-city", "data"),
    Output("store-selected-risk", "data"),
    Input("selected-date-input", "date"),
    State("store-selected-city", "data"),
)
def refresh_dashboard_for_date(
    selected_date_str: str | None,
    current_city: str | None,
) -> tuple[list[dict[str, Any]], list[str], str, str]:
    logger.info("Refreshing dashboard for selected date: %s", selected_date_str)
    selected_date = date.fromisoformat(selected_date_str) if selected_date_str else DEFAULT_SELECTED_DATE
    enriched_rows = enrich_dashboard_rows(RAW_DF, selected_date)
    city_options = get_city_options(enriched_rows)

    if current_city and current_city in city_options:
        city_value = current_city
    else:
        city_value = city_options[0] if city_options else ""

    return enriched_rows, city_options, city_value, ""


# -----------------------------
# Callback: enriched rows / selected city -> update sections
# -----------------------------
@callback(
    Output("kpi-card-row", "children"),
    Output("region-card-grid", "children"),
    Output("selected-city-label", "children"),
    Output("executive-donut-container", "children"),
    Output("executive-cards-container", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-selected-risk", "data"),
)
def refresh_top_sections(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_risk: str,
):
    vendor_summary = build_vendor_risk_summary(enriched_rows)
    client_summary = build_client_worst_risk_summary(enriched_rows)
    region_cards = build_region_cards(enriched_rows)
    city_summary = build_city_vendor_summary(enriched_rows, selected_city)
    city_donut = build_city_donut_data(enriched_rows, selected_city)

    city_label = f"{selected_city} · Vendor Risk Breakdown" if selected_city else "Vendor Risk Breakdown"

    return (
        build_kpi_cards(vendor_summary=vendor_summary, client_summary=client_summary),
        build_region_card_grid(region_cards=region_cards, selected_city=selected_city),
        city_label,
        build_executive_donut(donut_data=city_donut, total_vendors=city_summary["total_vendors"]),
        build_executive_cards(city_summary=city_summary, selected_risk=selected_risk),
    )


# -----------------------------
# Callback: click region card
# -----------------------------
@callback(
    Output("store-selected-city", "data", allow_duplicate=True),
    Output("store-selected-risk", "data", allow_duplicate=True),
    Input({"type": "region-card", "index": dash.ALL}, "n_clicks"),
    State({"type": "region-card", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def select_city_from_region_card(
    clicks: list[int | None],
    __: list[dict[str, str]],
) -> tuple[str, str]:
    if not clicks or all((value or 0) <= 0 for value in clicks):
        raise PreventUpdate

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate

    return str(trigger["index"]), ""


# -----------------------------
# Callback: click executive risk card
# -----------------------------
@callback(
    Output("store-selected-risk", "data", allow_duplicate=True),
    Input({"type": "risk-card", "index": dash.ALL}, "n_clicks"),
    State("store-selected-risk", "data"),
    prevent_initial_call=True,
)
def select_risk_category(
    _: list[int | None],
    current_risk: str,
) -> str:
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate

    clicked_risk = str(trigger["index"])
    next_risk = "" if current_risk == clicked_risk else clicked_risk
    logger.info("Risk selection: %s -> %s", current_risk, next_risk)
    return next_risk


# -----------------------------
# Callback: search input -> store
# -----------------------------
@callback(
    Output("store-search-text", "data"),
    Input({"type": "pivot-search-input", "index": dash.ALL}, "value"),
    prevent_initial_call=True,
)
def sync_search_text(search_values: list[str | None]) -> str:
    if not search_values:
        return ""
    return str(search_values[-1] or "").strip()


# -----------------------------
# Callback: pivot section
# -----------------------------
@callback(
    Output("pivot-section-wrapper", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-selected-risk", "data"),
    Input("store-search-text", "data"),
)
def refresh_pivot_section(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_risk: str,
    search_text: str,
):
    if not selected_risk:
        return build_empty_pivot_state()

    pivot_groups = build_client_pivot_groups(
        enriched_rows=enriched_rows,
        selected_city=selected_city,
        selected_risk=selected_risk,
        search_text=search_text,
    )

    return build_city_pivot_table(
        selected_city=selected_city,
        selected_risk=selected_risk,
        pivot_groups=pivot_groups,
        search_text=search_text,
    )


if __name__ == "__main__":
    app.run(debug=True)
