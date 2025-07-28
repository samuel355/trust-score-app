import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print environment variables
print(f"DEBUG: SUPABASE_URL from env: {os.getenv('SUPABASE_URL')}")

app = Flask(__name__)
app.config.from_object('app.config') # Load configurations from config.py

# Initialize Flask-Login for Okta authentication
from app.auth import login_manager
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import and register blueprints (routes) here
from app.routes import bp as routes_bp
app.register_blueprint(routes_bp)

# Register auth blueprint
from app.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

# ML API blueprint will be registered separately to avoid circular imports
def register_ml_blueprint():
    """Register ML blueprint after app initialization to avoid circular imports"""
    try:
        from routes.ml_endpoints import ml_bp
        app.register_blueprint(ml_bp)
        print("✅ ML API endpoints registered successfully")
    except Exception as e:
        print(f"❌ Failed to register ML endpoints: {e}")

# Register ML blueprint after all other initialization
register_ml_blueprint()

# Initialize database (if using one)
# Example: db.init_app(app)

# Initialize other components (Wazuh, Elasticsearch client)
