import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object('app.config') # Load configurations from config.py

# Import and register blueprints (routes) here
from app.routes import bp as routes_bp
app.register_blueprint(routes_bp)

# Initialize database (if using one)
# Example: db.init_app(app)

# Initialize other components (Wazuh, Elasticsearch client)
