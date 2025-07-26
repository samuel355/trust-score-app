import os

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  # safer way to parse boolean envs
    SECRET_KEY = os.getenv('SECRET_KEY')
    # Add other configuration options here based on environment variables
