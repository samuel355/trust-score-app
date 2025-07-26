from app import app
from app.config import Config

if __name__ == '__main__':
    # Validate credentials on startup
    print("🔐 Trust Engine Starting...")
    print("=" * 50)
    
    # Check if credentials are properly configured
    if not Config.validate_credentials():
        print("\n🚨 CRITICAL: Please configure your credentials before running the application!")
        print("📋 Steps to fix:")
        print("   1. Copy env.example to .env")
        print("   2. Fill in your actual credentials in .env")
        print("   3. Restart the application")
        print("\n💡 For Okta setup, see: docs/okta_setup.md")
        print("💡 For Supabase setup, see: app/supabase_schema.md")
        print("=" * 50)
        
        # Still run the app but warn user
        print("⚠️  Running with placeholder credentials - some features may not work!")
    
    print("🚀 Starting Trust Engine on http://localhost:5001")
    print("📖 API Documentation: http://localhost:5001/")
    print("🔑 Login: http://localhost:5001/auth/login")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=True) 