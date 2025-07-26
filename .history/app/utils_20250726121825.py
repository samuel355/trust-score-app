from supabase import create_client, Client
from app.config import Config
import random
import uuid
from datetime import datetime


def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_API_KEY
    return create_client(url, key)


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
