import json

import numpy as np
import xarray as xr

from src.app.get_values_logger import logger


def load_json(json_file: str, latitude_key: str, longitude_key: str):
    logger.info("Loading json file from %s", json_file)
    with open(json_file, encoding="uft-8") as f:
        points_data = json.load(f)
    # raise error if latitude_key or longitude_key not in any of the points
    if not all([latitude_key in point for point in points_data]):
        raise ValueError(f"Key {latitude_key} not found in all points")
    return points_data, latitude_key, longitude_key


def points_to_xr_dataset(points_data, latitude_key, longitude_key):
    logger.info("Converting points to xarray Dataset")
    latitudes = np.array([point[latitude_key] for point in points_data])
    longitudes = np.array([point[longitude_key] for point in points_data])
    points = xr.Dataset(
        {"x": (["points"], longitudes), "y": (["points"], latitudes)},
    )
    return points


def load_json_to_xr_dataset(json_file: str, latitude_key: str, longitude_key: str):
    points_data, latitude_key, longitude_key = load_json(
        json_file, latitude_key, longitude_key
    )
    return points_to_xr_dataset(points_data, latitude_key, longitude_key)
