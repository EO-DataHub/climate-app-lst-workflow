import os
from datetime import datetime

from dateutil.parser import parse
from pydantic import BaseModel

from app.get_values_logger import logger


class DatasetDetails(BaseModel):
    url: str
    datetime: datetime
    source_file_name: str
    unit: str | None
    output_name: str = None
    crs: str = "EPSG:4326"

    def __init__(self, **data):
        super().__init__(**data)
        self.output_name = self.create_output_name()

    def to_dict(self):
        return {
            "url": self.url,
            "datetime": self.datetime,
            "source_file_name": self.source_file_name,
            "unit": self.unit,
        }

    def create_output_name(self) -> str:
        """
        Create an output name based on the given datetime and optional template.

        Args:
            dt (datetime): The datetime to use for the output name.
            source_file_name (str | None): The source file name (optional).
            output_name_template (str | None): The template for
            the output name (optional).

        Returns:
            str: The generated output name.
        """
        output_name_template = os.environ.get("OUTPUT_NAME_TEMPLATE", None)
        dt = self.datetime
        file_name = self.source_file_name
        if type(dt) is str:
            dt = parse(dt)
        datetime_string = dt.strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(
            "Datetime string: %s, File name: %s",
            datetime_string,
            file_name,
        )
        if output_name_template is not None:
            logger.debug("Raw output name: %s", output_name_template)
            output_name_template = eval(f"f'{output_name_template}'")
            logger.debug("Evaluated output name: %s", output_name_template)
        else:
            output_name_template = dt.strftime("%Y-%m-%d")
            logger.debug("using default output name: %s", output_name_template)
        return output_name_template


class DatasetResult(BaseModel):
    asset_details: DatasetDetails
    values: list
    type: str
    asset: str = None


class ResultValues(BaseModel):
    variable: str
    dataset_details: DatasetDetails
    values: list[dict]
