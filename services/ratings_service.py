from analysis import read_custom_ratings
from xlsx_to_json import is_excel_valid, upload_json

from services.storage_service import StorageService
from utils.json_prep import clean_ratings_data

from typing import Dict, Any
import json
import pandas as pd


class RatingsService:
    """Service for processing, uploading, and retrieving TV ratings data from Excel files.

    This service handles the complete lifecycle of ratings data, from initial Excel processing
    to storage management and retrieval of processed data.
    """

    def __init__(self, contents: bytes, filename: str):
        """Initialize the RatingsService with Excel file contents and filename.

        Args:
            contents (bytes): Raw binary contents of the Excel file
            filename (str): Name of the Excel file [Digi 24-audiente zilnice la minut YYYY-MM-DD.xlsx]
        """
        self.filename = filename
        self.storage_service = StorageService(self.filename)
        self.contents = contents

    async def process_ratings(self) -> dict:
        """Process the Excel ratings file into a standardized format.

        Reads the Excel file from the third sheet (index 2), starting from the third row (header=2),
        using the first column as index and columns 19-37 for ratings data.

        Returns:
            dict: Processed and cleaned ratings data with extracted dates

        Raises:
            ValueError: If the Excel file format is invalid
        """
        xlsx_ratings_sheet = pd.read_excel(self.contents,  # type: ignore
                                           sheet_name=2,
                                           header=2,
                                           index_col=0,
                                           usecols=[0] + list(range(19, 37)))

        if not is_excel_valid(xlsx_ratings_sheet):
            raise ValueError("Invalid Excel format")

        return clean_ratings_data(xlsx_ratings_sheet, self.date)

    async def upload_ratings(self, df_as_dict):
        """Upload processed ratings data to storage.

        Args:
            df_as_dict: Dictionary containing the processed ratings data

        Returns:
            str: Storage path where the data was uploaded
        """
        return upload_json(df_as_dict, self.storage_service.storage_path())

    @staticmethod
    async def get_ratings(file_path: str, time_range: tuple[str, str], channels: list[str]) -> Dict[str, Any]:
        """Retrieve and process ratings data for specific channels and time ranges.

        Args:
            file_path (str): Path to the JSON file containing ratings data
            time_range (tuple[str, str]): Tuple of (start_time, end_time) in "HH:MM" format
            channels (list[str]): List of channel names to retrieve ratings for

        Returns:
            Dict[str, Any]: JSON-formatted ratings data containing resampled and mean values

        Example:
            >>>   RatingsService.get_ratings(
            ...     "ratings/2025-06-13.json",
            ...     ("20:00", "22:59"),
            ...     ["Channel1", "Channel2"]
            ... )
        """
        result = read_custom_ratings(file_path, time_range, channels)
        return json.loads(result)

    @property
    def date(self) -> str:
        dates:tuple = self.storage_service.extract_date()
        return f"{dates[0]}-{dates[1]}-{dates[2]}" ### 2025-06-12
