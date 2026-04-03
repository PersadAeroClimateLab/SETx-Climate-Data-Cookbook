"""
Multi-model ensemble time-series for a single Texas county.

    from line_plot import create_line_plot
    fig = create_line_plot()
    fig.show()

Zero Dash dependencies — works identically in a notebook cell.
Loads historical (1950–2014) + the chosen SSP scenario (2015–2100),
and plots one annual-mean trace per CMIP6 model with a bold
ensemble-mean overlay.
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config import (
    MODELS, LABELS, ALL_COUNTIES_LABEL,
    apply_unit_conversion, get_friendly_variable, get_friendly_scenario,
)

# One colour per model (Plotly qualitative Set1 + extras)
_MODEL_COLOURS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52", "#636EFA",
]


def _load_annual_series(
    model: str,
    scenario: str,
    variable: str,
    county: str,
    data_dir: str,
) -> pd.Series | None:
    """
    Load hist + *scenario* CSV files for one model/county and return an
    annual pandas Series (year integer index).  Returns None if no files found.
    """
    # Always prepend hist for baseline context; deduplicate if scenario == "hist"
    scenarios_to_load = ["hist"] if scenario == "hist" else ["hist", scenario]

    parts: list[pd.Series] = []
    for scen in scenarios_to_load:
        path = os.path.join(data_dir, f"{model}_{scen}_{variable}.csv")
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, index_col="year")
            if county == ALL_COUNTIES_LABEL:
                raw = df.mean(axis=1)
            else:
                raw = df[county]
            parts.append(raw.rename(model))
        except Exception:
            pass

    if not parts:
        return None

    combined = pd.concat(parts).sort_index()
    combined = combined[~combined.index.duplicated(keep="first")]
    return apply_unit_conversion(combined, variable)


def create_line_plot(
    variable: str = "tas",
    scenario: str = "ssp370",
    county: str = ALL_COUNTIES_LABEL,
    data_dir: str = "../data",
) -> go.Figure:
    """
    Annual time series for all CMIP6 models (semi-transparent) plus
    a bold ensemble-mean trace.  A dashed hline marks the 1980–2014
    baseline mean.
    """
    fig = go.Figure()
    loaded: list[pd.Series] = []

    for i, model in enumerate(MODELS):
        s = _load_annual_series(model, scenario, variable, county, data_dir)
        if s is None:
            continue
        loaded.append(s)
        colour = _MODEL_COLOURS[i % len(_MODEL_COLOURS)]

        fig.add_trace(go.Scatter(
            x=s.index,
            y=s.values,
            mode="lines",
            name=model,
            line=dict(color=colour, width=1.2),
            opacity=0.55,
            hovertemplate="%{y:.2f}",
        ))

    if loaded:
        aligned = pd.concat(loaded, axis=1).sort_index()
        mean = aligned.mean(axis=1)

        fig.add_trace(go.Scatter(
            x=mean.index,
            y=mean.values,
            mode="lines",
            name="Multi-Model Mean",
            line=dict(color="black", width=3),
            hovertemplate="%{y:.2f}",
        ))

        baseline_vals = [s.loc[1980:2014].mean() for s in loaded]
        baseline_vals = [v for v in baseline_vals if np.isfinite(v)]
        if baseline_vals:
            baseline = float(np.mean(baseline_vals))
            fig.add_hline(
                y=baseline,
                line_dash="dash",
                line_color="black",
                line_width=1.5,
                annotation_text="1980–2014 baseline",
                annotation_position="bottom",
                annotation_font_size=14,
                annotation_font_color="black",
                annotation_bgcolor="rgba(255,255,255,0.8)",
                annotation_bordercolor="black",
                annotation_borderwidth=1,
                annotation_borderpad=3,
            )

    county_label = "All Counties" if county == ALL_COUNTIES_LABEL else f"{county} County"
    title = (
        f"{county_label} — {get_friendly_variable(variable)}"
        f"<br><sup>Historical + {get_friendly_scenario(scenario)} — Annual Mean</sup>"
    )

    if not loaded:
        fig.update_layout(
            title=dict(text=f"No data available: {title}", x=0.5),
            template="plotly_white",
            font=dict(family="Inter", size=14),
        )
        return fig

    # Invisible trace required to force yaxis2 to render (Plotly limitation)
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        yaxis="y2",
        showlegend=False,
        hoverinfo="skip",
        hovertemplate="%{y:.2f}",
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis_title="Year",
        yaxis=dict(title=LABELS.get(variable, variable)),
        yaxis2=dict(
            overlaying="y",
            side="right",
            matches="y",
            showgrid=False,
            showticklabels=True,
            title="",
        ),
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0,
            xanchor="left", x=1.02,
            font=dict(size=11),
            title="Models"
        ),
        hovermode="x unified",
        template="plotly_white",
        font=dict(family="Inter", size=14),
        margin=dict(r=180, t=80, l=60, b=75),
    )

    return fig


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    _dir = os.path.join(os.path.dirname(__file__), "../data")
    create_line_plot(data_dir=_dir).show()
