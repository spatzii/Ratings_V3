from utils.config import current_config
from supabase import create_client, Client

url: str = current_config.SUPABASE_URL
key: str = current_config.SUPABASE_KEY

