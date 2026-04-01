"""
County choropleth map of Texas climate data.

    from map_plot import create_map_plot
    fig = create_map_plot()
    fig.show()

Zero Dash dependencies — works identically in a notebook cell.
"""

import json
import os
from urllib.request import urlopen

import geopandas as gpd
import numpy as np
import xarray as xr
import plotly.graph_objects as go

from config import (
    LABELS, COLORSCALES, COLORBAR_RANGES, MULTI_MODEL_LABEL,
    apply_unit_conversion, get_friendly_variable, get_friendly_scenario, parse_period,
)

# ── Texas county name → 5-digit FIPS string ──────────────────────────────────
TEXAS_FIPS = {
    "Anderson": "48001", "Andrews": "48003", "Angelina": "48005",
    "Aransas": "48007", "Archer": "48009", "Armstrong": "48011",
    "Atascosa": "48013", "Austin": "48015", "Bailey": "48017",
    "Bandera": "48019", "Bastrop": "48021", "Baylor": "48023",
    "Bee": "48025", "Bell": "48027", "Bexar": "48029",
    "Blanco": "48031", "Borden": "48033", "Bosque": "48035",
    "Bowie": "48037", "Brazoria": "48039", "Brazos": "48041",
    "Brewster": "48043", "Briscoe": "48045", "Brooks": "48047",
    "Brown": "48049", "Burleson": "48051", "Burnet": "48053",
    "Caldwell": "48055", "Calhoun": "48057", "Callahan": "48059",
    "Cameron": "48061", "Camp": "48063", "Carson": "48065",
    "Cass": "48067", "Castro": "48069", "Chambers": "48071",
    "Cherokee": "48073", "Childress": "48075", "Clay": "48077",
    "Cochran": "48079", "Coke": "48081", "Coleman": "48083",
    "Collin": "48085", "Collingsworth": "48087", "Colorado": "48089",
    "Comal": "48091", "Comanche": "48093", "Concho": "48095",
    "Cooke": "48097", "Coryell": "48099", "Cottle": "48101",
    "Crane": "48103", "Crockett": "48105", "Crosby": "48107",
    "Culberson": "48109", "Dallam": "48111", "Dallas": "48113",
    "Dawson": "48115", "Deaf Smith": "48117", "Delta": "48119",
    "Denton": "48121", "DeWitt": "48123", "Dickens": "48125",
    "Dimmit": "48127", "Donley": "48129", "Duval": "48131",
    "Eastland": "48133", "Ector": "48135", "Edwards": "48137",
    "Ellis": "48139", "El Paso": "48141", "Erath": "48143",
    "Falls": "48145", "Fannin": "48147", "Fayette": "48149",
    "Fisher": "48151", "Floyd": "48153", "Foard": "48155",
    "Fort Bend": "48157", "Franklin": "48159", "Freestone": "48161",
    "Frio": "48163", "Gaines": "48165", "Galveston": "48167",
    "Garza": "48169", "Gillespie": "48171", "Glasscock": "48173",
    "Goliad": "48175", "Gonzales": "48177", "Gray": "48179",
    "Grayson": "48181", "Gregg": "48183", "Grimes": "48185",
    "Guadalupe": "48187", "Hale": "48189", "Hall": "48191",
    "Hamilton": "48193", "Hansford": "48195", "Hardeman": "48197",
    "Hardin": "48199", "Harris": "48201", "Harrison": "48203",
    "Hartley": "48205", "Haskell": "48207", "Hays": "48209",
    "Hemphill": "48211", "Henderson": "48213", "Hidalgo": "48215",
    "Hill": "48217", "Hockley": "48219", "Hood": "48221",
    "Hopkins": "48223", "Houston": "48225", "Howard": "48227",
    "Hudspeth": "48229", "Hunt": "48231", "Hutchinson": "48233",
    "Irion": "48235", "Jack": "48237", "Jackson": "48239",
    "Jasper": "48241", "Jeff Davis": "48243", "Jefferson": "48245",
    "Jim Hogg": "48247", "Jim Wells": "48249", "Johnson": "48251",
    "Jones": "48253", "Karnes": "48255", "Kaufman": "48257",
    "Kendall": "48259", "Kenedy": "48261", "Kent": "48263",
    "Kerr": "48265", "Kimble": "48267", "King": "48269",
    "Kinney": "48271", "Kleberg": "48273", "Knox": "48275",
    "Lamar": "48277", "Lamb": "48279", "Lampasas": "48281",
    "La Salle": "48283", "Lavaca": "48285", "Lee": "48287",
    "Leon": "48289", "Liberty": "48291", "Limestone": "48293",
    "Lipscomb": "48295", "Live Oak": "48297", "Llano": "48299",
    "Loving": "48301", "Lubbock": "48303", "Lynn": "48305",
    "McCulloch": "48307", "McLennan": "48309", "McMullen": "48311",
    "Madison": "48313", "Marion": "48315", "Martin": "48317",
    "Mason": "48319", "Matagorda": "48321", "Maverick": "48323",
    "Medina": "48325", "Menard": "48327", "Midland": "48329",
    "Milam": "48331", "Mills": "48333", "Mitchell": "48335",
    "Montague": "48337", "Montgomery": "48339", "Moore": "48341",
    "Morris": "48343", "Motley": "48345", "Nacogdoches": "48347",
    "Navarro": "48349", "Newton": "48351", "Nolan": "48353",
    "Nueces": "48355", "Ochiltree": "48357", "Oldham": "48359",
    "Orange": "48361", "Palo Pinto": "48363", "Panola": "48365",
    "Parker": "48367", "Parmer": "48369", "Pecos": "48371",
    "Polk": "48373", "Potter": "48375", "Presidio": "48377",
    "Rains": "48379", "Randall": "48381", "Reagan": "48383",
    "Real": "48385", "Red River": "48387", "Reeves": "48389",
    "Refugio": "48391", "Roberts": "48393", "Robertson": "48395",
    "Rockwall": "48397", "Runnels": "48399", "Rusk": "48401",
    "Sabine": "48403", "San Augustine": "48405", "San Jacinto": "48407",
    "San Patricio": "48409", "San Saba": "48411", "Schleicher": "48413",
    "Scurry": "48415", "Shackelford": "48417", "Shelby": "48419",
    "Sherman": "48421", "Smith": "48423", "Somervell": "48425",
    "Starr": "48427", "Stephens": "48429", "Sterling": "48431",
    "Stonewall": "48433", "Sutton": "48435", "Swisher": "48437",
    "Tarrant": "48439", "Taylor": "48441", "Terrell": "48443",
    "Terry": "48445", "Throckmorton": "48447", "Titus": "48449",
    "Tom Green": "48451", "Travis": "48453", "Trinity": "48455",
    "Tyler": "48457", "Upshur": "48459", "Upton": "48461",
    "Uvalde": "48463", "Val Verde": "48465", "Van Zandt": "48467",
    "Victoria": "48469", "Walker": "48471", "Waller": "48473",
    "Ward": "48475", "Washington": "48477", "Webb": "48479",
    "Wharton": "48481", "Wheeler": "48483", "Wichita": "48485",
    "Wilbarger": "48487", "Willacy": "48489", "Williamson": "48491",
    "Wilson": "48493", "Winkler": "48495", "Wise": "48497",
    "Wood": "48499", "Yoakum": "48501", "Young": "48503",
    "Zapata": "48505", "Zavala": "48507",
}

