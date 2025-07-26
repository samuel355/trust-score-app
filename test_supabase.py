#!/usr/bin/env python3
"""
Test Supabase connection
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection"""
    
    # Get credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_API_KEY')
    
    print(f"Testing Supabase connection:")
    print(f"URL: {supabase_url}")
    print(f"Key: {supabase_key[:20]}..." if supabase_key else "No key found")
    print("-" * 50)
    
    try:
        # Try with current URL format
        print("Attempting connection with current URL format...")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test a simple query
        result = supabase.table('TelemetryData').select('*').limit(1).execute()
        print("✅ SUCCESS: Supabase connection working!")
        print(f"Query result: {len(result.data)} rows")
        return True
        
    except Exception as e:
        print(f"❌ FAILED with current URL: {str(e)}")
        
        # Try with alternative URL format
        try:
            print("\nTrying with alternative URL format...")
            # Extract project ID from the PostgreSQL URL
            if 'postgresql://' in supabase_url:
                # Convert PostgreSQL URL to Supabase URL
                # Extract project ID from: postgresql://postgres:password@db.project-id.supabase.co:5432/postgres
                parts = supabase_url.split('@')
                if len(parts) > 1:
                    db_part = parts[1].split('.')
                    if len(db_part) > 2:
                        project_id = db_part[1]  # Extract project ID
                        supabase_url_alt = f"https://{project_id}.supabase.co"
                        print(f"Alternative URL: {supabase_url_alt}")
                        
                        supabase: Client = create_client(supabase_url_alt, supabase_key)
                        result = supabase.table('TelemetryData').select('*').limit(1).execute()
                        print("✅ SUCCESS: Supabase connection working with alternative URL!")
                        print(f"Query result: {len(result.data)} rows")
                        return True
                        
        except Exception as e2:
            print(f"❌ FAILED with alternative URL: {str(e2)}")
        
        return False

if __name__ == "__main__":
    test_supabase_connection() 