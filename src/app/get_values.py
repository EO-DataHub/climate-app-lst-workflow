import ast
import operator

import numpy as np
import rasterio as rio
import xarray as xr
from aiohttp.client_exceptions import ClientResponseError
from rasterio.session import AWSSession
from rioxarray.exceptions import NoDataInBounds
from shapely.geometry import mapping

from app.asset_data import AssetData
from app.create_dataarray import DatasetDataArray
from app.get_values_logger import logger
from app.stac_parsing import DatasetDetails

aws_session = AWSSession(aws_unsigned=True)


class DatasetsValueExtractor:
    def __init__(
        self,
        dataset_details_list: list[DatasetDetails],
        assets: AssetData,
        expression: str,
    ):
        self.dataset_details_list = dataset_details_list
        self.assets = assets
        self.geometry_type_to_function = {
            "Point": ValueExtractor.get_values_points,
            "Polygon": ValueExtractor.get_values_polygons,
            "LineString": ValueExtractor.get_values_lines,
        }
        self.expression = expression

    def get_values_for_multiple_variables(self, variables: list[str]) -> dict:
        for variable in variables:
            self.get_values_for_datasets(variable, output_name_suffix=f"_{variable}")

    def get_min_max_values(self) -> dict:
        for dataset_details in self.dataset_details_list:
            self.get_min_max_values_for_dataset(dataset_details=dataset_details)

    def get_min_max_values_for_dataset(self, dataset_details: DatasetDetails) -> None:
        lst_value_extractor = ValueExtractor(
            dataset_details=dataset_details,
            assets=self.assets,
            variable="lst",
            expression="x-273.15",
        )
        lst_uncertainty_value_extractor = ValueExtractor(
            dataset_details=dataset_details,
            assets=self.assets,
            variable="lst_uncertainty",
        )
        lst_values = lst_value_extractor.get_values()
        lst_uncertainty_values = lst_uncertainty_value_extractor.get_values()
        min_values = [
            (a - b) if a is not None and b is not None else None
            for a, b in zip(lst_values, lst_uncertainty_values, strict=True)
        ]

        max_values = [
            (a + b) if a is not None and b is not None else None
            for a, b in zip(lst_values, lst_uncertainty_values, strict=True)
        ]
        self._update_asset_properties_caller(
            dataset_details=dataset_details,
            results=min_values,
            output_name_suffix="_minus_uncertainty",
        )
        self._update_asset_properties_caller(
            dataset_details=dataset_details,
            results=max_values,
            output_name_suffix="_plus_uncertainty",
        )

    def get_values_for_datasets(
        self, variable: str, output_name_suffix: str = ""
    ) -> dict:
        for dataset_details in self.dataset_details_list:
            self.get_values_for_dataset(
                dataset_details=dataset_details,
                variable=variable,
                output_name_suffix=output_name_suffix,
            )

    def get_values_for_dataset(
        self,
        dataset_details: DatasetDetails,
        variable: str,
        output_name_suffix: str = "",
    ) -> None:
        value_extractor = ValueExtractor(
            dataset_details=dataset_details,
            assets=self.assets,
            variable=variable,
            expression=self.expression,
        )
        results = value_extractor.get_values()
        self._update_asset_properties_caller(
            results=results,
            dataset_details=dataset_details,
            output_name_suffix=output_name_suffix,
        )

    def _update_asset_properties_caller(
        self, results: list, dataset_details: DatasetDetails, output_name_suffix: str
    ) -> None:
        if self.assets.geometry_type != "Point":
            output_name_suffix = f"{output_name_suffix}_average"
        for index, result in enumerate(results):
            self._update_asset_properties(
                index=index,
                dataset_details=dataset_details,
                result=result,
                output_name_suffix=output_name_suffix,
            )

    def _update_asset_properties(
        self,
        index: int,
        dataset_details: DatasetDetails,
        result: any,
        output_name_suffix: str = "",
    ) -> None:
        output_name = dataset_details.output_name + output_name_suffix
        properties = self.assets.json_data["features"][index]["properties"]
        returned_values = properties.setdefault("returned_values", {})
        dataset_values = returned_values.setdefault(output_name, {})
        dataset_values.update(
            {
                "value": result,
                "datetime": dataset_details.datetime.isoformat(),
                "unit": dataset_details.unit,
                "file_name": dataset_details.source_file_name,
                "key": output_name,
            }
        )

    def add_summary_statistics(self):
        for feature in self.assets.json_data["features"]:
            returned_values = feature["properties"]["returned_values"]
            values = [
                v["value"] for v in returned_values.values() if v["value"] is not None
            ]

            if values:
                # Compute statistics
                stats = {
                    "MINIMUM": float(min(values)),
                    "MAXIMUM": float(max(values)),
                    "MEAN": float(np.mean(values)),
                    "STANDARD_DEVIATION": float(np.std(values)),
                }
            else:
                stats = {
                    "MINIMUM": None,
                    "MAXIMUM": None,
                    "MEAN": None,
                    "STANDARD_DEVIATION": None,
                }

            # Add statistics to returned_values
            for stat_name, stat_value in stats.items():
                returned_values[stat_name] = {
                    "value": stat_value,
                    "type": "statistic",
                    "key": stat_name,
                }


