import json
import os
import tempfile

import boto3
import geopandas as gpd
import numpy as np
import requests
import xarray as xr

from app.get_values_logger import logger


def extract_bucket_and_key_from_s3_url(s3_path):
    """
    Extracts the bucket name and key from an S3 URL.

    Args:
        s3_path (str): The S3 URL in the format 's3://bucket_name/key'.

    Returns:
        tuple: A tuple containing the bucket name (str) and the key (str).
    """
    path_parts = s3_path.replace("s3://", "").split("/")
    bucket = path_parts.pop(0)
    key = "/".join(path_parts)
    return bucket, key


class AssetData:
    def __init__(self, source: str):
        self.source = source
        self.data, self.gdf = self.download()
        self.geometry_type = self.get_geometry_types()

    def load_json_from_file(self, file_path: str) -> dict:
        """
        Loads JSON content from a file and returns it as a dictionary.

        Args:
            file_path (str): The path to the JSON file.

        Returns:
            dict: The JSON content as a dictionary.

        Raises:
            RuntimeError: If the file is empty or contains invalid JSON.
        """
        with open(file_path, encoding="utf-8") as file:
            content = file.read()
            if not content.strip():
                raise RuntimeError(f"The JSON file {file_path} is empty.")
            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Failed to decode the content of the JSON file {file_path}"
                ) from exc

    def download(self) -> dict:
        """
        Download a spatial file from an HTTP URL or an
        S3 bucket and load its JSON content.

        Args:

        Returns:
            dict: The JSON content loaded from the downloaded file.
        """
        base_name = os.path.basename(self.source)
        if self.source.startswith("https://") or self.source.startswith("http://"):
            logger.info(f"Downloading {self.source} using http...")
            response = requests.get(self.source)
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                try:
                    logger.info("Downloading file")
                    temp_file.write(response.text)
                    temp_file.close()
                except RuntimeError as e:
                    logger.error(e)
            data = self.load_json_from_file(temp_file.name)
            gdf = gpd.read_file(temp_file.name)
        elif self.source.startswith("s3://"):
            s3 = boto3.client("s3")
            bucket_name, key = extract_bucket_and_key_from_s3_url(self.source)
            logger.info(f"Downloading key: {key} from bucket: {bucket_name}...")
            local_file = os.path.basename(key)
            s3.download_file(bucket_name, key, local_file)
            data = self.load_json_from_file(local_file)
            gdf = gpd.read_file(local_file)
        else:
            base_name = os.path.basename(self.source)
            bucket_arn = "workspaces-eodhp-test"
            logger.info(f"Downloading {self.source} from {bucket_arn}...")
            s3.download_file(bucket_arn, self.source, base_name)
            data = self.load_json_from_file(base_name)
            gdf = gpd.read_file(base_name)

        return data, gdf

    def point_to_xr_dataset(self) -> xr.Dataset:
        """
        Converts points data to an xarray Dataset.

        Returns:
        xr.Dataset: Dataset with points as coordinates.

        Raises:
        ValueError: If the input data is missing or invalid.
        """
        logger.info("Converting points to xarray Dataset")
        try:
            features = self.data["features"]
            latitudes = np.array(
                [feature["geometry"]["coordinates"][1] for feature in features]
            )
            longitudes = np.array(
                [feature["geometry"]["coordinates"][0] for feature in features]
            )
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Invalid points data: {e}")
            raise ValueError("Invalid points data") from e

        dataset = xr.Dataset(
            {"x": (["points"], longitudes), "y": (["points"], latitudes)},
        )
        return dataset

    def polygon_to_gdf(self) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame.from_features(self.data["features"])

    def get_geometry_types(self) -> list:
        geom_type_list = self._list_geometry_types()
        if not geom_type_list:
            raise ValueError("No geometry types found")
        first_type = geom_type_list[0]
        for geom_type in geom_type_list:
            if geom_type != first_type:
                return "Mixed"
        return first_type

    def _list_geometry_types(self) -> list:
        geometry_types = []
        for feature in self.data.get("features", []):
            geometry = feature.get("geometry", {})
            geometry_type = geometry.get("type")
            if geometry_type:
                geometry_types.append(geometry_type)
        return geometry_types
