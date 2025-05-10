from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

import firebase_admin

from firebase_admin import credentials, storage, initialize_app
import json

import logging

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
    blobs = list(_bucket.list_blobs(max_results=1))
    if blobs:
        logger.info(f"Successfully listed blob: {blobs[0].name}")
    else:
        logger.info("Bucket is empty but accessible")
except Exception as e:
    logger.error(f"Firebase Storage connection test failed: {str(e)}", exc_info=True)



def validate_excel(file, original_filename):

    if file.columns[4] != "Digi 24.1":
        print("Error")
        return "Error"

    else:
        return create_json(file, original_filename)


def create_json(file, original_filename):
    # Creates json file from xlsx & uploads to Firebase
    try:
        year, month = extract_year_and_month(original_filename)
        output_path = Path(f"ratings_data/{year}/{month}/{extract_date_from_filename(original_filename)}.json")

        if output_path.exists():
            logger.info(f"File {output_path} already exists, skipping...")
            return output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        json_data = file.to_json(orient='table')

        # Save locally
        with open(output_path, 'w') as f:
            json.dump(json.loads(json_data), f, indent=2)

        # Upload to Firebase Storage
        bucket = storage.bucket()

        blob_path = f"Ratings/{year}/{month}/{extract_date_from_filename(original_filename)}.json"
        logger.info(f"Uploading to Firebase Storage: {blob_path}")

        blob = bucket.blob(blob_path)
        blob.upload_from_string(
            json_data,
            content_type='application/json'
        )
        logger.info(f"Successfully uploaded: {blob_path}")

    except Exception as e:
        logger.error(f"Error processing {original_filename}: {str(e)}", exc_info=True)
        raise

    return output_path


def extract_year_and_month(filename):
    filename = str(filename).split(' ')[-1].replace('.xlsx', '')
    date_obj= datetime.strptime(filename, '%Y-%m-%d')
    return str(date_obj.year), f"{date_obj.month:02d}, f{date_obj.day:02d}"

def extract_date_from_filename(filename):
    filename = str(filename).split(' ')[-1].replace('.xlsx', '')
    return filename

def read_json(json_str):
    dataframe = pd.DataFrame(json.loads(json_str)['data'])
    return dataframe