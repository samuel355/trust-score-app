from supabase import create_client, Client
from app.config import Config


def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_API_KEY
    return create_client(url, key)
