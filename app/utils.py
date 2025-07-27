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
    """Load sample CICIDS2017 data from JSON file for testing"""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_cicids2017_data.json')
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Sample data file not found at {file_path}")
        return None


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
