#!/usr/bin/env python3
"""
Test Supabase connection using Trust Engine's method
"""

from app.utils import get_supabase_client
from app.config import Config

def test_trust_engine_supabase():
    """Test Supabase connection using Trust Engine's method"""
    
    print(f"Testing Trust Engine Supabase connection:")
    print(f"Config URL: {Config.SUPABASE_URL}")
    print(f"Config Key: {Config.SUPABASE_API_KEY[:20]}..." if Config.SUPABASE_API_KEY else "No key found")
    print("-" * 50)
    
    try:
        # Use the same method as Trust Engine
        supabase = get_supabase_client()
        
        # Test a simple query
        result = supabase.table('TelemetryData').select('*').limit(1).execute()
        print("✅ SUCCESS: Trust Engine Supabase connection working!")
        print(f"Query result: {len(result.data)} rows")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    test_trust_engine_supabase() 