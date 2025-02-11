import ast
import json

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