class ValueExtractor:
    def __init__(
        self,
        dataset_details: DatasetDetails,
        assets: AssetData,
        variable: str = None,
        expression: str = None,
    ):
        self.dataset_details = dataset_details
        self.assets = assets
        self.geometry_type = assets.geometry_type
        self.variable = variable
        self.dataset = self.load_dataset()
        self.geometry_type_to_function = {
            "Point": "get_values_points",
            "Polygon": "get_values_polygons",
            "LineString": "get_values_lines",
        }
        self.expression = expression

    def get_values_points(self) -> list:
        logger.info("Getting values for points")
        try:
            with rio.Env(aws_session):
                index_keys = list(self.dataset._indexes.keys())
                logger.info(f"Index keys: {index_keys}")
                if "lat" in index_keys and "lon" in index_keys:
                    logger.info("Using lat and lon as indexes")
                    values = self.dataset.sel(
                        lat=self.assets.data.y,
                        lon=self.assets.data.x,
                        method="nearest",
                    ).values.tolist()
                elif "y" in index_keys and "x" in index_keys:
                    logger.info("Using y and x as indexes")
                    values = self.dataset.sel(
                        x=self.assets.data.x,
                        y=self.assets.data.y,
                        method="nearest",
                    ).values.tolist()
                else:
                    logger.error("Unsupported index keys")
                    values = [None] * len(self.assets.x)
        except Exception as e:
            logger.error(f"Error extracting values from points: {e}")
            values = [None] * len(self.assets.data.x)
        values = [None if str(v) == "nan" else v for v in values]
        return values

    def get_values_polygons(self) -> list:
        logger.info("Getting values for polygons")
        results = []
        for _, row in self.assets.data.iterrows():
            minx, miny, maxx, maxy = row.geometry.bounds
            try:
                bbox_rds = self.dataset.rio.clip_box(
                    minx=minx,
                    miny=miny,
                    maxx=maxx,
                    maxy=maxy,
                    allow_one_dimensional_raster=True,
                )
                clipped = bbox_rds.rio.clip([mapping(row.geometry)], self.assets.crs)
                results.append(clipped.mean().item())
            except ClientResponseError:
                logger.error("ClientResponseError")
                results.append("DataError")
            except NoDataInBounds:
                logger.error("NoDataInBounds")
                results.append(None)
            except Exception as e:
                logger.error(f"Error extracting values from polygon: {e}")
                results.append(None)
        return [None if str(v) == "nan" else v for v in results]

    def get_values_lines(self) -> list:
        logger.info("Getting values for lines")
        results = []
        for _, row in self.assets.data.iterrows():
            minx, miny, maxx, maxy = row.geometry.bounds
            try:
                bbox_rds = self.dataset.rio.clip_box(
                    minx=minx,
                    miny=miny,
                    maxx=maxx,
                    maxy=maxy,
                    allow_one_dimensional_raster=True,
                )
                clipped = bbox_rds.rio.clip([mapping(row.geometry)], self.assets.crs)
                results.append(clipped.mean().item())
            except NoDataInBounds:
                results.append(None)
            except ClientResponseError:
                results.append("DataError")
        results = [None if str(v) == "nan" else v for v in results]
        return results

    def load_dataset(self) -> xr.Dataset:
        try:
            dataset = DatasetDataArray(
                dataset_details=self.dataset_details, variable=self.variable
            ).ds
            return dataset
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            dataset = None
        return dataset

    def get_values(self) -> list:
        method_name = self.geometry_type_to_function[self.geometry_type]
        method = getattr(self, method_name)
        result = method()
        if self.expression:
            result = [
                eval_expr(self.expression, value) if value is not None else None
                for value in result
            ]
        return result


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
