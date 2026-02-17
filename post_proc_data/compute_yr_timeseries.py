#!/usr/bin/env python3
"""
    compute_yr_timeseries.py

    Took 12 hours and 38 minutes to compute with inputs on local parallel filesystem
    and outputs on local SSD array. Levarging Dask for embarrasingly parallel computation.

    Will need revision for updated datasets (namely precipitation).
"""
from dask.distributed import LocalCluster, Client
from dask import delayed
from os import listdir
from os.path import isdir
import pandas as pd
import xarray


if __name__ == "__main__":
    cluster = LocalCluster(n_workers=80, threads_per_worker=1, memory_limit="5GB")
    client = cluster.get_client()

    head_dir = "/projects/dgs/persad_research/SETx_UIFL_Products"
    output_dir = "/local1/SETx_Analysis_Outputs"

    results =  {}

    for model in listdir(head_dir):
        for scenario in listdir(f"{head_dir}/{model}/"):
            for variable in listdir(f"{head_dir}/{model}/{scenario}/day/"):
                ds_dir_path = f"{head_dir}/{model}/{scenario}/day/{variable}"

                # Exclude a corrupted file
                if ds_dir_path == "/projects/dgs/persad_research/SETx_UIFL_Products/MPI-ESM1-2-HR/ssp585/day/tasmin":
                    continue

                num_files = len(listdir(ds_dir_path))

                # Skipping incomplete datasets
                if (num_files == 65 or num_files == 86) and variable != "precip":
                    ds = xarray.open_mfdataset(f"{ds_dir_path}/*.nc", chunks="auto", parallel=True, data_vars="all", compat="no_conflicts", combine='nested', concat_dim="time")
                    if not isdir(f"{output_dir}/{model}_{scenario}_{variable}_ts.zarr"):
                        ds[variable].mean(dim=["latitude", "longitude"]).chunk({"time":1}).to_zarr(f"{output_dir}/{model}_{scenario}_{variable}_ts.zarr", zarr_format=2)
                    if not isdir(f"{output_dir}/{model}_{scenario}_{variable}_smap.zarr"):
                        ds[variable].mean(dim="time").chunk().to_zarr(f"{output_dir}/{model}_{scenario}_{variable}_smap.zarr", zarr_format=2)

    # Re-read and resample
    def run_compute(path):
        ds_name = path.split("/")[-1]
        entry = ds_name.split("_ts.zarr")[0]
        var_name = entry.split("_")[-1]
        return (entry, xarray.open_zarr(path, consolidated=False, chunks=dict(time=-1))[var_name].resample(time="YE").mean().compute())

    delayed_computes = []
    for ds_name in listdir(output_dir):
        if "ts.zarr" in ds_name:
            delayed_computes.append(delayed(run_compute)(f"{output_dir}/{ds_name}"))

    results = client.compute(delayed_computes, sync=True)

    hist_results = [result for result in results if "_hist" in result[0]]
    fut_results = [result for result in results if "_hist" not in result[0]]

    hist_table = {result[0]: result[1].values for result in hist_results}
    fut_table = {result[0]: result[1].values for result in fut_results}

    pd.DataFrame(hist_table, index=hist_results[0][1].time.values).to_csv("setx_post_proc_historical_yr_timeseries.csv")
    pd.DataFrame(fut_table, index=fut_results[0][1].time.values).to_csv("setx_post_proc_future_yr_timeseries.csv")
