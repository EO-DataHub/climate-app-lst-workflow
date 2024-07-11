"""
Functions to get values from a cog file
"""

import xarray as xr

from src.app.get_values_logger import logger


def get_values(ds: xr.DataArray, points: xr.Dataset) -> list:
    logger.info("Getting values from COG file")
    return ds.sel(x=points.x, y=points.y, method="nearest").values[0].tolist()
