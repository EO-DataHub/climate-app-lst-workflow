import rasterio as rio
import rioxarray as rxr
import xarray as xr
from rasterio.session import AWSSession

from src.app.get_values_logger import logger

aws_session = AWSSession(aws_unsigned=True)


def load_cog(file_path: str) -> xr.DataArray:
    logger.info("Loading COG file from %s", file_path)
    with rio.Env(aws_session):
        ds = rxr.open_rasterio(file_path, mask_and_scale=True)
    return ds
