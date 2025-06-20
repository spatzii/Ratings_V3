import firebase_admin
import os

from firebase_admin import credentials, storage
from utils.config import current_config
from utils.logger import get_logger

logger = get_logger(__name__)



def initialize_firebase():
    """Initialize Firebase app if not already initialized."""
    if current_config.STORAGE_TYPE != 'firebase':
        return None

    try:
        return firebase_admin.get_app()
    except ValueError:  # Raised when no default app is initialized
        try:
            cred = credentials.Certificate(current_config.FIREBASE_CREDENTIALS)
            app = firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv('FIREBASE_BUCKET')
            })
            logger.info("Firebase initialized successfully")
            return app
        except Exception as e:
            logger.error(f"Firebase initialization error: {str(e)}")
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

