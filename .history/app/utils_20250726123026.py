from app.config import Config
import random
import uuid
from datetime import datetime
import json
import os


def generate_synthetic_telemetry():
    # Example feature names (replace with real names if available)
    feature_names = [f'feature_{i+1}' for i in range(62)]
    telemetry = {name: random.uniform(0, 100) for name in feature_names}
    # Add required metadata
    telemetry['session_id'] = str(uuid.uuid4())
    telemetry['vm_id'] = f'vm_{random.randint(1, 10)}'
    telemetry['event_type'] = random.choice(['login_success', 'login_failed', 'file_access', 'network_anomaly'])
    telemetry['timestamp'] = datetime.utcnow().isoformat()
    return telemetry


def load_sample_cicids2017_data():
    """Load sample CICIDS2017 data from JSON file for testing"""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_cicids2017_data.json')
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Sample data file not found at {file_path}")
        return None
