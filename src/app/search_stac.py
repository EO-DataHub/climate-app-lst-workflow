import argparse
import ast
import json
import logging
import os

import dotenv
import pystac_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()


def create_header() -> dict:
    """
    Creates the authorization header using the bearer token from environment variables.

    Returns:
        dict: A dictionary containing the authorization header.
    """
    token = os.environ.get("STAC_API_KEY")
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def open_catalog(catalog_url: str) -> pystac_client.Client:
    """
    Opens a STAC catalog with the provided URL and authorization headers.

    Args:
        catalog_url (str): The URL of the STAC catalog to open.

    Returns:
        pystac_client.Client: The opened STAC catalog client.
    """
    logger.info(f"Opening catalog at {catalog_url}")
    headers = create_header()
    catalog = pystac_client.Client.open(
        catalog_url,
        headers=headers,
    )
    return catalog


def query_to_filter(query: dict) -> dict:
    """
    Converts a query dictionary into a CQL2 JSON filter.

    Args:
        query (dict): A dictionary where keys are property names and
        values are the desired values.

    Returns:
        dict: A CQL2 JSON filter combining all conditions with an 'and' operator.
    """
    filters = []
    for key, value in query.items():
        filters.append(
            {
                "op": "=",
                "args": [{"property": f"properties.{key}"}, value],
            }
        )
    return {"op": "and", "args": filters}


def search_catalog(
    catalog, time_range, query, collection=None, max_items=None
) -> pystac_client.ItemSearch:
    """
    Searches the STAC catalog with the given parameters.

    Args:
        catalog (pystac_client.Client): The STAC catalog client.
        time_range (str): The datetime range for the search.
        query (dict): The query parameters for the search.
        collection (str, optional): The collection to search within.
        max_items (int, optional): The maximum number of items to return.

    Returns:
        pystac_client.ItemSearch: The search results.
    """
    logger.info(
        f"Searching catalog for items with time range {time_range} and query {query}"
    )
    cq2_filter = query_to_filter(query)
    search_params = {"datetime": time_range, "filter": cq2_filter}
    if collection:
        search_params["collections"] = [collection]
    if max_items:
        search_params["max_items"] = max_items
    search = catalog.search(**search_params)
    return search


def get_search_results(search) -> list:
    """
    Retrieves asset hrefs from search results.

    Args:
        search (pystac_client.ItemSearch): The search results.

    Returns:
        list: A list of asset href values.
    """
    logger.info("Getting search results")
    results = []
    for item in search.items():
        results.append(item.get_self_href())
    return results


def parse_args() -> argparse.Namespace:
    """
    Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Search STAC catalog")
    parser.add_argument(
        "--time_range",
        type=str,
        help="Time range to search for items in the catalog",
    )
    parser.add_argument(
        "--query",
        type=dict,
        help="Query to search for items in the catalog",
    )
    parser.add_argument(
        "--catalog_url",
        type=str,
        help="URL of the catalog to search",
        default="https://test.eodatahub.org.uk/api/catalogue/stac/catalogs/user-datasets/sparkgeouser/processing-results/cat_5e389b44-96ca-11ef-bd91-bed226a75fc2",
    )
    parser.add_argument(
        "--collection",
        type=str,
        help="STAC collection to search",
        default=None,
    )
    parser.add_argument(
        "--max_items", type=int, help="Maximum number of items to return", default=None
    )
    return parser.parse_args()


def search_stac(
    time_range: str,
    query: dict,
    catalog_url: str,
    collection: str = None,
    max_items: int = None,
) -> list:
    """
    Searches a STAC catalog with the given parameters.

    Args:
        time_range (str): The datetime range for the search.
        query (dict): The query parameters for the search.
        catalog_url (str): The URL of the STAC catalog to open.
        collection (str, optional): The collection to search within.
        max_items (int, optional): The maximum number of items to return.

    Returns:
        list: A list of dictionaries with datetime keys and asset href values.
    """
    logger.info(f"TYPE: {type(query)}")
    catalog = open_catalog(catalog_url=catalog_url)
    search = search_catalog(
        catalog,
        time_range=time_range,
        query=query,
        collection=collection,
        max_items=max_items,
    )
    results = get_search_results(search)
    return results


def process_stac_query_args(stac_query: str) -> dict:
    """
    Processes the STAC query string and returns a dictionary.

    Args:
        stac_query (str): The query string to process.

    Returns:
        dict: The query parameters as a dictionary.
    """
    logger.info(f"Processing STAC query string: {stac_query}")
    if stac_query is None:
        raise RuntimeError("The STAC query string is missing.")
    try:
        logger.info(f"Type of stac_query: {type(stac_query)}")
        try:
            query_dict = json.loads(stac_query)
        except json.JSONDecodeError:
            try:
                query_dict = ast.literal_eval(stac_query)
            except ValueError as e:
                raise ValueError(f"Invalid stac_query format: {e}") from e
        stac_catalog = query_dict.pop("stac_catalog")
        start_date = query_dict.pop("start_date")
        end_date = query_dict.pop("end_date")
        collection = query_dict.pop("collection")
        time_range = f"{start_date}/{end_date}"
        max_items = query_dict.pop("max_items", None)
        return {
            "stac_catalog": stac_catalog,
            "time_range": time_range,
            "collection": collection,
            "query": query_dict,
            "max_items": max_items,
        }
    except json.JSONDecodeError as exc:
        raise RuntimeError("Failed to decode the STAC query string") from exc


if __name__ == "__main__":
    # Example call ❯ python search_stac.py --time_range "2024-05-01/2024-05-04"
    # --query '{"day_night": {"eq": "DAY"}}'                            ─╯
    args = parse_args()
    query = json.loads(args.query)
    catalog = open_catalog(catalog_url=args.catalog_url)
    search = search_catalog(
        catalog,
        time_range=args.time_range,
        query=query,
        collection=args.collection,
        max_items=args.max_items,
    )
    results = get_search_results(search)
    print(results)
