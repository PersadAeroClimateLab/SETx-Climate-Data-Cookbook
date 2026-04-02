from os import listdir
import geopandas as gpd
import json
from urllib.request import urlopen
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import numpy as np


if __name__ == "__main__"
    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    with urlopen(url) as resp:
        geojson = json.load(resp)
    
    tx_features = [f for f in geojson["features"] if f["id"].startswith("48")]
    gdf = gpd.GeoDataFrame.from_features(tx_features, crs="EPSG:4326")
    gdf["fips"] = [int(f["id"]) for f in tx_features]
    gdf["name"] = [f["properties"].get("NAME", f["id"]) for f in tx_features]
    shp_mask = None
    
    for variable_name in ["tasmin", "tasmax", "rlds", "rsds", "sfcWind"]:
        zarr_dir = f"/projects/dgs/persad_research/SETx_UIFL_Zarr/{variable_name}"
        for zarr_name in listdir(zarr_dir):
            print(zarr_name)
            ds = xr.open_zarr(f"{zarr_dir}/{zarr_name}").resample(time="YE").mean()
            
            if shp_mask is None:
                lon = ds.lon.values
                lat = ds.lat.values
                
                transform = from_bounds(
                    lon.min(), lat.min(), lon.max(), lat.max(),
                    len(lon), len(lat)
                )
                
                shapes = [(geom, gdf.loc[i]["fips"]) for i, geom in enumerate(gdf.geometry)]
                grid = rasterize(
                    shapes,
                    out_shape=(len(lat), len(lon)),
                    transform=transform,
                    fill=-1,
                    dtype=np.int64,
                    all_touched=False
                )
                shp_mask = xr.DataArray(data=grid, dims=["lat", "lon"], coords=dict(lat=lat, lon=lon))
            
            result = ds[variable_name].groupby(shp_mask).mean(engine="flox", method="cohorts")
            grouped_yrly_means = result.sel(group=result.group.values[1:]).compute()
            years = [int(str(ts).split("-")[0]) for ts in grouped_yrly_means.time.values]
    
            county_names = []
            for fip in grouped_yrly_means.group.values:
                county_names.append(gdf[gdf["fips"] == fip]["name"].iloc[0])
            
            model, scenario, v, ext = zarr_name.split("_")
            grouped_yrly_means.assign_coords({"group": county_names, "time": years}).rename({"group": "county", "time": "year"}).to_pandas().to_csv(f"../data/{model}_{scenario}_{variable_name}.csv")