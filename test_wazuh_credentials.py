#!/usr/bin/env python3
"""
Simple script to test Wazuh credentials
"""

import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_wazuh_credentials(username, password, url="https://localhost:55000"):
    """Test Wazuh credentials"""
    try:
        auth_url = f"{url}/security/user/authenticate"
        auth_data = {
            'username': username,
            'password': password
        }
        
        response = requests.post(auth_url, json=auth_data, verify=False)
        
        if response.status_code == 200:
            print(f"✅ SUCCESS: {username}:{password}")
            return True
        else:
            print(f"❌ FAILED: {username}:{password} - {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {username}:{password} - {str(e)}")
        return False

def main():
    """Test common Wazuh credential combinations"""
    print("🔍 Testing Wazuh credentials...")
    print("=" * 50)
    
    # Common credential combinations
    credentials = [
        ("admin", "admin"),
        ("admin", "SecretPassword"),
        ("wazuh", "wazuh"),
        ("wazuh", "MyS3cureP4ssw0rd"),
        ("admin", "wazuh"),
        ("wazuh", "admin"),
        ("admin", "password"),
        ("admin", "123456"),
    ]
    
    success = False
    for username, password in credentials:
        if test_wazuh_credentials(username, password):
            success = True
            break
    
    if not success:
        print("\n❌ No credentials worked!")
        print("💡 Please check your Wazuh Docker setup and provide the correct credentials.")
        print("💡 You can also check the Wazuh documentation for default credentials.")

if __name__ == "__main__":
    main() 