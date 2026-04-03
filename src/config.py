"""
Shared constants and helpers for all plot modules.
"""

MULTI_MODEL_LABEL = "Multi-Model Mean"
ALL_COUNTIES_LABEL = "All Counties"

MODELS = [
    "BCC-CSM2-MR", "CESM2", "CMCC-ESM2", "CNRM-ESM2-1", "EC-Earth3",
    "FGOALS-g3", "GFDL-CM4", "MPI-ESM1-2-HR", "MRI-ESM2-0", "NorESM2-MM",
]

LABELS = {
    "hurs":    "Relative Humidity (%)",
    "huss":    "Specific Humidity (kg/kg)",
    "rlds":    "Downwelling Longwave Radiation (W/m²)",
    "rsds":    "Downwelling Shortwave Radiation (W/m²)",
    "sfcWind": "Near-Surface Wind Speed (m/s)",
    "tas":     "Temperature (°F)",
    "tasmax":  "Temperature (°F)",
    "tasmin":  "Temperature (°F)",
}

COLORSCALES = {
    "tas":     "Reds",
    "tasmax":  "Reds",
    "tasmin":  "Reds",
    "hurs":    "Teal",
    "huss":    "Teal",
    "rlds":    "Inferno",
    "rsds":    "Plasma",
    "sfcWind": "Viridis",
}

# Fixed colorbar bounds per variable (display units, after unit conversion).
# Covers the full range of Texas county period-means across all models/scenarios/periods.
COLORBAR_RANGES = {
    "tas":     (65,    80),     # °F  — annual mean temp, hist baseline to end-century warming
    "tasmax":  (75,    85),    # °F  — annual mean of daily highs
    "tasmin":  (55,    70),     # °F  — annual mean of daily lows
    "hurs":    (25,    85),     # %   — dry W. Texas to humid E. Texas
    "huss":    (0.011, 0.016),  # kg/kg
    "rlds":    (350,   400),    # W/m²
    "rsds":    (220,   240),    # W/m²
    "sfcWind": (3,   4),    # m/s
}

VARIABLE_OPTIONS = [
    {"label": "Daily Average Temperature",        "value": "tas"},
    {"label": "Daily High Temperature",           "value": "tasmax"},
    {"label": "Daily Low Temperature",            "value": "tasmin"},
    {"label": "Relative Humidity",                "value": "hurs"},
    {"label": "Specific Humidity",                "value": "huss"},
    {"label": "Downwelling Longwave Radiation",   "value": "rlds"},
    {"label": "Downwelling Shortwave Radiation",  "value": "rsds"},
    {"label": "Near-Surface Wind Speed",          "value": "sfcWind"},
]

SCENARIO_OPTIONS = [
    {"label": "Historical (1950–2014)",           "value": "hist"},
    {"label": "Low Severity (SSP1-2.6)",          "value": "ssp126"},
    {"label": "Intermediate Severity (SSP2-4.5)",          "value": "ssp245"},
    {"label": "High Severity (SSP3-7.0)",         "value": "ssp370"},
    {"label": "Highest Severe (SSP5-8.5)",           "value": "ssp585"},
]

# Excludes "hist" — used in the time-series tab where hist is loaded automatically
SSP_OPTIONS = [opt for opt in SCENARIO_OPTIONS if opt["value"] != "hist"]

# Map period options — historical has one fixed baseline; future scenarios offer two windows
MAP_PERIOD_OPTIONS_HIST   = [{"label": "Baseline (1985–2015)",     "value": "1985-2015"}]
MAP_PERIOD_OPTIONS_FUTURE = [
    {"label": "Mid-Century (2035–2065)", "value": "2035-2065"},
    {"label": "End-Century (2070–2100)", "value": "2070-2100"},
]


def parse_period(period: str) -> tuple[int, int]:
    """Return (start_year, end_year) from a 'YYYY-YYYY' period string."""
    start, end = period.split("-")
    return int(start), int(end)


def get_friendly_variable(variable: str) -> str:
    for opt in VARIABLE_OPTIONS:
        if opt["value"] == variable:
            return opt["label"]
    return variable


def get_friendly_scenario(scenario: str) -> str:
    for opt in SCENARIO_OPTIONS:
        if opt["value"] == scenario:
            return opt["label"]
    return scenario


def apply_unit_conversion(da, variable: str):
    """Convert raw CMIP6 output to display units (in-place arithmetic on DataArray)."""
    if "tas" in variable:
        return (da - 273.15) * (9.0 / 5.0) + 32.0
    if variable == "hurs":
        return da * 100.0
    return da
