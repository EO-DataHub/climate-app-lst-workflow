"""
Main starting point for the Lambda function.
"""

import json

from app.get_values import get_values_from_multiple_cogs, merge_results_into_dict
from app.get_values_logger import logger
from app.load_cogs import load_multiple_cogs
from app.load_points import check_json, points_to_xr_dataset
from app.stac_parsing import get_cog_urls


def get_data_values(
    stac_items: list[str], points_json: dict, latitude_key: str, longitude_key: str
):
    """
    Fetches data values for given points from STAC items.

    This function retrieves Cloud Optimized GeoTIFF (COG) URLs
    from the provided STAC items, loads the COGs, and extracts
    data values at specified points. The results are merged into
    a dictionary structure and returned.

    Parameters:
    - stac_items (list[str]): List of STAC item URLs.
    - points_json (dict): JSON object containing points.
    - latitude_key (str): Key for latitude in points_json.
    - longitude_key (str): Key for longitude in points_json.

    Returns:
    dict: A dictionary with the merged results of data values
    for the provided points.
    """
    cog_item_urls = get_cog_urls(stac_items)
    cog_dss = load_multiple_cogs(cog_item_urls)
    check_json(points_json, latitude_key, longitude_key)
    points = points_to_xr_dataset(points_json, latitude_key, longitude_key)
    return_values = get_values_from_multiple_cogs(datasets=cog_dss, points=points)
    return_json = merge_results_into_dict(return_values, points_json)
    return return_json


def lambda_handler(event, _):
    """
    Handles incoming requests to the Lambda function.

    This function processes events by extracting necessary
    parameters from the event body, validates them, and then
    calls `get_data_values` to fetch data values for given
    points from STAC items.

    Parameters:
    - event (dict): The event dict containing the request body.
    - context: The context in which the Lambda function is called.

    Returns:
    dict: A dictionary with either the fetched data values or
    an error message and corresponding HTTP status code.
    """
    logger.info("Received event: %s", json.dumps(event))
    logger.info("Starting lambda function")
    body = json.loads(event["body"])
    stac_items = body.get("stac_items")
    points_json = body.get("points")
    if points_json:
        points_json = json.loads(points_json)
    latitude_key = body.get("latitude_key")
    longitude_key = body.get("longitude_key")

    if not all([points_json, stac_items, latitude_key, longitude_key]):
        return {"statusCode": 400, "body": json.dumps("Missing required parameters")}
    try:
        response = get_data_values(stac_items, points_json, latitude_key, longitude_key)
        return {"statusCode": 200, "body": json.dumps(response)}
    except Exception as e:
        logger.error("Error: %s", e)
        return {"statusCode": 500, "body": json.dumps(str(e))}
