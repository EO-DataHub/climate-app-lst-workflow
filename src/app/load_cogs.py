"""
Functions to load cog files into a dataset
"""

import rasterio as rio
import rioxarray as rxr
import xarray as xr
from get_values_logger import logger
from rasterio.session import AWSSession

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
        logger.info("In AWS session")
        ds = rxr.open_rasterio(file_path, mask_and_scale=True)
        ds.attrs["file_path"] = file_path
        logger.info("Loaded COG file from %s", file_path)
    return ds
