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


def process_extra_args(extra_args: str) -> None:
    """
    Processes extra arguments and sets environment variables.

    Args:
        extra_args (str): A JSON string containing extra arguments.
    """
    extra_args = string_to_json(extra_args) if extra_args else None
    variable = extra_args.get("variable", None)
    crs = extra_args.get("crs", None)
    unit = extra_args.get("unit", None)
    output_name = extra_args.get("output_name", None)
    expression = extra_args.get("expression", None)
    output_type = extra_args.get("output_type", None)
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
