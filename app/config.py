import os

class Config:
    # Flask Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://project-id.supabase.co')
    SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY', 'supabase-anon-key')

    # Okta Configuration
    # Replace 'your-domain' with your actual Okta domain (e.g., dev-123456, yourcompany)
    OKTA_ISSUER = os.getenv('OKTA_ISSUER', 'https://your-domain.okta.com/oauth2/default')
    OKTA_CLIENT_ID = os.getenv('OKTA_CLIENT_ID', 'okta-client-id')
    OKTA_CLIENT_SECRET = os.getenv('OKTA_CLIENT_SECRET', 'okta-client-secret')
    OKTA_REDIRECT_URI = os.getenv('OKTA_REDIRECT_URI', 'http://localhost:5001/authorization-code/callback')
    # Audience is typically your Okta application's client ID or a custom identifier
    # For most cases, using the client ID works fine
    OKTA_AUDIENCE = os.getenv('OKTA_AUDIENCE', 'api://default')

    # Elasticsearch Configuration (HTTPS enabled)
    ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'https://localhost:9200')
    ELASTICSEARCH_USERNAME = os.getenv('ELASTICSEARCH_USERNAME', 'elastic')
    ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD', 'trust-engine-elastic-password')
    ELASTICSEARCH_SSL_VERIFY = os.getenv('ELASTICSEARCH_SSL_VERIFY', 'false').lower() == 'true'
    ELASTICSEARCH_CA_CERT = os.getenv('ELASTICSEARCH_CA_CERT', 'docker/ssl/ca/ca-cert.pem')

    # Wazuh Configuration (HTTPS enabled)
    WAZUH_API_URL = os.getenv('WAZUH_API_URL', 'https://localhost:55000')
    WAZUH_API_USERNAME = os.getenv('WAZUH_API_USERNAME', 'wazuh-wui')
    WAZUH_API_PASSWORD = os.getenv('WAZUH_API_PASSWORD', 'MyS3cr37P450r.*-')
    WAZUH_SSL_VERIFY = os.getenv('WAZUH_SSL_VERIFY', 'false').lower() == 'true'

    # Flask HTTPS Configuration
    FLASK_SSL_CERT = os.getenv('FLASK_SSL_CERT', 'docker/ssl/certs/trust-engine-cert.pem')
    FLASK_SSL_KEY = os.getenv('FLASK_SSL_KEY', 'docker/ssl/private/trust-engine-key.pem')
    FLASK_USE_SSL = os.getenv('FLASK_USE_SSL', 'true').lower() == 'true'

    # Update redirect URI for HTTPS
    OKTA_REDIRECT_URI = os.getenv('OKTA_REDIRECT_URI', 'https://localhost:5001/authorization-code/callback')

    @classmethod
    def validate_credentials(cls):
        """Validate that required credentials are set"""
        missing_credentials = []

        # Check for placeholder values
        if cls.SUPABASE_URL == 'https://project-id.supabase.co':
            missing_credentials.append('SUPABASE_URL')
        if cls.SUPABASE_API_KEY == 'supabase-anon-key':
            missing_credentials.append('SUPABASE_API_KEY')
        if cls.OKTA_ISSUER == 'https://your-domain.okta.com/oauth2/default':
            missing_credentials.append('OKTA_ISSUER')
        if cls.OKTA_CLIENT_ID == 'okta-client-id':
            missing_credentials.append('OKTA_CLIENT_ID')
        if cls.OKTA_CLIENT_SECRET == 'okta-client-secret':
            missing_credentials.append('OKTA_CLIENT_SECRET')

        if missing_credentials:
            print("⚠️  WARNING: The following credentials are using placeholder values:")
            for cred in missing_credentials:
                print(f"   - {cred}")
            print("\n📝 Please update your .env file with actual credentials.")
            print("   Copy env.example to .env and fill in your values.")
            return False

        return True
