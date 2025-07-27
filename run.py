from app import app
from app.config import Config
import os
import ssl

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

    # HTTPS Configuration
    if Config.FLASK_USE_SSL:
        ssl_cert = Config.FLASK_SSL_CERT
        ssl_key = Config.FLASK_SSL_KEY

        # Check if SSL certificates exist
        if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
            print("🔒 Starting Trust Engine with HTTPS on https://localhost:5001")
            print("📖 API Documentation: https://localhost:5001/")
            print("🔑 Login: https://localhost:5001/auth/login")
            print("🛡️  SSL Certificates: ✓ Found")
            print("=" * 50)

            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(ssl_cert, ssl_key)

            # Run with HTTPS
            app.run(
                host='0.0.0.0',
                port=5001,
                debug=Config.DEBUG,
                ssl_context=context
            )
        else:
            print(f"❌ SSL certificates not found:")
            print(f"   Certificate: {ssl_cert}")
            print(f"   Private Key: {ssl_key}")
            print("\n🔧 To generate SSL certificates, run:")
            print("   cd docker/ssl && ./generate_certificates.sh")
            print("\n⚠️  Falling back to HTTP mode...")
            print("🌐 Starting Trust Engine on http://localhost:5001")
            print("📖 API Documentation: http://localhost:5001/")
            print("🔑 Login: http://localhost:5001/auth/login")
            print("=" * 50)

            # Fall back to HTTP
            app.run(host='0.0.0.0', port=5001, debug=Config.DEBUG)
    else:
        print("🌐 Starting Trust Engine on http://localhost:5001")
        print("📖 API Documentation: http://localhost:5001/")
        print("🔑 Login: http://localhost:5001/auth/login")
        print("=" * 50)

        # Run with HTTP
        app.run(host='0.0.0.0', port=5001, debug=Config.DEBUG)
