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
        from stubs.mock_credentials import MockCredentialsService
        return MockCredentialsService()

    @classmethod
    def get_downloader(cls):
        from services.download_service import RatingsDownloader
        return RatingsDownloader(download_dir=cls.DOWNLOAD_DIR)



class ProductionConfig(Config):
    NAME = "Prod"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', "/Users/stefanpana/PycharmProjects/RatingsBackend"))

    SCHEMA = '/Users/stefanpana/PycharmProjects/RatingsBackend/core/mappings.json'

    @staticmethod
    def get_credentials_service(use_yesterday: bool = False):
        from services.email_service import EmailService
        return EmailService(use_yesterday=use_yesterday)

    @classmethod
    def get_downloader(cls):
        from services.download_service import RatingsDownloader
        return RatingsDownloader(download_dir=cls.DOWNLOAD_DIR)


class RaspberryConfig(Config):
    NAME = "Raspberry"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = Path('/home/panastefan/ratings/downloads')
    SCHEMA = '/home/panastefan/ratings/core/mappings.json'
    SLOTS_CONFIG = PROJECT_ROOT / 'core' / 'time_slots.json'

    @staticmethod
    def get_credentials_service(use_yesterday: bool = False):
        from services.email_service import EmailService
        return EmailService(use_yesterday=use_yesterday)

    @classmethod
    def get_downloader(cls):
        from services.download_service import RatingsDownloader
        return RatingsDownloader(download_dir=cls.DOWNLOAD_DIR)


class TestConfig(Config):
    """Test configuration using stub services and scenario files."""
    NAME = "Test"
    PROJECT_ROOT = Path(__file__).parent.parent
    DOWNLOAD_DIR = PROJECT_ROOT / 'Data' / 'test_downloads'
    SCHEMA = PROJECT_ROOT / 'core' / 'mappings.json'
    SLOTS_CONFIG = PROJECT_ROOT / 'core' / 'time_slots.json'
    SCENARIOS_FILE = PROJECT_ROOT / 'Data' / 'test_scenarios' / 'scenarios.json'

    @classmethod
    def get_credentials_service(cls, use_yesterday: bool = False):
        scenario = os.getenv('TEST_SCENARIO', 'happy_path')
        from stubs.stub_email_service import StubEmailService
        return StubEmailService.from_scenario_file(cls.SCENARIOS_FILE, scenario)

    @classmethod
    def get_downloader(cls):
        scenario = os.getenv('TEST_SCENARIO', 'happy_path')
        from stubs.stub_download_service import StubDownloader
        return StubDownloader.from_scenario_file(
            cls.SCENARIOS_FILE,
            scenario,
            download_dir=cls.DOWNLOAD_DIR
        )


# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'raspberry': RaspberryConfig,
    'test': TestConfig,
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

