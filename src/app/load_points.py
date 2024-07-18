"""
Functions to load points into a dataset
"""

import json

import numpy as np
import xarray as xr
from get_values_logger import logger


def load_json(json_file: str) -> dict:
    """
    Loads points data from a JSON file.

    Parameters:
    - json_file (str): Path to the JSON file.
    - latitude_key (str): Key for latitude values.
    - longitude_key (str): Key for longitude values.

    Returns:
    dict: Points data loaded from the file.
    """
    logger.info("Loading json file from %s", json_file)
    with open(json_file, encoding="utf-8") as f:
        points_data = json.load(f)
    return points_data


def check_json(points_data: dict, latitude_key: str, longitude_key: str) -> None:
    """
    Checks if latitude and longitude keys exist in all points.

    Parameters:
    - points_data (dict): Data containing points.
    - latitude_key (str): Key for latitude values.
    - longitude_key (str): Key for longitude values.

    Raises:
    ValueError: If any point lacks a required key.
    """
    if not all(
        [latitude_key in point and longitude_key in point for point in points_data]
    ):
        missing_keys = [
            latitude_key if latitude_key not in point else longitude_key
            for point in points_data
            if latitude_key not in point or longitude_key not in point
        ]
        raise ValueError(f"Missing keys {set(missing_keys)} in some points")


def points_to_xr_dataset(
    points_data: dict, latitude_key: str, longitude_key: str
) -> xr.Dataset:
    """
    Converts points data to an xarray Dataset.

    Parameters:
    - points_data (dict): Data containing points.
    - latitude_key (str): Key for latitude values.
    - longitude_key (str): Key for longitude values.

    Returns:
    xr.Dataset: Dataset with points as coordinates.
    """
    logger.info("Converting points to xarray Dataset")
    latitudes = np.array([point[latitude_key] for point in points_data])
    longitudes = np.array([point[longitude_key] for point in points_data])
    points = xr.Dataset(
        {"x": (["points"], longitudes), "y": (["points"], latitudes)},
    )
    return points


def load_json_to_xr_dataset(
    json_file: str, latitude_key: str, longitude_key: str
) -> xr.Dataset:
    """
    Loads JSON to xarray Dataset with specified keys.

    Parameters:
    - json_file (str): Path to the JSON file.
    - latitude_key (str): Key for latitude values.
    - longitude_key (str): Key for longitude values.

    Returns:
    xr.Dataset: Dataset with points as coordinates.
    """
    points_data, latitude_key, longitude_key = load_json(json_file)
    return points_to_xr_dataset(points_data, latitude_key, longitude_key)
