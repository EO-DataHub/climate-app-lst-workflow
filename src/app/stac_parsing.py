"""
Provides functions for parsing STAC (SpatioTemporal Asset Catalog) items,
retrieving specific assets such as COG (Cloud Optimized GeoTIFF) URLs.
"""

import json
from pathlib import Path

import requests
from get_values_logger import logger


def get_stac_item(url: str) -> dict:
    """
    Retrieve a STAC item from a specified URL.

    This function opens a given URL to read a STAC (SpatioTemporal
    Asset Catalog) item, assuming the resource is publicly
    accessible without authentication.

    Parameters:
    - url (str): The URL of the STAC item to retrieve.

    Returns:
    - dict: The STAC item loaded as a dictionary.
    """
    try:
        logger.debug(f"Attempting to open URL: {url}")
        with requests.get(url) as f:
            try:
                logger.debug(f"Successfully opened URL: {url}")
                stac_item = f.json()
            except json.JSONDecodeError as e:
                logger.error(f"Error loading JSON from {url}: {type(e).__name__}: {e}")
                raise ValueError(
                    f"Error loading JSON from {url}: {type(e).__name__}: {e}"
                ) from e
    except Exception as e:
        logger.error(f"Error opening {url}: {type(e).__name__}: {e}")
        raise ValueError(f"Error opening {url}: {type(e).__name__}: {e}") from e
    return stac_item


def get_cog_details_from_stac_url(stac_url: str) -> dict:
    """
    Retrieve COG (Cloud Optimized GeoTIFF) details from a
    STAC (SpatioTemporal Asset Catalog) URL.

    Args:
        stac_url (str): The URL of the STAC item.

    Returns:
        dict: A dictionary containing the COG details extracted from the STAC item.
    """
    stac_item = get_stac_item(stac_url)
    cog_details = get_cog_details(stac_item)
    return cog_details


def get_cog_details(stac_item: dict) -> dict:
    """
    Extract the URL of the first COG (Cloud Optimized GeoTIFF)
    found in the STAC item's assets.

    Iterates through the assets in the provided STAC item, looking
    for an asset with a media type of 'image/tiff' and returns the
    URL of the first match along with the datetime property of the STAC item.

    Parameters:
    - stac_item (dict): The STAC item to search through.

    Returns:
     - dict: A dictionary containing the URL of the COG asset and the datetime property,
            if found. None otherwise.
    """
    # TODO: Get this to work with multiple assets including zarr files
    logger.info("Getting COG details")
    for asset in stac_item["assets"]:
        media_type = stac_item["assets"][asset]["type"]
        if "image/tiff" in media_type:
            cog_url = stac_item["assets"][asset]["href"]
            dt = stac_item["properties"]["datetime"]
            source_file_name = Path(cog_url).stem
            source_file_name = source_file_name.replace(".", "-")
            unit = stac_item["properties"].get("unit", None)
            return {
                "url": cog_url,
                "datetime": dt,
                "source_file_name": source_file_name,
                "unit": unit,
            }


def get_cog_data(stac_item_url_list: list[str]) -> list[dict]:
    """
    Retrieve a list of COG URLs from a list of STAC item URLs.

    This function retrieves a list of COG (Cloud Optimized GeoTIFF)
    URLs from a list of STAC (SpatioTemporal Asset Catalog) item
    URLs. It uses the `get_stac_item` and `get_cog_url` functions
    to load and extract the URLs.

    Parameters:
    - stac_item_url_list (list[dict]): A list of URLs of STAC items.

    Returns:
    - list[str]: A list of COG assets found in the STAC items.
    """
    cog_urls = []
    for stac_item_url in stac_item_url_list:
        stac_item = get_stac_item(stac_item_url)
        cog_url = get_cog_details(stac_item)
        cog_urls.append(cog_url)
    return cog_urls
