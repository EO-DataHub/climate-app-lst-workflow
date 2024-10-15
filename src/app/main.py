#!/usr/bin/env python3
"""
Main starting point for the workflow.
"""

import argparse
import json
import os

import pandas as pd
from get_values import get_values_from_multiple_cogs, merge_results_into_dict
from get_values_logger import logger
from load_points import points_to_xr_dataset
from stac_items import default_stac_items


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
    parser.add_argument(
        "--json_string", type=str, help="GeoJSON string with points data"
    )
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


def response_to_csv(in_json: dict, out_csv: str) -> None:
    """
    Converts a JSON response to a CSV file with columns for every datetime,
    a row for every id, and values of 'value'.

    Parameters:
    in_json (dict): The input JSON data.
    out_csv (str): The output CSV file path.
    """
    try:
        data = []
        for feature in in_json.get("features", []):
            feature_id = feature["properties"]["id"]
            for dt, values in feature["properties"]["returned_values"].items():
                data.append(
                    {"id": feature_id, "datetime": dt, "value": values.get("value")}
                )

        df = pd.DataFrame(data)
        pivot_df = df.pivot_table(index="id", columns="datetime", values="value")
        pivot_df.reset_index(inplace=True)
        pivot_df.to_csv(out_csv, index=False)
        logger.info("CSV file successfully created at %s", out_csv)
    except Exception as e:
        logger.error("An error occurred: %s", e)
        raise


if __name__ == "__main__":
    args = parse_arguments()
    arg_points_json = json.loads(args.json_string)
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
        response_to_csv(process_response, "./asset_output/data.csv")
        catalog["data"] = process_response
        try:
            json.dump(catalog, f)
        except Exception as e:
            print("Error writing catalog.json file: %s", e)
