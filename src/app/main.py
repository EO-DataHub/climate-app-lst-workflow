import json

from app.get_values import get_values_from_multiple_cogs, merge_results_into_dict
from app.get_values_logger import logger
from app.load_cogs import load_multiple_cogs
from app.load_points import check_json, points_to_xr_dataset


def get_data_values(
    cog_files: list[str], points_json: dict, latitude_key: str, longitude_key: str
):
    cog_dss = load_multiple_cogs(cog_files)
    check_json(points_json, latitude_key, longitude_key)
    points = points_to_xr_dataset(points_json, latitude_key, longitude_key)
    return_values = get_values_from_multiple_cogs(datasets=cog_dss, points=points)
    return_json = merge_results_into_dict(return_values, points_json)
    return return_json


def lambda_handler(event, context):
    logger.info("Starting lambda function")
    cog_files = event["cog_files"]
    points_json = event["points"]
    if points_json:
        points_json = json.loads(points_json)
    latitude_key = event["latitude_key"]
    longitude_key = event["longitude_key"]

    if not all([points_json, cog_files, latitude_key, longitude_key]):
        return {"statusCode": 400, "body": json.dumps("Missing required parameters")}
    try:
        response = get_data_values(cog_files, points_json, latitude_key, longitude_key)
        return {"statusCode": 200, "body": json.dumps(response)}
    except Exception as e:
        logger.error("Error: %s", e)
        return {"statusCode": 500, "body": json.dumps(str(e))}
