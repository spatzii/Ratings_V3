from datetime import datetime
from typing import Final
import pandas as pd
from utils.logger import get_logger


logger = get_logger(__name__)
INDEX_COLUMN: Final = 'Timebands'

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

        if not RatingsService.is_excel_valid(xlsx_ratings_sheet):
            raise ValueError("Invalid Excel format")

        return RatingsService.clean_ratings_data(xlsx_ratings_sheet, self.date)

    @staticmethod
    def clean_ratings_data(dataframe: pd.DataFrame, date: str) -> dict:
        dataframe.columns = [col.replace('.1', '') for col in dataframe.columns]
        dataframe.index = pd.to_datetime([
            RatingsService.fix_broadcast_time(idx, date) for idx in dataframe.index
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

    @staticmethod
    def is_excel_valid(ratings_df: pd.DataFrame) -> bool:
        if ratings_df.columns[4] != "Digi 24.1":
            logger.info("XLSX Validation Error!")
            return False
        else:
            return True


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
