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
    """Load sample CICIDS2017 data and return as pandas DataFrame for testing"""
    import pandas as pd
    import numpy as np

    # Create synthetic CICIDS2017-style dataset with multiple samples
    np.random.seed(42)  # For reproducible results

    n_samples = 1000
    feature_names = [
        'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
        'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
        'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
        'Fwd Packet Length Std', 'Bwd Packet Length Max', 'Bwd Packet Length Min',
        'Bwd Packet Length Mean', 'Bwd Packet Length Std', 'Flow Bytes/s',
        'Flow Packets/s', 'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max',
        'Flow IAT Min', 'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Std',
        'Fwd IAT Max', 'Fwd IAT Min', 'Bwd IAT Total', 'Bwd IAT Mean',
        'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min', 'Fwd PSH Flags',
        'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags', 'Fwd Header Length',
        'Bwd Header Length', 'Fwd Packets/s', 'Bwd Packets/s', 'Min Packet Length',
        'Max Packet Length', 'Packet Length Mean', 'Packet Length Std',
        'Packet Length Variance', 'FIN Flag Count', 'SYN Flag Count',
        'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count',
        'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio', 'Average Packet Size',
        'Avg Fwd Segment Size', 'Avg Bwd Segment Size', 'Fwd Header Length.1',
        'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate',
        'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate',
        'Subflow Fwd Packets', 'Subflow Fwd Bytes', 'Subflow Bwd Packets'
    ]

    # Generate synthetic data
    data = {}

    for feature in feature_names:
        if 'Packets' in feature or 'Count' in feature or 'Flags' in feature:
            # Integer features
            data[feature] = np.random.poisson(lam=5, size=n_samples)
        elif 'Length' in feature or 'Size' in feature or 'Bytes' in feature:
            # Size-related features
            data[feature] = np.random.exponential(scale=100, size=n_samples)
        elif 'Duration' in feature or 'IAT' in feature:
            # Time-related features
            data[feature] = np.random.exponential(scale=0.1, size=n_samples)
        elif 'Rate' in feature or '/s' in feature:
            # Rate features
            data[feature] = np.random.exponential(scale=1000, size=n_samples)
        elif 'Ratio' in feature:
            # Ratio features
            data[feature] = np.random.uniform(0, 1, size=n_samples)
        else:
            # General numeric features
            data[feature] = np.random.normal(loc=50, scale=15, size=n_samples)

    # Create labels (80% benign, 20% malicious)
    labels = np.random.choice(['BENIGN', 'MALICIOUS'], size=n_samples, p=[0.8, 0.2])
    data['Label'] = labels

    # Create DataFrame
    df = pd.DataFrame(data)

    # Ensure no negative values for features that shouldn't be negative
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].abs()

    print(f"✅ Generated synthetic CICIDS2017 dataset: {df.shape[0]} samples, {df.shape[1]} features")
    print(f"   Label distribution: {df['Label'].value_counts().to_dict()}")

    return df


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
