import rioxarray as rxr
import xarray as xr

from app.get_values_logger import logger
from app.stac_parsing import DatasetDetails


class DatasetDataArray:
    def __init__(
        self,
        dataset_details: DatasetDetails,
        variable: str | None = None,
        crs: str = "EPSG:4326",
    ) -> None:
        self.variable = variable if variable else None
        self.crs = crs
        self.dataset_details = dataset_details
        self.file_type = self.determine_file_type()
        self.ds = self.open_dataset()

    def determine_file_type(self) -> str:
        """
        Determines the file type based on the URL extension.

        Parameters:

        Returns:
        str: The type of the file ('GeoTIFF', 'JSON', 'NetCDF', or 'Unknown').
        """
        url = self.dataset_details.url
        if url.endswith(".tif") or url.endswith(".tiff"):
            return "GeoTIFF"
        elif url.endswith(".json"):
            return "JSON"
        elif url.endswith(".nc"):
            return "NetCDF"
        else:
            return "Unknown"

    def open_dataset(self) -> xr.Dataset:
        """
        Opens a dataset from a URL.

        Parameters:

        Returns:
        xr.Dataset: Dataset opened from URL.
        """
        logger.info("Opening dataset from URL")
        url = self.dataset_details.url
        try:
            match self.file_type:
                case "JSON":
                    logger.info("Opening JSON file")
                    ds = xr.open_dataset(url, decode_coords="all", engine="kerchunk")
                    if self.variable:
                        ds = ds[self.variable]
                        ds = ds.squeeze()
                case "NetCDF":
                    logger.info("Opening NetCDF file")
                    ds = xr.open_dataset(url, decode_coords="all")
                    if self.variable:
                        ds = ds[self.variable]
                        ds = ds.squeeze()
                case "GeoTIFF":
                    logger.info("Opening GeoTIFF file")
                    ds = rxr.open_rasterio(url, mask_and_scale=True)
                case _:
                    raise ValueError(f"Unsupported file type: {self.file_type}")
            ds.attrs["file_path"] = url
            if self.crs:
                ds.rio.write_crs(self.crs, inplace=True)
            else:
                if not ds.rio.crs:
                    logger.info("CRS not found in dataset. Writing default CRS.")
                    ds.rio.write_crs("EPSG:4326", inplace=True)
            return ds
        except Exception as e:
            logger.error(f"Failed to open dataset from URL: {url}. Error: {e}")
            raise e
