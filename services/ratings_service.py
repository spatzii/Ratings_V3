from analysis import read_custom_ratings
from xlsx_to_json import is_excel_valid, upload_json

from services.storage_service import StorageService
from utils.json_prep import clean_ratings_data

from typing import Dict, Any
import json
import pandas as pd

class RatingsService:

    def __init__(self, contents:bytes, filename:str):
        self.storage_service = StorageService(filename)
        self.contents = contents


    async def process_ratings(self) -> dict:
        xlsx_ratings_sheet = pd.read_excel(self.contents, # type: ignore
                                           sheet_name=2,
                                           header=2,
                                           index_col=0,
                                           usecols=[0] + list(range(19, 37)))

        if not is_excel_valid(xlsx_ratings_sheet):
            raise ValueError("Invalid Excel format")

        return clean_ratings_data(xlsx_ratings_sheet, self.storage_service.extract_date())

    async def upload_ratings(self, df_as_dict):
        return upload_json(df_as_dict, self.storage_service.storage_path())

    @staticmethod
    async def get_ratings(file_path: str, time_range: tuple[str, str], channels: list[str]) -> Dict[str, Any]:
        # Move the display logic here
        result = read_custom_ratings(file_path, time_range, channels)
        return json.loads(result)

