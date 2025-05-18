import firebase_admin
import os

from firebase_admin import credentials, storage, initialize_app
from config import config
from logger import logger


env = os.getenv('ENV', 'development')
current_config = config[env]


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