_GEOJSON_CACHE: dict | None = None
_COUNTY_GDF_CACHE: gpd.GeoDataFrame | None = None


def _load_geojson() -> dict:
    global _GEOJSON_CACHE
    if _GEOJSON_CACHE is None:
        url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
        with urlopen(url) as resp:
            _GEOJSON_CACHE = json.load(resp)
    return _GEOJSON_CACHE


def _get_texas_county_gdf() -> gpd.GeoDataFrame:
    global _COUNTY_GDF_CACHE
    if _COUNTY_GDF_CACHE is None:
        geojson = _load_geojson()
        tx_features = [f for f in geojson["features"] if f["id"].startswith("48")]
        gdf = gpd.GeoDataFrame.from_features(tx_features, crs="EPSG:4326")
        gdf["fips"] = [f["id"] for f in tx_features]
        gdf["name"] = [f["properties"].get("NAME", f["id"]) for f in tx_features]
        _COUNTY_GDF_CACHE = gdf
    return _COUNTY_GDF_CACHE


def _aggregate_grid_to_counties(mean_da) -> gpd.GeoDataFrame:
    """Spatially aggregate a (lat, lon) DataArray to Texas county means."""
    tx_gdf = _get_texas_county_gdf()

    lats = mean_da.coords["lat"].values
    lons = mean_da.coords["lon"].values
    vals = mean_da.values

    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    flat_lats = lat_grid.ravel()
    flat_lons = lon_grid.ravel()
    flat_vals = vals.ravel()

    finite_mask = np.isfinite(flat_vals)
    points_gdf = gpd.GeoDataFrame(
        {"value": flat_vals[finite_mask]},
        geometry=gpd.points_from_xy(flat_lons[finite_mask], flat_lats[finite_mask]),
        crs="EPSG:4326",
    )

    joined = gpd.sjoin(points_gdf, tx_gdf[["fips", "name", "geometry"]], how="left", predicate="within")
    county_means = joined.groupby("fips").agg({"value": "mean", "name": "first"}).reset_index()
    return county_means


