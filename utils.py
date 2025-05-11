from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

import firebase_admin

from firebase_admin import credentials, storage, initialize_app
import json

import logging

INDEX_COLUMN = 'Timebands'


# Configure logging to output to console only
logging.basicConfig(
    level=logging.INFO,  # Use INFO level for production
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


try:
    cred = credentials.Certificate("C:/Users/panas/PycharmProjects/ratings_backend/ratings-firebase-key.json")
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': 'ratings-v2-firebase.firebasestorage.app'
    })
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Firebase initialization error: {str(e)}")

logger.info("Testing Firebase Storage connection...")

try:
    _bucket = storage.bucket()
    logger.info(f"Successfully connected to bucket: {_bucket.name}")
    # blobs = list(_bucket.list_blobs(max_results=1))
    # if blobs:
    #     logger.info(f"Successfully listed blob: {blobs[0].name}")
    # else:
    #     logger.info("Bucket is empty but accessible")
except Exception as e:
    logger.error(f"Firebase Storage connection test failed: {str(e)}", exc_info=True)

def validate_excel(file, original_filename):

    if file.columns[4] != "Digi 24.1":
        logger.info("XLSX Validation Error!")
        return "Error"

    else:
        return create_json(file, original_filename)


def create_json(dataframe, original_filename):
    # Creates json file from xlsx & uploads to Firebase
    try:
        year, month, day = extract_date_from_filename(original_filename)
        file_date = f"{year}-{month}-{day}"
        output_path = Path(f"ratings_data/{year}/{month}/{year}-{month}-{day}.json")

        if output_path.exists():
            logger.info(f"File {output_path} already exists, skipping...")
            return output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean up column names and process timestamps
        dataframe.columns = [col.replace('.1', '') for col in dataframe.columns]
        dataframe.index = pd.to_datetime([
            fix_broadcast_time(idx, file_date) for idx in dataframe.index
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
        # Export to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)



        # Upload to Firebase Storage
    #     bucket = storage.bucket()
    #
    #     blob_path = f"Ratings/{year}/{month}/{extract_date_from_filename(original_filename)}.json"
    #     logger.info(f"Uploading to Firebase Storage: {blob_path}")
    #
    #     blob = bucket.blob(blob_path)
    #     blob.upload_from_string(
    #         json_data,
    #         content_type='application/json'
    #     )
    #     logger.info(f"Successfully uploaded: {blob_path}")
    #
    except Exception as e:
        logger.error(f"Error processing {original_filename}: {str(e)}", exc_info=True)
        raise

    return output_path


def extract_date_from_filename(filename: Path) -> tuple[str, str, str]:
    """Extract year, month, day from filename in YYYY-MM-DD format."""
    date_str = str(filename).split(' ')[-1].replace('.xlsx', '')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return (str(date_obj.year),
            f"{date_obj.month:02d}",
            f"{date_obj.day:02d}")

def fix_broadcast_time(timestr: str, date_of_file: str) -> str | None:
    """Convert time strings like '24:00' to next day datetime."""
    try:
        hour, minute = map(int, timestr.split(':'))
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

def read_json(file):
    with file.open('r', encoding='utf-8') as f:
        data = json.load(f)
        dataframe = pd.DataFrame(data['data'])
        dataframe.set_index(INDEX_COLUMN, inplace=True)
        dataframe.index = pd.to_datetime(dataframe.index)
        return dataframe
