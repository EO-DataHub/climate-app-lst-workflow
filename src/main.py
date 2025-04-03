#!/usr/bin/env python3
"""
Main starting point for the workflow.
"""

import argparse

from shortuuid import ShortUUID

from app.asset_data import AssetData
from app.create_response import ResponseStatus, WorkflowResponse
from app.extra import process_extra_args, string_to_json
from app.get_values import DatasetsValueExtractor
from app.get_values_logger import logger
from app.search_stac import StacSearch
from app.stac_parsing import get_asset_data_list


def parse_arguments():
    """
    Parses command-line arguments for the request.

    Returns:
        argparse.Namespace: An object that holds the parsed arguments as
        attributes.
    """
    logger.info("Parsing command-line arguments")
    parser = argparse.ArgumentParser(description="Make a request.")
    parser.add_argument("--assets", type=str, help="GeoJSON string with points data")
    parser.add_argument(
        "--stac_query", type=str, help="Query to pass to stac", default=None
    )
    parser.add_argument("--stac_catalog", type=str, help="STAC catalog URL")
    parser.add_argument("--stac_collection", type=str, help="STAC collection ID")
    parser.add_argument("--start_date", type=str, help="Start date for STAC search")
    parser.add_argument("--end_date", type=str, help="End date for STAC search")
    parser.add_argument(
        "--max_items", type=int, help="Maximum number of items to return", default=None
    )
    parser.add_argument(
        "--extra_args", type=str, help="Extra arguments for the workflow", default=None
    )
    args = parser.parse_args()

    logger.info("Extra arguments: %s", args.extra_args)

    extra_args = process_extra_args(args.extra_args)

    for key, value in extra_args.items():
        setattr(args, key, value)

    logger.info("Parsed extra arguments: %s", args.extra_args)
    args.stac_query = string_to_json(args.stac_query) if args.stac_query else None

    return args


def run_workflow(args: argparse.Namespace) -> None:
    """
    Runs the workflow with the provided arguments.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    stac_search = StacSearch(
        catalog_url=args.stac_catalog,
        start_date=args.start_date,
        end_date=args.end_date,
        stac_query=args.stac_query,
        collection=args.stac_collection,
        max_items=args.max_items,
    )

    no_of_results = stac_search.number_of_results
    if no_of_results == 0:
        logger.error("No STAC items found")
        WorkflowResponse(status=ResponseStatus.ERROR, error_msg="No STAC items found")
    else:
        logger.info(f"Found {no_of_results} STAC items, getting points data")
        spatial_data = AssetData(args.assets)

        logger.info("Getting asset data list")
        asset_data_list = get_asset_data_list(stac_search.results)

        logger.info("Getting values from STAC items")

        dve = DatasetsValueExtractor(
            dataset_details_list=asset_data_list,
            assets=spatial_data,
            expression=args.expression,
        )

        # Add id to features if it does not exist
        for feature in dve.assets.json_data["features"]:
            if "id" not in feature["properties"]:
                feature["properties"]["id"] = ShortUUID().random(length=8)
            feature["properties"]["returned_values"] = {}

        print(f"args.output_type: {args.output_type}")
        print(f"args.variable: {args.variable}")
        if args.output_type == "min_max":
            dve.get_min_max_values()
        else:
            dve.get_values_for_datasets(variable=args.variable)

        # Add summary statistics to the features
        dve.add_summary_statistics()

        WorkflowResponse(
            return_values=dve.assets.json_data,
            status=ResponseStatus.SUCCESS,
        )


if __name__ == "__main__":
    logger.info("Starting the workflow")
    args = parse_arguments()
    run_workflow(args)