def _load_multimodel_county_means(variable: str, scenario: str, data_dir: str, period: str) -> gpd.GeoDataFrame:
    """Load multi-model mean NetCDF and return county-aggregated means for the given period."""
    multi_model_dir = os.path.join(
        os.path.dirname(os.path.abspath(data_dir.rstrip(os.sep))), "multi-model"
    )
    nc_path = os.path.join(multi_model_dir, f"{variable}-{scenario}_multimodel_mean.nc")
    ds = xr.open_dataset(nc_path)
    start_year, end_year = parse_period(period)
    da = ds[variable].sel(year=slice(start_year, end_year))
    da = apply_unit_conversion(da.mean(dim="year"), variable).load()
    return _aggregate_grid_to_counties(da)


def create_map_plot(
    variable: str = "tas",
    model: str = MULTI_MODEL_LABEL,
    scenario: str = "ssp370",
    data_dir: str = "../data/SETx_County_data",
    period: str = "2035-2065",
) -> go.Figure:
    """
    Choropleth of Texas counties coloured by the period mean of *variable*
    for the given *model*, *scenario*, and *period* (e.g. '2035-2065').
    """
    try:
        geojson = _load_geojson()
        start_year, end_year = parse_period(period)

        if model == MULTI_MODEL_LABEL:
            county_df = _load_multimodel_county_means(variable, scenario, data_dir, period)
            fips  = county_df["fips"].tolist()
            vals  = county_df["value"].tolist()
            names = county_df["name"].tolist()
        else:
            zarr_path = os.path.join(data_dir, f"{model}_{scenario}_{variable}.zarr")
            ds = xr.open_zarr(zarr_path)
            da = apply_unit_conversion(ds[variable].isel(model=0), variable)
            da = da.sel(time=(da.time.dt.year >= start_year) & (da.time.dt.year <= end_year))
            mean_da = da.mean(dim="time").load()

            counties  = mean_da.coords["county"].values.tolist()
            values    = mean_da.values.tolist()
            rows = [(TEXAS_FIPS[c], v, c) for c, v in zip(counties, values) if c in TEXAS_FIPS]
            if not rows:
                raise ValueError("No counties matched the FIPS lookup table.")
            fips, vals, names = map(list, zip(*rows))

        period_label = f"{start_year}–{end_year}"
        zmin, zmax = COLORBAR_RANGES[variable]
        fig = go.Figure(go.Choropleth(
            geojson=geojson,
            locations=fips,
            z=vals,
            zmin=zmin,
            zmax=zmax,
            colorscale=COLORSCALES[variable],
            colorbar=dict(title=dict(text=LABELS[variable], side="right")),
            customdata=names,
            hovertemplate="<b>%{customdata} County</b><br>" + LABELS[variable] + ": %{z:.2f}<extra></extra>",
            marker_line_color="white",
            marker_line_width=0.5,
        ))

        title = (
            f"{get_friendly_variable(variable)}"
            f"<br><sup>{model} — {get_friendly_scenario(scenario)} — {period_label} Mean</sup>"
        )

        fig.update_layout(
            title=dict(text=title, x=0.5),
            geo=dict(
                scope="usa",
                projection_type="albers usa",
                showlakes=True,
                showland=True,
                landcolor="rgba(230,230,230,0.4)",
                fitbounds="locations",
            ),
            template="plotly_white",
            font=dict(family="Inter", size=14),
            margin=dict(r=20, l=20, t=80, b=20),
        )

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(
            title=f"Error loading data: {e}",
            template="plotly_white",
        )

    return fig


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    _dir = os.path.join(os.path.dirname(__file__), "../data/SETx_County_data")
    create_map_plot(data_dir=_dir).show()
