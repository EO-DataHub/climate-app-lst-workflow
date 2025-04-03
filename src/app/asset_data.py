import json
import tempfile
from pathlib import Path

import boto3
import geopandas as gpd
import numpy as np
import pandas as pd
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
        self.json_data, self.gdf = self.download()
        self.geometry_type = self.get_geometry_types()
        self.data, self.no_of_assets = self.get_assets_and_count()
        self.crs = self.gdf.crs if self.gdf.crs else "EPSG:4326"

    def get_assets_and_count(self):
        if self.geometry_type == "Point":
            asset_data = self.point_to_xr_dataset()
            no_of_assets = len(asset_data.x)
        else:
            asset_data = self.gdf
            no_of_assets = len(asset_data)
        return asset_data, no_of_assets

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

        Returns:
            dict: The JSON content loaded from the downloaded file.
        """
        file_path = self._download_file()
        return self._process_file(file_path)

    def _download_file(self) -> Path:
        """
        Downloads the file from the source URL or S3 bucket.

        Returns:
            Path: The path to the downloaded file.
        """
        if self.source.startswith(("https://", "http://")):
            return self._download_from_http()
        elif self.source.startswith("s3://"):
            return self._download_from_s3()
        else:
            return Path(self.source)

    def _download_from_http(self) -> Path:
        """
        Downloads a file from an HTTP/HTTPS URL.

        Returns:
            Path: The path to the downloaded file.
        """
        logger.info(f"Downloading {self.source} using HTTP...")
        response = requests.get(self.source)
        response.raise_for_status()  # Raise an error for HTTP issues
        file_extension = Path(self.source).suffix
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_extension, delete=False
        ) as temp_file:
            logger.info("Writing downloaded file to temporary location")
            temp_file.write(response.text)
            temp_file.close()
        return Path(temp_file.name)

    def _download_from_s3(self) -> Path:
        """
        Downloads a file from an S3 bucket.

        Returns:
            Path: The path to the downloaded file.
        """
        s3 = boto3.client("s3")
        bucket_name, key = extract_bucket_and_key_from_s3_url(self.source)
        logger.info(f"Downloading key: {key} from bucket: {bucket_name}...")
        local_file = Path(key).name
        s3.download_file(bucket_name, key, local_file)
        return Path(local_file)

    def _process_file(self, file_path: Path) -> tuple:
        """
        Processes the downloaded file based on its extension.

        Args:
            file_path (Path): The path to the downloaded file.

        Returns:
            tuple: A tuple containing the JSON data and GeoDataFrame.
        """
        if file_path.suffix in [".geojson", ".json"]:
            logger.info(f"Processing GeoJSON/JSON file: {file_path}")
            data = self.load_json_from_file(file_path.as_posix())
            gdf = gpd.read_file(file_path.as_posix())
        elif file_path.suffix == ".csv":
            with open(file_path, encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("{") and first_line.endswith("}"):
                    logger.info(
                        "Detected JSON-like content in CSV file. Parsing as JSON."
                    )
                    data = self.load_json_from_file(file_path.as_posix())
                    gdf = gpd.GeoDataFrame.from_features(data["features"])
                else:
                    logger.info(f"Processing CSV file: {file_path}")
                    gdf = self.csv_to_geodataframe(file_path.as_posix())
                    data = (
                        gdf.__geo_interface__
                    )  # Convert GeoDataFrame to GeoJSON-like dict
        else:
            logger.error(f"Unsupported file type: {file_path.suffix}")
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        return data, gdf

    def csv_to_geodataframe(self, file_path: str) -> gpd.GeoDataFrame:
        """
        Converts a CSV file with latitude and longitude columns to a GeoDataFrame.

        Args:
            file_path (str): The path to the CSV file.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame with geometry created
            from latitude and longitude.
        """
        logger.info(f"Converting CSV file {file_path} to GeoDataFrame")
        try:
            df = pd.read_csv(file_path)
            if "latitude" not in df.columns or "longitude" not in df.columns:
                raise ValueError(
                    "CSV file must contain 'latitude' and 'longitude' columns."
                )
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326",
            )
            return gdf
        except Exception as e:
            logger.error(f"Failed to convert CSV to GeoDataFrame: {e}")
            raise RuntimeError(f"Error processing CSV file {file_path}") from e

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
            features = self.json_data["features"]
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
        return gpd.GeoDataFrame.from_features(self.json_data["features"])

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
        for feature in self.json_data.get("features", []):
            geometry = feature.get("geometry", {})
            geometry_type = geometry.get("type")
            if geometry_type:
                geometry_types.append(geometry_type)
        return geometry_types
