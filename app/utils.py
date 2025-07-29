from supabase import create_client, Client
from app.config import Config
import random
import uuid
from datetime import datetime
import json
import os
from elasticsearch import Elasticsearch
import logging

# Set up logging
logger = logging.getLogger(__name__)

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


def load_sample_cicids2017_data():
    """Load sample CICIDS2017 data from JSON file and generate multiple samples for training"""
    import pandas as pd
    import numpy as np
    import json
    import os

    # Path to the sample JSON file
    json_file_path = "data/sample_cicids2017_data.json"

    if not os.path.exists(json_file_path):
        print(f"❌ Sample JSON file not found: {json_file_path}")
        # Create a minimal fallback dataset
        return pd.DataFrame({
            'Flow Duration': [0.123],
            'Total Fwd Packets': [45],
            'Label': ['BENIGN']
        })

    try:
        # Load the sample JSON file
        with open(json_file_path, 'r') as f:
            sample_data = json.load(f)

        # Filter out non-feature fields to get only CICIDS2017 features
        exclude_fields = ['session_id', 'vm_id', 'event_type', 'timestamp']
        features = {k: v for k, v in sample_data.items() if k not in exclude_fields}

        # Generate multiple samples based on the template
        n_samples = 1000
        np.random.seed(42)  # For reproducible results

        data_rows = []
        for i in range(n_samples):
            row = {}
            for feature, base_value in features.items():
                if isinstance(base_value, (int, float)):
                    # Add realistic variations to numeric values
                    if feature in ['Init_Win_bytes_forward', 'Init_Win_bytes_backward']:
                        # Keep window size values realistic
                        row[feature] = np.random.choice([0, 65535, 32768, 8192], p=[0.1, 0.5, 0.3, 0.1])
                    elif 'Count' in feature or 'Flags' in feature:
                        # Integer flags and counts with small variations
                        variation = np.random.poisson(lam=max(1, abs(base_value)))
                        row[feature] = max(0, variation)
                    elif 'Duration' in feature or 'IAT' in feature:
                        # Time-related features
                        variation = np.random.exponential(scale=max(0.001, abs(base_value)))
                        row[feature] = max(0, variation)
                    else:
                        # Other numeric features with realistic variations (±30%)
                        variation_factor = np.random.uniform(0.7, 1.3)
                        row[feature] = max(0, base_value * variation_factor)
                else:
                    row[feature] = base_value

            data_rows.append(row)

        # Create DataFrame
        df = pd.DataFrame(data_rows)

        # Add Label column (80% BENIGN, 20% MALICIOUS)
        labels = np.random.choice(['BENIGN', 'MALICIOUS'], size=n_samples, p=[0.8, 0.2])
        df['Label'] = labels

        print(f"✅ Generated CICIDS2017 dataset from sample: {df.shape[0]} samples, {df.shape[1]} features")
        print(f"   Label distribution: {df['Label'].value_counts().to_dict()}")

        return df

    except Exception as e:
        print(f"❌ Error loading sample JSON file: {e}")
        # Create a minimal fallback dataset
        return pd.DataFrame({
            'Flow Duration': [0.123],
            'Total Fwd Packets': [45],
            'Label': ['BENIGN']
        })


def load_real_sample_cicids2017_data():
    """Load data from the actual sample_cicids2017_data.json file"""
    import pandas as pd
    import numpy as np
    import json
    import os

    # Path to the sample JSON file
    json_file_path = "data/sample_cicids2017_data.json"

    if not os.path.exists(json_file_path):
        print(f"❌ Sample JSON file not found: {json_file_path}")
        return load_sample_cicids2017_data()  # Fallback to synthetic data

    try:
        # Load the JSON file
        with open(json_file_path, 'r') as f:
            sample_data = json.load(f)

        # Filter out non-feature fields
        exclude_fields = ['session_id', 'vm_id', 'event_type', 'timestamp']
        features = {k: v for k, v in sample_data.items() if k not in exclude_fields}

        # Create multiple samples based on the single JSON sample
        n_samples = 1000
        np.random.seed(42)  # For reproducible results

        # Generate variations of the sample data
        data_rows = []
        for i in range(n_samples):
            row = {}
            for feature, base_value in features.items():
                if isinstance(base_value, (int, float)):
                    # Add some variation to numeric values
                    if feature in ['Init_Win_bytes_forward', 'Init_Win_bytes_backward']:
                        # Keep window size values as-is or common values
                        row[feature] = np.random.choice([0, 65535, 32768, 8192], p=[0.1, 0.5, 0.3, 0.1])
                    elif 'Count' in feature or 'Flags' in feature:
                        # Integer flags and counts
                        row[feature] = max(0, int(base_value + np.random.normal(0, 1)))
                    else:
                        # Other numeric features with some variation
                        variation = np.random.normal(1, 0.2)  # 20% variation
                        row[feature] = max(0, base_value * variation)
                else:
                    row[feature] = base_value

            data_rows.append(row)

        # Create DataFrame
        df = pd.DataFrame(data_rows)

        # Add Label column (80% BENIGN, 20% MALICIOUS)
        labels = np.random.choice(['BENIGN', 'MALICIOUS'], size=n_samples, p=[0.8, 0.2])
        df['Label'] = labels

        print(f"✅ Loaded real sample CICIDS2017 data: {df.shape[0]} samples, {df.shape[1]} features")
        print(f"   Label distribution: {df['Label'].value_counts().to_dict()}")

        return df

    except Exception as e:
        print(f"❌ Error loading sample JSON file: {e}")
        print("🔄 Falling back to synthetic data generation...")
        return load_sample_cicids2017_data()  # Fallback to synthetic data


