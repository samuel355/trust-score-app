#!/usr/bin/env python3
"""
Test Trust Engine configuration
"""

from app.config import Config
from app.utils import get_supabase_client

def test_trust_engine_config():
    """Test what configuration Trust Engine is using"""
    
    print("=== Trust Engine Configuration ===")
    print(f"SUPABASE_URL: {Config.SUPABASE_URL}")
    print(f"SUPABASE_API_KEY: {Config.SUPABASE_API_KEY[:20]}..." if Config.SUPABASE_API_KEY else "No key")
    
    print("\n=== Testing Supabase Client ===")
    try:
        supabase = get_supabase_client()
        print("✅ Supabase client created successfully")
        
        # Test a simple query
        result = supabase.table('TelemetryData').select('*').limit(1).execute()
        print("✅ Supabase query successful")
        
    except Exception as e:
        print(f"❌ Supabase client failed: {str(e)}")

if __name__ == "__main__":
    test_trust_engine_config() 