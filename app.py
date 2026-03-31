"""
Main Dash application for the LPG Stock Tacker Dashboard.

KPI layout:
- Row 1: Total Vendors | Total Clients (all, no risk dots)
- Row 2: Vendors with LPG | Clients with LPG | Vendors with Alternative (clickable) | Clients with Alternative
"""

from __future__ import annotations

from datetime import date
from typing import Any

import dash
from dash import Dash, Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from aggregations import (
    build_alt_city_cards,
    build_alt_donut_data,
    build_alt_pivot_groups,
    build_alt_type_summary,
    build_alternative_client_summary,
    build_alternative_vendor_summary,
    build_city_donut_data,
    build_city_vendor_summary,
    build_client_pivot_groups,
    build_client_worst_risk_summary,
    build_overall_client_summary,
    build_overall_vendor_summary,
    build_region_cards,
    build_vendor_risk_summary,
    enrich_dashboard_rows,
)
from components import (
    build_alt_city_card_grid,
    build_alt_empty_pivot_state,
    build_alt_pivot_table,
    build_alt_type_cards,
    build_city_pivot_table,
    build_dashboard_header,
    build_empty_pivot_state,
    build_executive_cards,
    build_executive_donut,
    build_kpi_section,
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
    """Cities from LPG rows only (alternative vendors excluded from city selection)."""
    lpg = [r for r in enriched_rows if not r.get("is_alternative", False)]
    cities = {str(row["region"]).strip() for row in lpg if row.get("region")}
    return sorted(cities)


def get_alt_city_options(enriched_rows: list[dict[str, Any]]) -> list[str]:
    """Cities that have at least one alternative vendor."""
    alt = [r for r in enriched_rows if r.get("is_alternative", False)]
    cities = {str(r["region"]).strip() for r in alt if r.get("region")}
    return sorted(cities)


# -----------------------------
# Initial precomputed state
# -----------------------------
initial_rows = enrich_dashboard_rows(RAW_DF, DEFAULT_SELECTED_DATE)
initial_cities = get_city_options(initial_rows)
initial_city = initial_cities[0] if initial_cities else ""

initial_overall_vendor = build_overall_vendor_summary(initial_rows)
initial_overall_client = build_overall_client_summary(initial_rows)
initial_lpg_vendor = build_vendor_risk_summary(initial_rows)
initial_lpg_client = build_client_worst_risk_summary(initial_rows)
initial_alt_vendor = build_alternative_vendor_summary(initial_rows)
initial_alt_client = build_alternative_client_summary(initial_rows)
initial_region_cards = build_region_cards(initial_rows)
initial_city_summary = build_city_vendor_summary(initial_rows, initial_city)
initial_city_donut = build_city_donut_data(initial_rows, initial_city)
initial_alt_city_cards = build_alt_city_cards(initial_rows)
initial_alt_type_summary = build_alt_type_summary(initial_rows, initial_city)
initial_alt_donut = build_alt_donut_data(initial_rows, initial_city)


app.layout = html.Div(
    className="page-shell",
    children=[
        # ---- stores: LPG view ----
        dcc.Store(id="store-enriched-rows", data=initial_rows),
        dcc.Store(id="store-selected-city", data=initial_city),
        dcc.Store(id="store-selected-risk", data=DEFAULT_SELECTED_RISK),
        dcc.Store(id="store-search-text", data=""),
        dcc.Store(id="store-city-options", data=initial_cities),
        # ---- stores: alt view ----
        dcc.Store(id="store-alt-view-open", data=False),
        dcc.Store(id="store-alt-selected-type", data=""),
        dcc.Store(id="store-alt-search", data=""),
        build_dashboard_header(
            title=APP_TITLE,
            subtitle=APP_SUBTITLE,
            selected_date=DEFAULT_SELECTED_DATE,
        ),
        html.Div(
            className="dashboard-body",
            children=[
                html.Div(
                    id="kpi-section",
                    children=build_kpi_section(
                        overall_vendor=initial_overall_vendor,
                        overall_client=initial_overall_client,
                        lpg_vendor=initial_lpg_vendor,
                        lpg_client=initial_lpg_client,
                        alt_vendor=initial_alt_vendor,
                        alt_client=initial_alt_client,
                        alt_view_open=False,
                    ),
                ),

                # LPG region cards (hidden when alt view is open)
                html.Div(
                    id="region-card-grid",
                    className="region-card-grid-wrapper",
                    children=build_region_card_grid(
                        region_cards=initial_region_cards,
                        selected_city=initial_city,
                    ),
                ),

                # Alt city cards (shown only when alt view is open)
                html.Div(
                    id="alt-city-grid",
                    className="region-card-grid-wrapper",
                    style={"display": "none"},
                    children=build_alt_city_card_grid(
                        alt_city_cards=initial_alt_city_cards,
                        selected_city=initial_city,
                    ),
                ),

                build_section_tabs(active_label=SECTION_TAB_LABEL),

                # LPG executive view (hidden when alt view is open)
                html.Div(
                    id="lpg-executive-view",
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

                # Alternative coverage view (shown only when alt view is open)
                html.Div(
                    id="alt-executive-view",
                    className="executive-view-section",
                    style={"display": "none"},
                    children=[
                        html.Div(
                            className="executive-view-header",
                            children=[
                                html.H2("Alternative Coverage", className="section-title"),
                                html.P(
                                    id="alt-city-label",
                                    className="section-subtitle",
                                    children=f"{initial_city} · Backup Availability Breakdown" if initial_city else "Backup Availability Breakdown",
                                ),
                            ],
                        ),
                        html.Div(
                            className="executive-view-card",
                            children=[
                                html.Div(
                                    id="alt-donut-container",
                                    className="executive-donut-container",
                                    children=build_executive_donut(
                                        donut_data=initial_alt_donut,
                                        total_vendors=initial_alt_type_summary["total_vendors"],
                                    ),
                                ),
                                html.Div(
                                    id="alt-type-cards-container",
                                    className="executive-cards-container",
                                    children=build_alt_type_cards(
                                        type_summary=initial_alt_type_summary,
                                        selected_type="",
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),

                # LPG pivot (hidden when alt view is open)
                html.Div(
                    id="pivot-section-wrapper",
                    className="pivot-section-wrapper",
                    children=build_empty_pivot_state(),
                ),

                # Alt pivot (shown only when alt view is open)
                html.Div(
                    id="alt-pivot-wrapper",
                    className="pivot-section-wrapper",
                    style={"display": "none"},
                    children=build_alt_empty_pivot_state(),
                ),
            ],
        ),
    ],
)


# -----------------------------------------------------------------------
# Callback: selected date -> recompute all enriched rows
# -----------------------------------------------------------------------
@callback(
    Output("store-enriched-rows", "data"),
    Output("store-city-options", "data"),
    Output("store-selected-city", "data"),
    Output("store-selected-risk", "data"),
    Input("selected-date-input", "value"),
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


# -----------------------------------------------------------------------
# Callback: enriched rows / selected city / risk -> update LPG sections
# -----------------------------------------------------------------------
@callback(
    Output("kpi-section", "children"),
    Output("region-card-grid", "children"),
    Output("selected-city-label", "children"),
    Output("executive-donut-container", "children"),
    Output("executive-cards-container", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-selected-risk", "data"),
    State("store-alt-view-open", "data"),
)
def refresh_top_sections(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_risk: str,
    alt_view_open: bool,
):
    overall_vendor = build_overall_vendor_summary(enriched_rows)
    overall_client = build_overall_client_summary(enriched_rows)
    lpg_vendor = build_vendor_risk_summary(enriched_rows)
    lpg_client = build_client_worst_risk_summary(enriched_rows)
    alt_vendor = build_alternative_vendor_summary(enriched_rows)
    alt_client = build_alternative_client_summary(enriched_rows)

    region_cards = build_region_cards(enriched_rows)
    city_summary = build_city_vendor_summary(enriched_rows, selected_city)
    city_donut = build_city_donut_data(enriched_rows, selected_city)

    city_label = f"{selected_city} · Vendor Risk Breakdown" if selected_city else "Vendor Risk Breakdown"

    return (
        build_kpi_section(
            overall_vendor=overall_vendor,
            overall_client=overall_client,
            lpg_vendor=lpg_vendor,
            lpg_client=lpg_client,
            alt_vendor=alt_vendor,
            alt_client=alt_client,
            alt_view_open=bool(alt_view_open),
        ),
        build_region_card_grid(region_cards=region_cards, selected_city=selected_city),
        city_label,
        build_executive_donut(donut_data=city_donut, total_vendors=city_summary["total_vendors"]),
        build_executive_cards(city_summary=city_summary, selected_risk=selected_risk),
    )


# -----------------------------------------------------------------------
# Callback: click region card -> select LPG city
# -----------------------------------------------------------------------
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


# -----------------------------------------------------------------------
# Callback: click executive risk card -> select risk category
# -----------------------------------------------------------------------
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


# -----------------------------------------------------------------------
# Callback: search input -> LPG search store
# -----------------------------------------------------------------------
@callback(
    Output("store-search-text", "data"),
    Input({"type": "pivot-search-input", "index": dash.ALL}, "value"),
    prevent_initial_call=True,
)
def sync_search_text(search_values: list[str | None]) -> str:
    if not search_values:
        return ""
    return str(search_values[-1] or "").strip()


# -----------------------------------------------------------------------
# Callback: LPG pivot section
# -----------------------------------------------------------------------
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
    if not selected_risk and not search_text:
        return build_empty_pivot_state(search_text)

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


# =======================================================================
# ALT VIEW CALLBACKS
# =======================================================================

# -----------------------------------------------------------------------
# Callback: click alt-vendor KPI card -> toggle alt view open/closed
# -----------------------------------------------------------------------
@callback(
    Output("store-alt-view-open", "data"),
    Output("store-alt-selected-type", "data"),
    Input("alt-vendor-kpi-card", "n_clicks"),
    State("store-alt-view-open", "data"),
    prevent_initial_call=True,
)
def toggle_alt_view(n_clicks: int | None, is_open: bool) -> tuple[bool, str]:
    if not n_clicks or n_clicks <= 0:
        raise PreventUpdate
    new_open = not bool(is_open)
    logger.info("Alt view toggled: %s", new_open)
    return new_open, ""


# -----------------------------------------------------------------------
# Callback: alt view open state -> show/hide LPG vs alt sections
# -----------------------------------------------------------------------
@callback(
    Output("region-card-grid", "style"),
    Output("alt-city-grid", "style"),
    Output("lpg-executive-view", "style"),
    Output("alt-executive-view", "style"),
    Output("pivot-section-wrapper", "style"),
    Output("alt-pivot-wrapper", "style"),
    Input("store-alt-view-open", "data"),
)
def toggle_view_visibility(is_open: bool):
    show = {"display": "block"}
    hide = {"display": "none"}
    if is_open:
        return hide, show, hide, show, hide, show
    return show, hide, show, hide, show, hide


# -----------------------------------------------------------------------
# Callback: KPI section highlight update when alt view toggles
# -----------------------------------------------------------------------
@callback(
    Output("kpi-section", "children", allow_duplicate=True),
    Input("store-alt-view-open", "data"),
    State("store-enriched-rows", "data"),
    State("store-selected-risk", "data"),
    prevent_initial_call=True,
)
def refresh_kpi_for_alt_toggle(
    alt_view_open: bool,
    enriched_rows: list[dict[str, Any]],
    selected_risk: str,
):
    overall_vendor = build_overall_vendor_summary(enriched_rows)
    overall_client = build_overall_client_summary(enriched_rows)
    lpg_vendor = build_vendor_risk_summary(enriched_rows)
    lpg_client = build_client_worst_risk_summary(enriched_rows)
    alt_vendor = build_alternative_vendor_summary(enriched_rows)
    alt_client = build_alternative_client_summary(enriched_rows)

    return build_kpi_section(
        overall_vendor=overall_vendor,
        overall_client=overall_client,
        lpg_vendor=lpg_vendor,
        lpg_client=lpg_client,
        alt_vendor=alt_vendor,
        alt_client=alt_client,
        alt_view_open=bool(alt_view_open),
    )


# -----------------------------------------------------------------------
# Callback: click alt city card -> select alt city
# -----------------------------------------------------------------------
@callback(
    Output("store-selected-city", "data", allow_duplicate=True),
    Output("store-alt-selected-type", "data", allow_duplicate=True),
    Input({"type": "alt-city-card", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def select_alt_city(clicks: list[int | None]) -> tuple[str, str]:
    if not clicks or all((v or 0) <= 0 for v in clicks):
        raise PreventUpdate

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate

    return str(trigger["index"]), ""


# -----------------------------------------------------------------------
# Callback: click alt type card -> select coverage type filter
# -----------------------------------------------------------------------
@callback(
    Output("store-alt-selected-type", "data", allow_duplicate=True),
    Input({"type": "alt-type-card", "index": dash.ALL}, "n_clicks"),
    State("store-alt-selected-type", "data"),
    prevent_initial_call=True,
)
def select_alt_type(_: list[int | None], current_type: str) -> str:
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered_id
    if not trigger or "index" not in trigger:
        raise PreventUpdate

    clicked = str(trigger["index"])
    return "" if current_type == clicked else clicked


# -----------------------------------------------------------------------
# Callback: alt city grid refresh
# -----------------------------------------------------------------------
@callback(
    Output("alt-city-grid", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
)
def refresh_alt_city_grid(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
):
    alt_city_cards = build_alt_city_cards(enriched_rows)
    return build_alt_city_card_grid(alt_city_cards=alt_city_cards, selected_city=selected_city)


# -----------------------------------------------------------------------
# Callback: alt executive view refresh (donut + type cards + label)
# -----------------------------------------------------------------------
@callback(
    Output("alt-city-label", "children"),
    Output("alt-donut-container", "children"),
    Output("alt-type-cards-container", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-alt-selected-type", "data"),
)
def refresh_alt_executive_view(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_type: str,
):
    if not selected_city:
        return "Backup Availability Breakdown", [], []

    type_summary = build_alt_type_summary(enriched_rows, selected_city)
    donut_data = build_alt_donut_data(enriched_rows, selected_city)

    label = f"{selected_city} · Backup Availability Breakdown"
    donut = build_executive_donut(donut_data=donut_data, total_vendors=type_summary["total_vendors"])
    type_cards = build_alt_type_cards(type_summary=type_summary, selected_type=selected_type)

    return label, donut, type_cards


# -----------------------------------------------------------------------
# Callback: alt search input -> alt search store
# -----------------------------------------------------------------------
@callback(
    Output("store-alt-search", "data"),
    Input({"type": "alt-search-input", "index": dash.ALL}, "value"),
    prevent_initial_call=True,
)
def sync_alt_search(values: list[str | None]) -> str:
    if not values:
        return ""
    return str(values[-1] or "").strip()


# -----------------------------------------------------------------------
# Callback: alt pivot section
# -----------------------------------------------------------------------
@callback(
    Output("alt-pivot-wrapper", "children"),
    Input("store-enriched-rows", "data"),
    Input("store-selected-city", "data"),
    Input("store-alt-selected-type", "data"),
    Input("store-alt-search", "data"),
)
def refresh_alt_pivot(
    enriched_rows: list[dict[str, Any]],
    selected_city: str,
    selected_type: str,
    search_text: str,
):
    if not selected_type and not search_text:
        return build_alt_empty_pivot_state(search_text)

    pivot_groups = build_alt_pivot_groups(
        enriched_rows=enriched_rows,
        selected_city=selected_city,
        selected_type=selected_type,
        search_text=search_text,
    )

    return build_alt_pivot_table(
        selected_city=selected_city,
        selected_type=selected_type,
        pivot_groups=pivot_groups,
        search_text=search_text,
    )


if __name__ == "__main__":
    app.run(debug=True)
