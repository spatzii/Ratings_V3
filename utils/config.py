import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    # Common configurations
    pass

class DevelopmentConfig(Config):
    NAME = "Dev"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = Path("/Users/stefanpana/PycharmProjects/RatingsBackend")

    SCHEMA = '/Users/stefanpana/PycharmProjects/RatingsBackend/core/mappings.json'

    @staticmethod
    def get_credentials_service():
        from services.mock_credentials import MockCredentialsService
        return MockCredentialsService()



class ProductionConfig(Config):
    NAME = "Prod"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', "/Users/stefanpana/PycharmProjects/RatingsBackend"))

    SSCHEMA = '/Users/stefanpana/PycharmProjects/RatingsBackend/core/mappings.json'

    @staticmethod
    def get_credentials_service():
        from services.email_service import EmailService
        return EmailService()


class RaspberryConfig(Config):
    NAME = "Raspberry"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = Path('/home/pi/ratings/downloads')
    SCHEMA = '/home/pi/ratings/core/mappings.json'

    @staticmethod
    def get_credentials_service():
        from services.email_service import EmailService
        return EmailService()

# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'raspberry': RaspberryConfig,
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

