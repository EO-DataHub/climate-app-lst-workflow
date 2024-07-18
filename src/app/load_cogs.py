"""
Functions to load cog files into a dataset
"""

import rasterio as rio
import rioxarray as rxr
import xarray as xr
from rasterio.session import AWSSession

from app.get_values_logger import logger

aws_session = AWSSession(aws_unsigned=True)


def load_cog(file_path: str) -> xr.DataArray:
    """
    Loads a single COG file into an xarray.DataArray.

    Parameters:
    - file_path (str): Path to the COG file.

    Returns:
    xr.DataArray: Data array with COG file data.
    """
    logger.info("Loading COG file from %s", file_path)
    with rio.Env(aws_session):
        ds = rxr.open_rasterio(file_path, mask_and_scale=True)
        ds.attrs["file_path"] = file_path
    return ds


def load_multiple_cogs(file_paths: list[str]) -> list[xr.DataArray]:
    """
    Loads multiple COG files into xarray.DataArrays.

    Parameters:
    - file_paths (list[str]): Paths to COG files.

    Returns:
    list[xr.DataArray]: List of data arrays from COG files.
    """
    logger.info("Loading COG files")
    datasets = []
    for file_path in file_paths:
        ds = load_cog(file_path)
        datasets.append(ds)
    return datasets
