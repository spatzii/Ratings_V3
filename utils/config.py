import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    # Common configurations
    pass

class DevelopmentConfig(Config):
    NAME = "Dev"
    PROJECT_ROOT = Path(__file__).parent.parent
    # Create a platform-independent path for storage
    # STORAGE_PATH = str(PROJECT_ROOT / 'ratings_data')

    SCHEMA = 'C:/Users/panas/PycharmProjects/ratings_backend/core/mappings.json'

    @staticmethod
    def get_credentials_service():
        from services.mock_credentials import MockCredentialsService
        return MockCredentialsService()



class ProductionConfig(Config):
    NAME = "Prod"
    PROJECT_ROOT = Path(__file__).parent.parent

    SCHEMA = os.getenv('mappings.json')

    @staticmethod
    def get_credentials_service():
        from services.email_service import EmailService
        return EmailService()

# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def initialize_settings():
    """Initialize application settings and environment configuration."""
    env = os.getenv('ENV', 'development')

    # Load environment variables from .env file in development
    if env in ['development', 'supabase']:
        load_dotenv()

    return config.get(env, config['default'])

# Create a settings instance that can be imported by other modules
current_config = initialize_settings()

