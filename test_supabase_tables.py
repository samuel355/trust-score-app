#!/usr/bin/env python3
"""
Check Supabase tables
"""

from app.utils import get_supabase_client

def check_supabase_tables():
    """Check what tables exist in Supabase"""
    
    try:
        supabase = get_supabase_client()
        
        # Try to list tables by querying system tables
        print("Checking Supabase tables...")
        
        # Try to query the TelemetryData table
        try:
            result = supabase.table('TelemetryData').select('*').limit(1).execute()
            print("✅ TelemetryData table exists")
        except Exception as e:
            print(f"❌ TelemetryData table error: {str(e)}")
        
        # Try to query the TrustScore table
        try:
            result = supabase.table('TrustScore').select('*').limit(1).execute()
            print("✅ TrustScore table exists")
        except Exception as e:
            print(f"❌ TrustScore table error: {str(e)}")
        
        # Try to insert a test record
        try:
            test_data = {
                'vm_id': 'test-vm',
                'vm_agent_id': 'test-agent',
                'timestamp': '2024-01-01T00:00:00Z',
                'event_type': 'test',
                'stride_category': 'Unknown',
                'risk_level': 1,
                'features': {'test': 'value'}
            }
            
            result = supabase.table('TelemetryData').insert(test_data).execute()
            print("✅ Test insert successful")
            
            # Clean up test data
            supabase.table('TelemetryData').delete().eq('vm_id', 'test-vm').execute()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"❌ Test insert failed: {str(e)}")
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")

if __name__ == "__main__":
    check_supabase_tables() 