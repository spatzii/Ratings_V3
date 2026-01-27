import io
from datetime import datetime
from typing import Final
from utils.logger import get_logger
from utils.config import current_config

import pandas as pd
import json


logger = get_logger(__name__)
INDEX_COLUMN: Final = 'Timebands'
CHANNELS: Final = ['TTV', 'B1TV', 'Romania TV', 'Digi 24', 'Realitatea Plus', 'Antena 3 CNN',
                   'EuroNews', 'TVR 1', 'Antena 1', 'Pro TV', 'DigiSport 1']
SCHEMA_PATH = current_config.SCHEMA

class RatingsFileService:
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
        self.contents = contents

    async def process_ratings_file(self) -> dict:
        """Process the Excel ratings file into a standardized format.

        Reads the Excel file from the third sheet (index 2), starting from the third row (header=2),
        using the first column as index and columns 19-37 for ratings data.

        Returns:
            dict: Processed and cleaned ratings data with extracted dates

        Raises:
            ValueError: If the Excel file format is invalid
        """
        excel_buffer = io.BytesIO(self.contents)

        xlsx_ratings_sheet = pd.read_excel(excel_buffer,  # type: ignore
                                           sheet_name=2, # Periods(U21-59 + g)
                                           header=[1,2],
                                           index_col=0)['Rtg%'][CHANNELS]

        return RatingsFileService.clean_data(xlsx_ratings_sheet, self.date)

    @staticmethod
    def clean_data(dataframe: pd.DataFrame, date: str) -> dict:
        # dataframe.columns = [col.replace('.1', '') for col in dataframe.columns]
        dataframe.index = pd.to_datetime([
            RatingsFileService.fix_broadcast_time(idx, date) for idx in dataframe.index
        ])
        dataframe = dataframe[~dataframe.index.isna()]

        # Prepare for JSON export
        dataframe.index.name = INDEX_COLUMN
        dataframe = dataframe.reset_index()
        dataframe[INDEX_COLUMN] = dataframe[INDEX_COLUMN].dt.strftime('%Y-%m-%d %H:%M')

        schema = {
            "fields": [
                {"name": col, "type": "string" if col == INDEX_COLUMN else "number"}
                for col in dataframe.columns
            ]
        }
        json_data = {
            "schema": schema,
            "data": dataframe.to_dict('records')
        }
        return json_data


    @staticmethod
    def pivot_datatable(json_data: dict) -> list[dict]:
        with open(SCHEMA_PATH, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles the BOM
            mappings = json.load(f)

        df_melted = pd.melt(pd.DataFrame(json_data.get('data')), id_vars=['Timebands'], var_name='channel_id', value_name='rating')
        # Create a mapping dictionary from the schema
        channel_mapping = {channel['name']: str(channel['id']) for channel in mappings['channels']}
        # Replace the values in df_melted['variable'] using the mapping
        df_melted['channel_id'] = df_melted['channel_id'].replace(channel_mapping)

        return df_melted.to_dict('records')





    @staticmethod
    def fix_broadcast_time(timestring: str, date_of_file: str) -> str | None:
        """Convert time strings like '24:00' to next day datetime."""
        try:
            hour, minute = map(int, timestring.split(':'))
            if hour >= 24:
                hour -= 24
                next_day = pd.to_datetime(date_of_file) + pd.Timedelta(days=1)
                return f'{next_day.strftime("%Y-%m-%d")} {hour:02d}:{minute:02d}'
            return f'{date_of_file} {hour:02d}:{minute:02d}'
        except:
            return None

    ### TODO: These two need to be joined
    def extract_date(self) -> tuple[str, str, str]:
        """Extract year, month, day from the filename and returns a tuple in the (YYYY), (MM), (DD) format."""
        date_str = str(self.filename).split(' ')[-1].replace('.xlsx', '')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return (str(date_obj.year),
                f"{date_obj.month:02d}",
                f"{date_obj.day:02d}")

    @property
    def date(self) -> str:
        dates:tuple = self.extract_date()
        return f"{dates[0]}-{dates[1]}-{dates[2]}" ### 2025-06-12
