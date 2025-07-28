#!/usr/bin/env python3
"""
ML Blueprint Registration Script
Registers the ML API blueprint after app initialization to avoid circular imports
"""

from app import app
from routes.ml_endpoints import ml_bp

def register_ml_blueprint():
    """Register the ML API blueprint with the Flask app"""
    try:
        app.register_blueprint(ml_bp)
        print("✅ ML API blueprint registered successfully")
        print(f"   Blueprint name: {ml_bp.name}")
        print(f"   URL prefix: {ml_bp.url_prefix}")

        # List available ML endpoints
        ml_endpoints = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('ml_api.'):
                ml_endpoints.append(f"{rule.methods} {rule.rule}")

        if ml_endpoints:
            print(f"   Available ML endpoints: {len(ml_endpoints)}")
            for endpoint in ml_endpoints[:5]:  # Show first 5
                print(f"     - {endpoint}")
            if len(ml_endpoints) > 5:
                print(f"     ... and {len(ml_endpoints) - 5} more")

        return True

    except Exception as e:
        print(f"❌ Failed to register ML blueprint: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Trust Engine ML Blueprint Registration")
    print("=" * 50)

    success = register_ml_blueprint()

    if success:
        print("\n🎉 ML API is ready!")
        print("You can now use all ML endpoints in your Flask application.")
        print("\nExample endpoints:")
        print("  - GET  /api/ml/health")
        print("  - POST /api/ml/train")
        print("  - POST /api/ml/predict")
        print("  - GET  /api/ml/evaluate")
    else:
        print("\n❌ ML API registration failed!")
        print("Check the error messages above and fix any issues.")

    print("=" * 50)
