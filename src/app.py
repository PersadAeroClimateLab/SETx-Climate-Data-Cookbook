"""
SETX-UIFL 1km Climate Atlas — Dash web application.

Run with:  docker run -v $(pwd):/app -p 8080:8080 setx_webapp
Open:      http://localhost:8080

Layout: shared control bar → county choropleth map → multi-model time series.
Clicking a county on the map updates the time series below.
"""

import os

import pandas as pd
from dash import Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from config import (
    MAP_PERIOD_OPTIONS_FUTURE, MAP_PERIOD_OPTIONS_HIST,
    MODELS, MULTI_MODEL_LABEL, ALL_COUNTIES_LABEL, SCENARIO_OPTIONS, VARIABLE_OPTIONS,
)
from line_plot import create_line_plot
from map_plot import create_map_plot

# ── Data directory ─────────────────────────────────────────────────────────────
DATA_DIR = os.environ.get(
    "SETX_DATA_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"),
)

# Derive county list from the header of any available CSV
_sample_csv = os.path.join(DATA_DIR, "BCC-CSM2-MR_hist_tas.csv")
COUNTIES = sorted(pd.read_csv(_sample_csv, nrows=0).columns.drop("year").tolist())

# ── Layout helpers ─────────────────────────────────────────────────────────────
def _ctrl(label: str, child) -> html.Div:
    """Vertically-labelled control block."""
    return html.Div([
        html.Label(label, style={"fontSize": "11px", "fontWeight": "600", "color": "#6b7280", "marginBottom": "2px"}),
        child,
    ], style={"display": "flex", "flexDirection": "column", "flex": "1", "minWidth": "0"})


def _drop(id_: str, options: list, value: str, **kwargs) -> dcc.Dropdown:
    return dcc.Dropdown(id=id_, options=options, value=value, clearable=False, **kwargs)


# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = "SETX-UIFL 1km Climate Atlas"

app.layout = html.Div([

    # ── Control bar ───────────────────────────────────────────────────────────
    html.Div([
        html.Span(
            "SETX-UIFL 1km Climate Atlas",
            style={"fontWeight": "700", "fontSize": "1rem", "whiteSpace": "nowrap", "marginRight": "24px", "color": "#111827"},
        ),
        _ctrl("Variable", _drop("variable", VARIABLE_OPTIONS, "tas")),
        _ctrl("Scenario", _drop("scenario", SCENARIO_OPTIONS, "ssp370")),
        _ctrl("Period",   _drop("map-period", MAP_PERIOD_OPTIONS_FUTURE, "2035-2065")),
        _ctrl("Model",    _drop("model",
            [{"label": MULTI_MODEL_LABEL, "value": MULTI_MODEL_LABEL}] + [{"label": m, "value": m} for m in MODELS],
            MULTI_MODEL_LABEL,
        )),
        _ctrl("County",   _drop("county",
            [{"label": ALL_COUNTIES_LABEL, "value": ALL_COUNTIES_LABEL}] + [{"label": c, "value": c} for c in COUNTIES],
            ALL_COUNTIES_LABEL,
        )),
    ], style={
        "display": "flex",
        "alignItems": "flex-end",
        "gap": "12px",
        "padding": "10px 16px",
        "backgroundColor": "#f9fafb",
        "borderBottom": "1px solid #e5e7eb",
    }),

    # ── Map ───────────────────────────────────────────────────────────────────
    dcc.Graph(
        id="map-graph",
        style={"height": "50vh"},
        config={"displayModeBar": False},
    ),

    # ── Time series ───────────────────────────────────────────────────────────
    dcc.Graph(
        id="line-graph",
        style={"height": "47vh"},
        config={"displayModeBar": False},
    ),

], style={"fontFamily": "Inter, sans-serif", "backgroundColor": "#ffffff"})


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    Output("county", "value"),
    Input("map-graph", "clickData"),
    prevent_initial_call=True,
)
def select_county_from_map(click_data):
    """Propagate a choropleth click to the shared County dropdown."""
    if click_data is None:
        raise PreventUpdate
    return click_data["points"][0]["customdata"]


@app.callback(
    Output("map-period", "options"),
    Output("map-period", "value"),
    Input("scenario", "value"),
    State("map-period", "value"),
)
def update_period_options(scenario: str, current_period: str):
    if scenario == "hist":
        return MAP_PERIOD_OPTIONS_HIST, "1985-2015"
    # Keep current future period if it's already a valid future period, else default
    future_values = {o["value"] for o in MAP_PERIOD_OPTIONS_FUTURE}
    value = current_period if current_period in future_values else "2035-2065"
    return MAP_PERIOD_OPTIONS_FUTURE, value


@app.callback(
    Output("map-graph", "figure"),
    [
        Input("variable",   "value"),
        Input("model",      "value"),
        Input("scenario",   "value"),
        Input("map-period", "value"),
    ],
)
def update_map(variable: str, model: str, scenario: str, period: str):
    return create_map_plot(variable, model, scenario, DATA_DIR, period)


@app.callback(
    Output("line-graph", "figure"),
    [
        Input("variable", "value"),
        Input("scenario", "value"),
        Input("county",   "value"),
    ],
)
def update_line(variable: str, scenario: str, county: str):
    return create_line_plot(variable, scenario, county, DATA_DIR)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True,
        dev_tools_hot_reload=True,
    )
