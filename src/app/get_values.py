"""
Functions to get values from a cog file
"""

import geopandas as gpd
import rasterio as rio
import xarray as xr
from pyproj import Transformer
from rasterio.session import AWSSession
from shapely.geometry import mapping

from app.asset_data import AssetData
from app.create_dataarray import DatasetDataArray
from app.get_values_logger import logger
from app.stac_parsing import DatasetDetails

aws_session = AWSSession(aws_unsigned=True)


def get_values_points(datasource_array: xr.DataArray, points: xr.Dataset) -> list:
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
    with rio.Env(aws_session):
        ds_crs = datasource_array.rio.crs
        if ds_crs != "EPSG:4326":
            logger.info("Transforming points to dataset CRS")
            transformer = Transformer.from_crs("EPSG:4326", ds_crs, always_xy=True)
            x_t, y_t = transformer.transform(points.x, points.y)  # pylint: disable=E0633
            points = xr.Dataset(
                {"x": (["points"], x_t), "y": (["points"], y_t)},
            )
        index_keys = list(datasource_array._indexes.keys())
        logger.info(f"Index keys: {index_keys}")
        if "lat" in index_keys and "lon" in index_keys:
            logger.info("Using lat and lon as indexes")
            values = (
                datasource_array.sel(lat=points.y, lon=points.x, method="nearest")
                .values[0]
                .tolist()
            )
        elif "y" in index_keys and "x" in index_keys:
            logger.info("Using y and x as indexes")
            values = (
                datasource_array.sel(x=points.x, y=points.y, method="nearest")
                .values[0]
                .tolist()
            )
        else:
            logger.error("Unsupported index keys")
        # replace nan with None
        values = [None if str(v) == "nan" else v for v in values]
        return values


def get_values_polygons(
    datasource_array: DatasetDataArray, polygons_gdf: gpd.GeoDataFrame
) -> list:
    """
    Extracts values from a raster dataset for specified polygons.

    Parameters:
    - raster_dataset (DatasetDataArray): The raster dataset to extract values from.
    - polygons_gdf (gpd.GeoDataFrame): GeoDataFrame containing polygons of interest.

    Returns:
    list: A list of mean values for each polygon.
    """
    ds_crs = datasource_array.rio.crs
    if ds_crs and ds_crs != "EPSG:4326":
        logger.info("Transforming polygons to dataset CRS")
        polygons_gdf = polygons_gdf.to_crs(ds_crs)
    datasource_array = datasource_array.squeeze()
    results = []
    means = []
    for _, row in polygons_gdf.iterrows():
        minx, miny, maxx, maxy = row.geometry.bounds
        bbox_rds = datasource_array.rio.clip_box(
            minx=minx, miny=miny, maxx=maxx, maxy=maxy
        )
        clipped = bbox_rds.rio.clip([mapping(row.geometry)], polygons_gdf.crs)
        stats_dict = {
            "mean": clipped.mean().item(),
            "max": clipped.max().item(),
            "min": clipped.min().item(),
        }
        results.append(stats_dict)
        means.append(clipped.mean().item())
    means = [None if str(v) == "nan" else v for v in means]
    return means


def get_values_lines(
    datasource_array: DatasetDataArray, lines_gdf: gpd.GeoDataFrame
) -> list:
    """
    Extracts values from a raster dataset for specified line strings.

    Parameters:
    - raster_dataset (DatasetDataArray): The raster dataset to extract values from.
    - lines_gdf (gpd.GeoDataFrame): GeoDataFrame containing line strings of interest.

    Returns:
    list: A list of mean values for each line string.
    """
    ds_crs = datasource_array.rio.crs
    if ds_crs and ds_crs != "EPSG:4326":
        logger.info("Transforming lines to dataset CRS")
        lines_gdf = lines_gdf.to_crs(ds_crs)
    datasource_array = datasource_array.squeeze()
    results = []
    means = []
    for _, row in lines_gdf.iterrows():
        minx, miny, maxx, maxy = row.geometry.bounds
        bbox_rds = datasource_array.rio.clip_box(
            minx=minx, miny=miny, maxx=maxx, maxy=maxy
        )
        clipped = bbox_rds.rio.clip([mapping(row.geometry)], lines_gdf.crs)
        stats_dict = {
            "mean": clipped.mean().item(),
            "max": clipped.max().item(),
            "min": clipped.min().item(),
        }
        results.append(stats_dict)
        means.append(clipped.mean().item())
    means = [None if str(v) == "nan" else v for v in means]
    return means


def get_values_for_multiple_datasets(
    dataset_details_list: list[DatasetDetails],
    assets: AssetData,
    extra_args: str = None,
) -> list:
    """
    Retrieve values for multiple STAC assets.

    Parameters:
    dataset_details_list (list[DatasetDetails]): List of dataset details to process.
    points (xr.Dataset): Dataset containing the points to extract values for.
    extra_args (str, optional): Additional arguments for asset processing.

    Returns:
    list: A list of dictionaries containing asset details and their
    corresponding values.
    """
    logger.debug("Getting values from multiple files")
    return_values = []

    geometry_type_to_function = {
        "Point": get_values_points,
        "Polygon": get_values_polygons,
        "LineString": get_values_lines,
    }
    geometry_type = assets.geometry_type

    if geometry_type in geometry_type_to_function:
        if geometry_type == "Point":
            assets = assets.point_to_xr_dataset()
        else:
            assets = assets.gdf

        for dataset_details in dataset_details_list:
            logger.info("Getting values from multiple datasets")
            dataset_array = DatasetDataArray(
                dataset_details=dataset_details, extra_args=extra_args
            ).ds
            result = geometry_type_to_function[geometry_type](
                datasource_array=dataset_array,
                points=assets if geometry_type == "Point" else assets,
            )
            return_values.append({"asset_details": dataset_details, "values": result})

    return return_values
