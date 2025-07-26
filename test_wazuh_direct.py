#!/usr/bin/env python3
"""
Test Wazuh API connection directly
"""

import requests
import urllib3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_wazuh_connection():
    """Test Wazuh connection using the same method as Trust Engine"""
    
    # Get credentials from environment
    wazuh_url = os.getenv('WAZUH_API_URL', 'https://localhost:55000')
    wazuh_username = os.getenv('WAZUH_API_USERNAME', 'wazuh-wui')
    wazuh_password = os.getenv('WAZUH_API_PASSWORD', 'MyS3cr37P450r.*-')
    
    print(f"Testing Wazuh connection:")
    print(f"URL: {wazuh_url}")
    print(f"Username: {wazuh_username}")
    print(f"Password: {'*' * len(wazuh_password)}")
    print("-" * 50)
    
    try:
        session = requests.Session()
        
        auth_url = f"{wazuh_url}/security/user/authenticate"
        auth_data = {
            'username': wazuh_username,
            'password': wazuh_password
        }
        
        print(f"Making request to: {auth_url}")
        print(f"Using Basic Authentication with username: {wazuh_username}")
        
        # Use Basic Authentication with GET request (not POST with JSON)
        response = session.get(auth_url, auth=(wazuh_username, wazuh_password), verify=False)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Wazuh authentication successful!")
            return True
        else:
            print(f"❌ FAILED: Wazuh authentication failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_wazuh_connection() 