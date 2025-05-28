import json
import pandas as pd

from utils.config import current_config
from pathlib import Path
from firebase_admin import storage
from utils.logger import get_logger
from typing import Final

from utils.json_prep import generate_storage_path, handle_storage_path, clean_ratings_data

logger = get_logger(__name__)

INDEX_COLUMN: Final = 'Timebands'


def validate_excel(ratings_df: pd.DataFrame) -> bool:
    if ratings_df.columns[4] != "Digi 24.1":
        logger.info("XLSX Validation Error!")
        return False
    else:
        return True


def prepare_json(ratings_df: pd.DataFrame, original_filename: str) -> str:
    storage_path:str = generate_storage_path(original_filename)
    full_path:str = handle_storage_path(storage_path)
    prepared_json:dict = clean_ratings_data(ratings_df, original_filename)
    upload_json(prepared_json, full_path)
    return full_path


def upload_json(prepared_json:dict, output_path:str) -> None:
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


def json_to_df(file):
    data = None  ## supress "local variable might be referenced before assignment"

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