def load_multiple_cicids2017_files(data_dir="data/"):
    """
    Load multiple CICIDS2017 JSON files from data directory
    This function will be used when you get the real RFE-processed CICIDS2017 dataset
    """
    import pandas as pd
    import json
    import os
    import glob

    try:
        # Look for all JSON files in data directory
        json_pattern = os.path.join(data_dir, "*.json")
        json_files = glob.glob(json_pattern)

        if not json_files:
            print(f"❌ No JSON files found in {data_dir}")
            return load_sample_cicids2017_data()  # Fallback to sample-based data

        print(f"📂 Found {len(json_files)} JSON files in {data_dir}")

        all_data = []
        exclude_fields = ['session_id', 'vm_id', 'event_type', 'timestamp']

        for json_file in json_files:
            print(f"📄 Loading {os.path.basename(json_file)}...")

            try:
                with open(json_file, 'r') as f:
                    file_data = json.load(f)

                # Handle both single objects and arrays of objects
                if isinstance(file_data, list):
                    # Multiple records in file
                    for record in file_data:
                        # Filter out non-feature fields
                        features = {k: v for k, v in record.items() if k not in exclude_fields}
                        if features:  # Only add if there are actual features
                            all_data.append(features)
                else:
                    # Single record in file
                    features = {k: v for k, v in file_data.items() if k not in exclude_fields}
                    if features:
                        all_data.append(features)

            except Exception as e:
                print(f"⚠️  Error loading {json_file}: {e}")
                continue

        if not all_data:
            print("❌ No valid data found in JSON files")
            return load_sample_cicids2017_data()

        # Create DataFrame from all loaded data
        df = pd.DataFrame(all_data)

        # If no Label column exists, add one (for when real data doesn't have labels yet)
        if 'Label' not in df.columns:
            print("🏷️  No labels found, adding synthetic labels for training...")
            # Add synthetic labels (80% BENIGN, 20% MALICIOUS)
            import numpy as np
            np.random.seed(42)
            labels = np.random.choice(['BENIGN', 'MALICIOUS'], size=len(df), p=[0.8, 0.2])
            df['Label'] = labels

        print(f"✅ Loaded real CICIDS2017 dataset: {df.shape[0]} samples, {df.shape[1]} features")
        if 'Label' in df.columns:
            print(f"   Label distribution: {df['Label'].value_counts().to_dict()}")

        return df

    except Exception as e:
        print(f"❌ Error loading multiple JSON files: {e}")
        print("🔄 Falling back to sample-based data generation...")
        return load_sample_cicids2017_data()


def get_elasticsearch_client():
    """Get Elasticsearch client with enhanced HTTPS configuration"""
    try:
        # HTTPS configuration
        ssl_config = {
            'verify_certs': Config.ELASTICSEARCH_SSL_VERIFY,
            'ssl_show_warn': False,
            'request_timeout': 30,
            'retry_on_timeout': True,
            'max_retries': 3
        }

        # Add CA certificate if SSL verification is enabled
        if Config.ELASTICSEARCH_SSL_VERIFY and hasattr(Config, 'ELASTICSEARCH_CA_CERT'):
            ssl_config['ca_certs'] = Config.ELASTICSEARCH_CA_CERT

        client = Elasticsearch(
            Config.ELASTICSEARCH_URL,
            http_auth=(Config.ELASTICSEARCH_USERNAME, Config.ELASTICSEARCH_PASSWORD),
            **ssl_config
        )

        # Test connection
        if client.ping():
            logger.info(f"Elasticsearch client connected successfully to {Config.ELASTICSEARCH_URL}")
        else:
            logger.warning("Elasticsearch ping failed")

        return client

    except Exception as e:
        logger.error(f"Failed to create Elasticsearch client: {str(e)}")
        return None


def index_to_elasticsearch(index_prefix: str, document: dict, es_client=None) -> bool:
    """Helper function to index documents to Elasticsearch with time-based indexing"""
    try:
        if es_client is None:
            es_client = get_elasticsearch_client()

        if es_client is None:
            return False

        # Create time-based index name
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        index_name = f"{index_prefix}-{date_str}"

        # Add @timestamp field for Kibana
        document['@timestamp'] = document.get('timestamp', datetime.utcnow().isoformat())

        response = es_client.index(
            index=index_name,
            body=document
        )

        logger.debug(f"Indexed document to {index_name}: {response['_id']}")
        return True

    except Exception as e:
        logger.error(f"Failed to index to Elasticsearch: {str(e)}")
        return False


def search_elasticsearch(index_pattern: str, query: dict, size: int = 100) -> list:
    """Helper function to search Elasticsearch indices"""
    try:
        es_client = get_elasticsearch_client()
        if es_client is None:
            return []

        response = es_client.search(
            index=index_pattern,
            body=query,
            size=size
        )

        return [hit['_source'] for hit in response['hits']['hits']]

    except Exception as e:
        logger.error(f"Elasticsearch search failed: {str(e)}")
        return []
