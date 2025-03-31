import datetime as dt
import json
import mimetypes
import os
import time
from pathlib import Path

import geopandas as gpd

from app.get_values_logger import logger


class ResponseStatus:
    SUCCESS = "success"
    ERROR = "error"


class WorkflowResponse:
    def __init__(
        self, status: ResponseStatus, return_values: dict = None, error_msg=None
    ):
        self.status = status
        self.error_msg = error_msg
        if self.status == ResponseStatus.ERROR:
            self.process_response = {}
            self.out_file = "./error.txt"
            self.create_error_response()
        else:
            self.process_response = return_values
            self.out_file = "./data.csv"
            self.to_csv()

        self.stac_item = self.createStacItem()
        self.stac_catalog_root = self.createStacCatalogRoot()
        self.write_stac_files()

    def createStacItem(self) -> dict:
        """
        Create a STAC (SpatioTemporal Asset Catalog)
        item from the given output file name

        Args:

        Returns:
            data (dict): The STAC item data.
        """
        stem = Path(self.out_file).stem
        now = time.time_ns() / 1_000_000_000
        dateNow = dt.datetime.fromtimestamp(now)
        dateNow = dateNow.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        size = os.path.getsize(f"{self.out_file}")
        mime = mimetypes.guess_type(f"{self.out_file}")[0]
        data = {
            "stac_version": "1.0.0",
            "id": f"{stem}-{now}",
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[-180, -90], [-180, 90], [180, 90], [180, -90], [-180, -90]]
                ],
            },
            "properties": {
                "created": f"{dateNow}",
                "datetime": f"{dateNow}",
                "updated": f"{dateNow}",
            },
            "bbox": [-180, -90, 180, 90],
            "assets": {
                f"{stem}": {
                    "type": f"{mime}",
                    "roles": ["data"],
                    "href": f"{self.out_file}",
                    "file:size": size,
                }
            },
            "links": [
                {"type": "application/json", "rel": "parent", "href": "catalog.json"},
                {"type": "application/geo+json", "rel": "self", "href": f"{stem}.json"},
                {"type": "application/json", "rel": "root", "href": "catalog.json"},
            ],
        }
        return data

    def createStacCatalogRoot(self) -> dict:
        """
        Create the root STAC (SpatioTemporal Asset Catalog) catalog
        from the given output file name.

        Args:

        Returns:
            data (dict): The root STAC catalog data.
        """
        stem = Path(self.out_file).stem
        catalog = {
            "stac_version": "1.0.0",
            "id": "",
            "type": "Catalog",
            "title": "LST Results",
            "description": "Root catalog",
            "links": [
                {"type": "application/geo+json", "rel": "item", "href": f"{stem}.json"},
                {"type": "application/json", "rel": "self", "href": "catalog.json"},
            ],
        }
        catalog["data"] = self.process_response
        return catalog

    def write_stac_files(self):
        """
        Write the STAC item and catalog root to their respective JSON files.
        """
        try:
            json_to_file(self.stac_item, f"{Path(self.out_file).stem}.json")
            json_to_file(self.stac_catalog_root, "./catalog.json")
        except Exception as e:
            logger.error(f"Error writing STAC files: {e}")

    def to_csv(self) -> None:
        """
        Converts a JSON response to a CSV file with columns for every datetime,
        a row for every id, and values of 'value'.

        Parameters:
        process_response (dict): The input JSON data.
        out_csv (str): The output CSV file path.
        """
        data = self.process_response.get("features", [])
        gdf = gpd.GeoDataFrame.from_features(data)

        def extract_datetime_values(row):
            for key, val in row["returned_values"].items():
                row[key] = val["value"] if val.get("value") else "none"
            return row

        gdf = gdf.apply(extract_datetime_values, axis=1)
        gdf.drop(columns=["returned_values", "geometry"], inplace=True)
        csv_filename = "./data.csv"
        gdf.to_csv(csv_filename, index=False)

    def create_error_response(self) -> dict:
        """
        Create an error response with the given error message.

        Args:
        error_msg (str): The error message.

        Returns:
        dict: The error response.
        """
        error_return = {
            "statusCode": 500,
            "body": {"error": self.error_msg},
        }
        json_to_file(error_return, self.out_file)


def json_to_file(json_data: dict, file_path: str) -> None:
    """
    Writes JSON data to a file.

    Args:
        json_data (dict): The JSON data to write.
        file_path (str): The path to the file where the JSON data will be written.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        try:
            json.dump(json_data, f)
        except Exception as e:
            logger.error(f"Error writing data to file, {file_path}: {e}")
