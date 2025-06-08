from analysis import read_custom_ratings
from xlsx_to_json import is_excel_valid, prepare_json
from utils.utils_endpoints import return_file_path

from typing import Dict, Any
import json
import pandas as pd

class RatingsService:

    @staticmethod
    async def process_uploaded_ratings(contents_of_xlsx: bytes, filename: str) -> str:
        # Move the upload logic here
        xlsx_ratings_sheet = pd.read_excel(contents_of_xlsx, # type: ignore
                                           sheet_name=2,
                                           header=2,
                                           index_col=0,
                                           usecols=[0] + list(range(19, 37)))

        if not is_excel_valid(xlsx_ratings_sheet):
            raise ValueError("Invalid Excel format")

        return prepare_json(xlsx_ratings_sheet, filename)

    @staticmethod
    async def get_ratings(file_path: str, time_range: tuple[str, str], channels: list[str]) -> Dict[str, Any]:
        # Move the display logic here
        result = read_custom_ratings(file_path, time_range, channels)
        return json.loads(result)

