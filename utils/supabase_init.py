from supabase import create_client, Client
from utils.config import current_config

class SupabaseClient:
    _instance = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            cls._instance = create_client(
                current_config.SUPABASE_URL,
                current_config.SUPABASE_KEY
            )
        return cls._instance

supabase = SupabaseClient.get_client()
