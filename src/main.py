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


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for the request.

    Returns:
        argparse.Namespace: An object that holds the parsed arguments as
        attributes.

    Raises:
        ValueError: If required arguments are missing or invalid.
    """
    logger.info("Parsing command-line arguments")
    parser = argparse.ArgumentParser(description="Make a request.")
    parser.add_argument(
        "--assets", type=str, required=True, help="GeoJSON string with points data"
    )
    parser.add_argument(
        "--stac_query", type=str, help="Query to pass to stac", default=None
    )
    parser.add_argument(
        "--stac_catalog", type=str, required=True, help="STAC catalog URL"
    )
    parser.add_argument(
        "--stac_collection", type=str, required=True, help="STAC collection ID"
    )
    parser.add_argument(
        "--start_date", type=str, required=True, help="Start date for STAC search"
    )
    parser.add_argument(
        "--end_date", type=str, required=True, help="End date for STAC search"
    )
    parser.add_argument(
        "--max_items", type=int, help="Maximum number of items to return", default=None
    )
    parser.add_argument(
        "--extra_args", type=str, help="Extra arguments for the workflow", default=None
    )
    parser.add_argument(
        "--output_type",
        type=str,
        choices=["min_max", "values"],
        required=False,
        default="values",
        help="Type of output to generate",
    )
    parser.add_argument(
        "--variable", type=str, help="Variable to extract values for", default=None
    )

    args = parser.parse_args()

    logger.info("Extra arguments: %s", args.extra_args)

    logger.info("Processing extra arguments")
    extra_args = process_extra_args(args.extra_args)
    for key, value in extra_args.items():
        setattr(args, key, value)

    args.stac_query = string_to_json(args.stac_query) if args.stac_query else None
    return args


def process_stac_search(args: argparse.Namespace) -> StacSearch:
    """
    Process STAC search with error handling.

    Args:
        args: Command line arguments

    Returns:
        StacSearch: Initialized STAC search object

    Raises:
        RuntimeError: If STAC search fails or returns no results
    """
    try:
        stac_search = StacSearch(
            catalog_url=args.stac_catalog,
            start_date=args.start_date,
            end_date=args.end_date,
            stac_query=args.stac_query,
            collection=args.stac_collection,
            max_items=args.max_items,
        )

        if stac_search.number_of_results == 0:
            raise RuntimeError("No STAC items found matching the criteria")

        logger.info(f"Found {stac_search.number_of_results} STAC items")
        return stac_search

    except Exception as e:
        logger.error(f"STAC search failed: {str(e)}")
        raise RuntimeError(f"STAC search failed: {str(e)}") from e


def process_asset_data(args: argparse.Namespace) -> AssetData:
    """
    Process asset data with error handling.

    Args:
        args: Command line arguments

    Returns:
        AssetData: Initialized asset data object

    Raises:
        RuntimeError: If asset data processing fails
    """
    try:
        return AssetData(args.assets)
    except Exception as e:
        logger.error(f"Failed to process asset data: {str(e)}")
        raise RuntimeError(f"Failed to process asset data: {str(e)}") from e


def run_workflow(args: argparse.Namespace) -> None:
    """
    Runs the workflow with the provided arguments.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.

    Raises:
        RuntimeError: If any step of the workflow fails
    """
    try:
        # Process STAC search
        stac_search = process_stac_search(args)

        # Process asset data
        spatial_data = process_asset_data(args)

        # Get asset data list
        logger.info("Getting asset data list")
        asset_data_list = get_asset_data_list(stac_search.results)

        # Initialize value extractor
        dve = DatasetsValueExtractor(
            dataset_details_list=asset_data_list,
            assets=spatial_data,
            expression=args.expression,
        )

        # Add IDs to features if they don't exist
        for feature in dve.assets.json_data["features"]:
            if "id" not in feature["properties"]:
                feature["properties"]["id"] = ShortUUID().random(length=8)
            feature["properties"]["returned_values"] = {}

        # Process values based on output type
        logger.info(f"Processing values with output type: {args.output_type}")
        if args.output_type == "min_max":
            dve.get_min_max_values()
        else:
            if not args.variable:
                raise ValueError("Variable must be specified for value extraction")
            dve.get_values_for_datasets(variable=args.variable)

        # Add summary statistics
        dve.add_summary_statistics()

        # Return success response
        WorkflowResponse(
            return_values=dve.assets.json_data,
            status=ResponseStatus.SUCCESS,
        )

    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        WorkflowResponse(status=ResponseStatus.ERROR, error_msg=str(e))
        raise RuntimeError(f"Workflow failed: {str(e)}") from e


if __name__ == "__main__":
    try:
        logger.info("Starting the workflow")
        args = parse_arguments()
        run_workflow(args)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
