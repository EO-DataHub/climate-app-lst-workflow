#!/usr/bin/env python3
"""
Main starting point for the workflow.
"""

import argparse
import json
import os
import sys
import tempfile

import boto3
import requests
from botocore import UNSIGNED
from botocore.client import Config
from get_values import get_values_from_multiple_cogs, merge_results_into_dict
from get_values_logger import logger
from load_points import points_to_xr_dataset
from stac_items import default_stac_items
from stac_parsing import get_cog_data


def get_data_values(stac_items: list[str], points_json: dict):
    """
    Fetches data values for given points from STAC items.

    This function retrieves Cloud Optimized GeoTIFF (COG) URLs
    from the provided STAC items, loads the COGs, and extracts
    data values at specified points. The results are merged into
    a dictionary structure and returned.

    Parameters:
    - stac_items (list[str]): List of STAC item URLs.
    - points_json (dict): JSON object containing points.

    Returns:
    dict: A dictionary with the merged results of data values
    for the provided points.
    """
    logger.info("Converting points to an xr dataset")
    points = points_to_xr_dataset(points_json)
    logger.info("Loading COGs")
    return_values = get_values_from_multiple_cogs(stac_urls=stac_items, points=points)
    logger.info("Merging results into dict")
    return_json = merge_results_into_dict(return_values, points_json)
    return return_json


def process_request(
    points_json: dict,
    stac_items: list[str],
    workflow: bool = False,
) -> dict:
    """
    Processes a request to get data values for points.

    Parameters:
    - points_json (dict): JSON containing points data.
    - stac_items (list[str]): List of STAC item IDs.

    Returns:
    dict: Response with status code and body.
    """
    if not all([points_json, stac_items]):
        return {"statusCode": 400, "body": json.dumps("Missing required parameters")}
    try:
        response = get_data_values(stac_items, points_json)
        if workflow:
            return response
        else:
            try:
                return {"statusCode": 200, "body": json.dumps(response)}
            except Exception as e:
                logger.error("Error when returning response: %s", e)
                return {"statusCode": 500, "body": json.dumps(str(e))}
    except Exception as e:
        logger.error("Error: %s", e)
        return {"statusCode": 500, "body": json.dumps(str(e))}


def parse_arguments():
    """
    Parses command-line arguments for the request.

    Returns:
        argparse.Namespace: An object that holds the parsed arguments as
        attributes.
    """
    logger.info("Parsing command-line arguments")
    parser = argparse.ArgumentParser(description="Make a request.")
    parser.add_argument("--json_file", type=str, help="GeoJSON string with points data")
    parser.add_argument("--stac_items", type=str, help="STAC item URLs", default=None)
    return parser.parse_args()


def get_catalog() -> dict:
    """
    Creates and returns a basic STAC catalog dictionary.

    This function generates a dictionary representing a SpatioTemporal Asset Catalog
    (STAC) catalog with predefined properties.

    Returns:
    - dict: A dictionary representing the STAC catalog with predefined properties.
    """
    logger.info("Creating STAC catalog")
    return {
        "stac_version": "1.0.0",
        "id": "asset-vulnerability-catalog",
        "type": "Catalog",
        "description": "OS-C physrisk asset vulnerability catalog",
        "links": [
            {"rel": "self", "href": "./catalog.json"},
            {"rel": "root", "href": "./catalog.json"},
        ],
    }


def load_json_from_file(file_path):
    """
    Loads JSON content from a file and returns it as a dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The JSON content as a dictionary.

    Raises:
        RuntimeError: If the file is empty or contains invalid JSON.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        if not content.strip():
            raise RuntimeError(f"The JSON file {file_path} is empty.")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Failed to decode the content of the JSON file {file_path}"
            ) from exc


def load_json_from_url(url):
    """
    Loads JSON content from a URL and returns it as a dictionary.

    Args:
        url (str): The URL to the JSON file.

    Returns:
        dict: The JSON content as a dictionary.

    Raises:
        RuntimeError: If the request fails or the content is invalid JSON.
    """
    url_response = requests.get(url, timeout=30)
    if url_response.status_code != 200:
        raise RuntimeError(
            f"Request to get the content of the input JSON {url} over HTTP failed: {url_response.text}"
        )
    content = url_response.content.decode("utf-8")
    if not content.strip():
        raise RuntimeError(f"The JSON content from {url} is empty.")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Failed to decode the content of the input JSON {url} over HTTP"
        ) from exc


def load_json_from_s3(s3_path):
    """
    Loads JSON content from an S3 path and returns it as a dictionary.

    Args:
        s3_path (str): The S3 path to the JSON file.

    Returns:
        dict: The JSON content as a dictionary.

    Raises:
        RuntimeError: If the file is empty or contains invalid JSON.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False).name
    s3 = boto3.client("s3")

    # Create an S3 client with anonymous access
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    logger.debug("Using the unsigned S3 client")
    print("Downloading file from S3...")
    s3_bucket = s3_path.split("/")[2]
    s3_bucketkey = "/".join(s3_path.split("/")[3:])
    s3.download_file(s3_bucket, s3_bucketkey, temp_file)
    return load_json_from_file(temp_file)


if __name__ == "__main__":
    args = parse_arguments()
    try:
        if "http" in args.json_file:
            logger.info("Getting the content of the input JSON over HTTP")
            arg_points_json = load_json_from_url(args.json_file)
        elif "s3" in args.json_file:
            logger.info("Getting the content of the input JSON from S3")
            arg_points_json = load_json_from_s3(args.json_file)
        else:
            logger.info("Reading the input JSON file")
            arg_points_json = load_json_from_file(args.json_file)
    except RuntimeError as e:
        logger.error(e)
        sys.exit(1)
    if args.stac_items is None:
        arg_stac_items = default_stac_items
    else:
        arg_stac_items = json.loads(args.stac_items)
    process_response = process_request(
        points_json=arg_points_json,
        stac_items=arg_stac_items,
        workflow=True,
    )
    # Make a stac catalog.json file to satitsfy the process runner
    os.makedirs("asset_output", exist_ok=True)
    with open("./asset_output/catalog.json", "w", encoding="utf-8") as f:
        catalog = get_catalog()
        catalog["data"] = process_response
        try:
            json.dump(catalog, f)
        except Exception as e:
            print("Error writing catalog.json file: %s", e)
