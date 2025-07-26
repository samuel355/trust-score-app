import os

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  # safer way to parse boolean envs
    SECRET_KEY = os.getenv('SECRET_KEY')
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-supabase-url.supabase.co')
    SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY', 'your-supabase-api-key')
