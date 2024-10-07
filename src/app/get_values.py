"""
Functions to get values from a cog file
"""

from datetime import datetime
from pathlib import Path

import xarray as xr
from get_values_logger import logger
from load_cogs import load_cog
from pyproj import Transformer
from shortuuid import ShortUUID
from stac_parsing import get_cog_details, get_stac_item


def get_values(cog_url: str, points: xr.Dataset) -> list:
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
    ds = load_cog(cog_url)
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
    return values


def get_values_from_stac(stac_url: list[str], points: xr.Dataset) -> dict:
    """
    Retrieves values from a COG file for given points.

    Parameters:
    - stac_item (dict): STAC item with COG URL.
    - points (xr.Dataset): Dataset of points to extract values for.

    Returns:
    dict: A dictionary with file path and values.
    """
    logger.info("Getting values from STAC item")
    stac_item = get_stac_item(stac_url)
    stac_details = get_cog_details(stac_item)
    logger.info("STAC details: %s", stac_details)
    values = get_values(stac_details["url"], points)
    return {"stac_details": stac_details, "values": values}


def get_values_from_multiple_cogs(stac_urls: list[str], points: xr.Dataset) -> list:
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
    for ds in stac_urls:
        return_values.append(get_values_from_stac(ds, points))
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
        if "id" not in feature["properties"]:
            feature["properties"]["id"] = ShortUUID().random(length=8)
        feature["properties"]["returned_values"] = {}

    for result in results_list:
        dt = result["stac_details"]["datetime"]
        file_name = result["stac_details"]["source_file_name"]
        unit = result["stac_details"]["unit"]
        for index, value in enumerate(result["values"]):
            request_json["features"][index]["properties"]["returned_values"][
                file_name
            ] = {"value": value, "datetime": dt, "unit": unit}
    return request_json
