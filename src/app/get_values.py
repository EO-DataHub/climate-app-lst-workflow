"""
Functions to get values from a cog file
"""

import ast
import operator

import geopandas as gpd
import rasterio as rio
import xarray as xr
from aiohttp.client_exceptions import ClientResponseError
from pyproj import Transformer
from rasterio.session import AWSSession
from rioxarray.exceptions import NoDataInBounds
from shapely.geometry import mapping

from app.asset_data import AssetData
from app.create_dataarray import DatasetDataArray
from app.get_values_logger import logger
from app.stac_parsing import DatasetDetails

aws_session = AWSSession(aws_unsigned=True)


def get_values_points(datasource_array: xr.DataArray, assets: xr.Dataset) -> list:
    """
    Extracts values from a COG file for specified points.

    Parameters:
    - ds (xr.DataArray): Data array to extract values from.
    - assets (xr.Dataset): Dataset containing points of interest.

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
            x_t, y_t = transformer.transform(assets.x, assets.y)  # pylint: disable=E0633
            assets = xr.Dataset(
                {"x": (["points"], x_t), "y": (["points"], y_t)},
            )
        index_keys = list(datasource_array._indexes.keys())
        logger.info(f"Index keys: {index_keys}")
        if "lat" in index_keys and "lon" in index_keys:
            logger.info("Using lat and lon as indexes")
            try:
                values = (
                    datasource_array.sel(lat=assets.y, lon=assets.x, method="nearest")
                    .values[0]
                    .tolist()
                )
            except Exception as e:
                logger.error(f"Error extracting values from points: {e}")
                values = [None] * len(assets.x)
        elif "y" in index_keys and "x" in index_keys:
            logger.info("Using y and x as indexes")
            try:
                values = (
                    datasource_array.sel(x=assets.x, y=assets.y, method="nearest")
                    .values[0]
                    .tolist()
                )
            except Exception as e:
                logger.error(f"Error extracting values from points: {e}")
                values = [None] * len(assets.x)
        else:
            logger.error("Unsupported index keys")
        # replace nan with None
        values = [None if str(v) == "nan" else v for v in values]
        return values


def get_values_polygons(
    datasource_array: DatasetDataArray, assets: gpd.GeoDataFrame
) -> list:
    """
    Extracts values from a raster dataset for specified polygons.

    Parameters:
    - raster_dataset (DatasetDataArray): The raster dataset to extract values from.
    - assets (gpd.GeoDataFrame): GeoDataFrame containing polygons of interest.

    Returns:
    list: A list of mean values for each polygon.
    """
    ds_crs = datasource_array.rio.crs
    if ds_crs and ds_crs != "EPSG:4326":
        logger.info("Transforming polygons to dataset CRS")
        assets = assets.to_crs(ds_crs)
    datasource_array = datasource_array.squeeze()
    results = []
    for _, row in assets.iterrows():
        minx, miny, maxx, maxy = row.geometry.bounds
        try:
            bbox_rds = datasource_array.rio.clip_box(
                minx=minx,
                miny=miny,
                maxx=maxx,
                maxy=maxy,
                allow_one_dimensional_raster=True,
            )
            clipped = bbox_rds.rio.clip([mapping(row.geometry)], assets.crs)
            results.append(clipped.mean().item())
        except ClientResponseError:
            results.append("DataError")
        except NoDataInBounds:
            results.append(None)
        except Exception as e:
            logger.error(f"Error extracting values from polygon: {e}")
            results.append(None)
    results = [None if str(v) == "nan" else v for v in results]
    return results


def get_values_lines(
    datasource_array: DatasetDataArray, assets: gpd.GeoDataFrame
) -> list:
    """
    Extracts values from a raster dataset for specified line strings.

    Parameters:
    - raster_dataset (DatasetDataArray): The raster dataset to extract values from.
    - assets (gpd.GeoDataFrame): GeoDataFrame containing line strings of interest.

    Returns:
    list: A list of mean values for each line string.
    """
    ds_crs = datasource_array.rio.crs
    if ds_crs and ds_crs != "EPSG:4326":
        logger.info("Transforming lines to dataset CRS")
        assets = assets.to_crs(ds_crs)
    datasource_array = datasource_array.squeeze()
    results = []
    for _, row in assets.iterrows():
        minx, miny, maxx, maxy = row.geometry.bounds
        try:
            bbox_rds = datasource_array.rio.clip_box(
                minx=minx, miny=miny, maxx=maxx, maxy=maxy
            )
            clipped = bbox_rds.rio.clip([mapping(row.geometry)], assets.crs)
            results.append(clipped.mean().item())
        except NoDataInBounds:
            results.append(None)
        except ClientResponseError:
            results.append("DataError")
    results = [None if str(v) == "nan" else v for v in results]
    return results


def eval_expr(expr, value):
    """
    Safely evaluate a mathematical expression with a given value.
    """
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.BitXor: operator.xor,
        ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):  # <number>
            return node.value
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return operators[type(node.op)](_eval(node.operand))
        elif isinstance(node, ast.Name):
            if node.id == "x":
                return value
            else:
                raise ValueError(f"Unsupported variable: {node.id}")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "round"
        ):
            args = [_eval(arg) for arg in node.args]
            return round(*args)
        else:
            raise TypeError(node)

    node = ast.parse(expr, mode="eval").body
    return _eval(node)


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
            no_of_assets = len(assets.x)
        else:
            assets = assets.gdf
            no_of_assets = len(assets)

        for dataset_details in dataset_details_list:
            logger.info("Getting values from multiple datasets")
            try:
                dataset_array = DatasetDataArray(
                    dataset_details=dataset_details, extra_args=extra_args
                ).ds
            except Exception as e:
                logger.error(f"Error getting values for dataset: {e}")
                values = [None] * no_of_assets
                return_values.append(
                    {"asset_details": dataset_details, "values": values}
                )
                continue
            result = geometry_type_to_function[geometry_type](
                datasource_array=dataset_array,
                assets=assets,
            )
            if extra_args and "expression" in extra_args:
                expression = extra_args.get("expression", None)
                result = [
                    eval_expr(expression, value) if value is not None else None
                    for value in result
                ]

            return_values.append({"asset_details": dataset_details, "values": result})

    return return_values
