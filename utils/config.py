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
    SLOTS_CONFIG = PROJECT_ROOT / 'core' / 'time_slots.json'

    SCHEMA = '/Users/stefanpana/PycharmProjects/RatingsBackend/core/mappings.json'

    @staticmethod
    def get_credentials_service(use_yesterday:bool = False):
        from services.mock_credentials import MockCredentialsService
        return MockCredentialsService()



class ProductionConfig(Config):
    NAME = "Prod"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', "/Users/stefanpana/PycharmProjects/RatingsBackend"))

    SCHEMA = '/Users/stefanpana/PycharmProjects/RatingsBackend/core/mappings.json'

    @staticmethod
    def get_credentials_service(use_yesterday: bool = False):
        from services.email_service import EmailService
        return EmailService(use_yesterday=use_yesterday)


class RaspberryConfig(Config):
    NAME = "Raspberry"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = Path('/home/pi/ratings/downloads')
    SCHEMA = '/home/panastefan/ratings/core/mappings.json'
    SLOTS_CONFIG = PROJECT_ROOT / 'core' / 'time_slots.json'

    @staticmethod
    def get_credentials_service(use_yesterday: bool = False):
        from services.email_service import EmailService
        return EmailService(use_yesterday=use_yesterday)

# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'raspberry': RaspberryConfig,
    'default': DevelopmentConfig,
}


def initialize_settings():
    """Initialize application settings and environment configuration."""
    # Always load .env file first
    load_dotenv()

    # Get environment from ENV variable, default to development
    env = os.getenv('ENV', 'development')

    print(f"Loading configuration: {env}")  # Debug output

    return config.get(env, config['default'])


# Create a settings instance that can be imported by other modules
current_config = initialize_settings()

