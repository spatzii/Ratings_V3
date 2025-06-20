import os
from pathlib import Path
from dotenv import load_dotenv
import json

class Config:
    # Common configurations
    pass

class DatabaseConfig(Config):
    PROJECT_ROOT = Path(__file__).parent.parent

    # Read from environment variable instead of file
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    if not SUPABASE_KEY:
        # Only try to read from file if env var is not set (development environment)
        try:
            _key_path = PROJECT_ROOT / 'sql' / 'postgres_key.json'
            with open(_key_path) as f:
                _key_data = json.load(f)
                SUPABASE_KEY = _key_data.get('SUPABASE_KEY')
        except FileNotFoundError:
            # Handle the case when neither env var nor file exists
            SUPABASE_KEY = None

    STORAGE_TYPE = 'sql'
    SUPABASE_URL = 'https://rfisrnemucoeijomqqxp.supabase.co'


class DevelopmentConfig(Config):

    ### FIREBASE
    PROJECT_ROOT = Path(__file__).parent.parent
    # Create a platform-independent path for storage
    STORAGE_PATH = str(PROJECT_ROOT / 'ratings_data')
    STORAGE_TYPE = 'local'



class ProductionConfig(Config):

    ### FIREBASE
    STORAGE_TYPE = 'firebase'
    FIREBASE_BUCKET = os.getenv('FIREBASE_BUCKET')  # Gets value from .env
    FIREBASE_CREDENTIALS = '/etc/secrets/ratings-firebase-key.json'  # Gets value from Server (Render atm) .env
    STORAGE_PATH = os.getenv('FIREBASE_STORAGE_PATH', 'Ratings')
    ### SUPABASE
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')


# You can set this based on an environment variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'supabase': DatabaseConfig
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

