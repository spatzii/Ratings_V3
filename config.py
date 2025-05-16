class Config:
    # Common configurations
    pass

class DevelopmentConfig(Config):
    STORAGE_PATH = 'C:/Users/panas/PycharmProjects/ratings_backend/ratings_data'
    STORAGE_TYPE = 'local'

class ProductionConfig(Config):
    STORAGE_PATH = 'your-firebase-path'  # Firebase storage path
    STORAGE_TYPE = 'firebase'

# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}