import pandas as pd

from services.storage_service import StorageService
from utils.logger import get_logger
from typing import Final

logger = get_logger(__name__)

INDEX_COLUMN: Final = 'Timebands'


def clean_ratings_data(dataframe, date:tuple[str, str, str]) -> dict:
    year, month, day = date

    file_format_from_date: str = f"{year}-{month}-{day}"

    dataframe.columns = [col.replace('.1', '') for col in dataframe.columns]
    dataframe.index = pd.to_datetime([
        fix_broadcast_time(idx, file_format_from_date) for idx in dataframe.index
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
