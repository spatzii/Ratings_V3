import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Common configurations
    pass

class DevelopmentConfig(Config):
    STORAGE_PATH = 'C:/Users/panas/PycharmProjects/ratings_backend/ratings_data'
    STORAGE_TYPE = 'local'

class ProductionConfig:
    STORAGE_TYPE = 'firebase'
    FIREBASE_BUCKET = os.getenv('FIREBASE_BUCKET')  # Gets value from .env
    FIREBASE_CREDENTIALS = '/etc/secrets/ratings-firebase-key.json'  # Gets value from .env
    STORAGE_PATH = os.getenv('FIREBASE_STORAGE_PATH', 'Ratings')


# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}