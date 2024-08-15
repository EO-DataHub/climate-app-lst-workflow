"""
Functions to get values from a cog file
"""

from pathlib import Path

import xarray as xr
from get_values_logger import logger
from pyproj import Transformer
from shortuuid import ShortUUID


def get_values(ds: xr.DataArray, points: xr.Dataset) -> list:
    """
    Extracts values from a COG file for specified points.

    Parameters:
    - ds (xr.DataArray): Data array to extract values from.
    - points (xr.Dataset): Dataset containing points of interest.

    Returns:
    list: A list containing the file path and extracted values,
    replacing NaNs with None.
    """
    logger.info("Getting values from COG file")
    ds_crs = ds.rio.crs
    if ds_crs == "EPSG:4326":
        points_transformed = points
    else:
        transformer = Transformer.from_crs("EPSG:4326", ds_crs, always_xy=True)
        x_t, y_t = transformer.transform(points.x, points.y)  # pylint: disable=E0633
        points_transformed = xr.Dataset(
            {"x": (["points"], x_t), "y": (["points"], y_t)},
        )
    values = (
        ds.sel(x=points_transformed.x, y=points_transformed.y, method="nearest")
        .values[0]
        .tolist()
    )
    # replace nan with None
    values = [None if str(v) == "nan" else v for v in values]
    source_file_name = Path(ds.attrs["file_path"]).stem
    return {"file_path": source_file_name, "values": values}


def get_values_from_multiple_cogs(
    datasets: list[xr.DataArray], points: xr.Dataset
) -> list:
    """
    Retrieves values from multiple COG files for given points.

    Parameters:
    - datasets (list[xr.DataArray]): List of data arrays.
    - points (xr.Dataset): Dataset of points to extract values for.

    Returns:
    list: A list of dictionaries with file paths and values.
    """
    logger.info("Getting values from multiple COG files")
    return_values = []
    for ds in datasets:
        return_values.append(get_values(ds, points))
    return return_values


def merge_results_into_dict(results_list: list, request_json: dict) -> dict:
    """
    Merges extracted values into the original request JSON.

    Parameters:
    - results_list (list): List of dicts with file paths and values.
    - request_json (dict): Original request GeoJSON to merge results into.

    Returns:
    dict: The updated request JSON with merged results.
    """
    for feature in request_json["features"]:
        if "id" in feature["properties"]:
            feature["properties"]["original_id"] = feature["properties"]["id"]
        feature["properties"]["id"] = ShortUUID().random(length=8)
        feature["properties"]["returned_values"] = {}

    for file_info in results_list:
        for index, value in enumerate(file_info["values"]):
            request_json["features"][index]["properties"]["returned_values"][
                file_info["file_path"]
            ] = value
    return request_json
