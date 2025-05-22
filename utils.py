import json
import pandas as pd

from config import current_config
from datetime import datetime
from pathlib import Path
from firebase_admin import storage
from logger import logger
from typing import Final

INDEX_COLUMN: Final = 'Timebands'


def validate_original_excel_file(ratings_df):

    if ratings_df.columns[4] != "Digi 24.1":
        logger.info("XLSX Validation Error!")
        return "Error"
    else:
        return True

def prepare_json(ratings_df, original_filename_as_string):
    storage_path = generate_storage_path(original_filename_as_string)
    full_path = handle_storage_path(storage_path)
    prepared_json = clean_ratings_data(ratings_df, original_filename_as_string)
    return upload_json(prepared_json, full_path)

def generate_storage_path(original_filename):
    year, month, day = extract_date_from_filename(original_filename)
    return f"{year}/{month}/{year}-{month}-{day}.json"

def handle_storage_path(base_path: str) -> str:
    """Handle storage-specific path operations"""
    if current_config.STORAGE_TYPE == 'local':
        full_path = Path(f"{current_config.STORAGE_PATH}/{base_path}")
        if full_path.exists():
            logger.info(f"File {full_path} already exists, skipping...")
            return str(full_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return str(full_path)
    else:  # firebase
        return f"{current_config.STORAGE_PATH}/{base_path}"

def clean_ratings_data(dataframe, original_filename):
    year, month, day = extract_date_from_filename(original_filename)

    file_format_from_date = f"{year}-{month}-{day}"

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

def upload_json(prepared_json, output_path):
    try:
        if current_config.STORAGE_TYPE == 'local':
            # Export to JSON
            with open(Path(output_path), 'w', encoding='utf-8') as f:
                json.dump(prepared_json, f, indent=2)

        # Upload to Firebase Storage
        if current_config.STORAGE_TYPE == 'firebase':
            bucket = storage.bucket()
            logger.info(f"Uploading to Firebase Storage: {output_path}")
            blob = bucket.blob(output_path)
            blob.upload_from_string(
                json.dumps(prepared_json),
                content_type='application/json'
            )
            logger.info(f"Successfully uploaded: {output_path}")

    except Exception as e:
        logger.error(f"Error processing {output_path}: {str(e)}", exc_info=True)
        raise

    return output_path

def extract_date_from_filename(filename: Path) -> tuple[str, str, str]:
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
    new_columns = {col: col.replace(string_to_remove, '') for col in df.columns}
    return df.rename(columns=new_columns)

def unpack_json_to_dataframe(file):
    data = None ## supress "local variable might be referenced before assignment"

    try:
        if current_config.STORAGE_TYPE == 'firebase':
            # Handle Firebase storage path
            bucket = storage.bucket()
            blob = bucket.blob(file)  # file here is the path string
            content = blob.download_as_text()
            data = json.loads(content)
        else:
            # Handle local file path
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        dataframe = pd.DataFrame(data['data'])
        dataframe.set_index(INDEX_COLUMN, inplace=True)
        dataframe.index = pd.to_datetime(dataframe.index)
        return dataframe
    except Exception as e:
        logger.error(f"Error reading JSON: {str(e)}")
        raise

def test_firebase():
    if current_config.STORAGE_TYPE == 'firebase':
        try:
            bucket = storage.bucket()
            logger.info(f"Testing connection to bucket: {bucket.name}")
            return {
                "status": "success",
                "message": f"Successfully connected to Firebase bucket: {bucket.name}"
            }
        except Exception as e:
            logger.error(f"Firebase connection test failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Firebase connection failed: {str(e)}"
            }
    else:
        return {
            "status": "error",
            "message": "Firebase storage is not configured"
        }

