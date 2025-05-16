import os

class Config:
    # Common configurations
    pass

class DevelopmentConfig(Config):
    STORAGE_PATH = 'C:/Users/panas/PycharmProjects/ratings_backend/ratings_data'
    STORAGE_TYPE = 'local'

class ProductionConfig(Config):
    STORAGE_TYPE = 'firebase'
    # Firebase configuration - these should be loaded from environment variables
    FIREBASE_BUCKET = os.getenv('FIREBASE_BUCKET')
    FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')
    # If you need a path-like structure in Firebase
    STORAGE_PATH = os.getenv('FIREBASE_STORAGE_PATH', 'ratings_data')


# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}