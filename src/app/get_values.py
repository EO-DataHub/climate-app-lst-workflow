"""
Functions to get values from a cog file
"""

import xarray as xr

from app.get_values_logger import logger


def get_values(ds: xr.DataArray, points: xr.Dataset) -> list:
    logger.info("Getting values from COG file")
    values = ds.sel(x=points.x, y=points.y, method="nearest").values[0].tolist()
    # replace nan with None
    values = [None if str(v) == "nan" else v for v in values]
    return {"file_path": ds.attrs["file_path"], "values": values}


def get_values_from_multiple_cogs(
    datasets: list[xr.DataArray], points: xr.Dataset
) -> list:
    logger.info("Getting values from multiple COG files")
    return_values = []
    for ds in datasets:
        return_values.append(get_values(ds, points))
    return return_values


def merge_results_into_dict(results_list: list, request_json: dict) -> dict:
    for file_info in results_list:
        file_values = file_info["values"]
        file_path = file_info["file_path"]
        for index, value in enumerate(file_values):
            request_json[index][file_path] = value
    return request_json
