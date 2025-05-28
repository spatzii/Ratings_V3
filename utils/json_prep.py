import pandas as pd

from utils.config import current_config
from pathlib import Path
from utils.logger import get_logger
from typing import Final
from datetime import datetime

logger = get_logger(__name__)

INDEX_COLUMN: Final = 'Timebands'


def generate_storage_path(original_filename:str) -> str:
    year, month, day = extract_date_from_filename(original_filename)
    return f"{year}/{month}/{year}-{month}-{day}.json"


def handle_storage_path(base_path: str) -> str:
    """Handle storage-specific path operations

    Example:
        >>> received_path = ...

    """
    if current_config.STORAGE_TYPE == 'local':
        full_path: Path = Path(f"{current_config.STORAGE_PATH}/{base_path}")
        if full_path.exists():
            logger.info(f"File {full_path} already exists, skipping...")
            return str(full_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return str(full_path)
    else:  # firebase
        return f"{current_config.STORAGE_PATH}/{base_path}"


def clean_ratings_data(dataframe, original_filename) -> dict:
    year, month, day = extract_date_from_filename(original_filename)

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


def extract_date_from_filename(filename: str) -> tuple[str, str, str]:
    """Extract year, month, day from the filename in YYYY-MM-DD format."""
    date_str = str(filename).split(' ')[-1].replace('.xlsx', '')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return (str(date_obj.year),
            f"{date_obj.month:02d}",
            f"{date_obj.day:02d}")


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


def rename_columns(df, string_to_remove):
    new_columns: dict = {col: col.replace(string_to_remove, '') for col in df.columns}
    return df.rename(columns=new_columns)  ## Not used!
