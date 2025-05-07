import ast
import json
import os

from app.get_values_logger import logger


def string_to_json(string: str) -> dict | None:
    """
    Converts a string to a JSON object.

    Args:
        string (str): The string to convert.

    Returns:
        dict | None: The JSON object if conversion is successful, None otherwise.
    """
    try:
        return json.loads(string)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(string)
        except (ValueError, SyntaxError) as ast_err:
            logger.error(f"ast.literal_eval failed: {ast_err}")
            return None


def parse_string_to_list(input_string):
    """
    Parses a string representation of a list into an actual list.

    Args:
        input_string (str): The string to parse.

    Returns:
        list | str: The parsed list if the input is a list string, otherwise
        the original string.
    """
    if input_string.startswith("[") and input_string.endswith("]"):
        return ast.literal_eval(input_string)
    return input_string


def process_extra_args(extra_args: str | dict | None) -> dict:
    """
    Processes extra arguments and sets environment variables.

    Args:
        extra_args (str | dict | None): A JSON string or
        dictionary containing extra arguments.

    Returns:
        dict: Dictionary containing processed extra arguments.
    """
    if isinstance(extra_args, dict):
        args_dict = extra_args
    else:
        args_dict = string_to_json(extra_args) if extra_args else {}

    variable = args_dict.get("variable", None)
    crs = args_dict.get("crs", None)
    unit = args_dict.get("unit", None)
    output_name = args_dict.get("output_name", None)
    expression = args_dict.get("expression", None)
    output_type = args_dict.get("output_type", None)

    # Set environment variables
    if output_name:
        os.environ["OUTPUT_NAME_TEMPLATE"] = output_name

    return {
        "variable": variable,
        "crs": crs,
        "unit": unit,
        "expression": expression,
        "output_type": output_type,
    }
