#!/usr/bin/env python3
"""
Check actual table schema in Supabase
"""

from app.utils import get_supabase_client

def check_table_schema():
    """Check the actual schema of tables"""
    
    try:
        supabase = get_supabase_client()
        
        print("Checking actual table schemas...")
        
        # Try to get table info by attempting different column combinations
        test_columns = [
            ['id'],
            ['vm_id'],
            ['vm_agent_id'],
            ['timestamp'],
            ['event_type'],
            ['stride_category'],
            ['risk_level'],
            ['features'],
            ['session_id'],
            ['trust_score'],
            ['mfa_required']
        ]
        
        print("\n=== TelemetryData Table ===")
        for columns in test_columns:
            try:
                result = supabase.table('TelemetryData').select(','.join(columns)).limit(1).execute()
                print(f"✅ Columns {columns} exist")
            except Exception as e:
                print(f"❌ Columns {columns} don't exist: {str(e)}")
        
        print("\n=== TrustScore Table ===")
        for columns in test_columns:
            try:
                result = supabase.table('TrustScore').select(','.join(columns)).limit(1).execute()
                print(f"✅ Columns {columns} exist")
            except Exception as e:
                print(f"❌ Columns {columns} don't exist: {str(e)}")
        
        # Try a minimal insert to see what works
        print("\n=== Testing Minimal Insert ===")
        try:
            minimal_data = {
                'vm_id': 'test-vm',
                'timestamp': '2024-01-01T00:00:00Z'
            }
            result = supabase.table('TelemetryData').insert(minimal_data).execute()
            print("✅ Minimal insert successful")
            
            # Clean up
            supabase.table('TelemetryData').delete().eq('vm_id', 'test-vm').execute()
            print("✅ Cleanup successful")
            
        except Exception as e:
            print(f"❌ Minimal insert failed: {str(e)}")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")

if __name__ == "__main__":
    check_table_schema() 