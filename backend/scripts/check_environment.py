#!/usr/bin/env python3
"""
Check environment configuration and CORS settings
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from main import get_cors_origins


def check_environment():
    """Check environment configuration"""
    print("🔍 Environment Configuration Check")
    print("=" * 50)

    # Check environment variables
    print("\n📋 Environment Variables:")
    print(f"   ENVIRONMENT (from env): {os.getenv('ENVIRONMENT', 'NOT SET')}")
    print(f"   RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT SET')}")
    print(f"   PORT: {os.getenv('PORT', 'NOT SET')}")
    print(f"   DATABASE_URL present: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")

    # Check settings
    print("\n⚙️  Settings Configuration:")
    print(f"   ENVIRONMENT (from settings): {settings.ENVIRONMENT}")
    print(f"   FRONTEND_URL: {settings.FRONTEND_URL}")
    print(f"   ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
    print(f"   DEBUG: {settings.DEBUG}")

    # Check if .env file exists
    env_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )
    print(f"\n📄 .env file exists: {'Yes' if os.path.exists(env_file_path) else 'No'}")

    # Check CORS origins
    print("\n🌐 CORS Origins:")
    cors_origins = get_cors_origins()
    for i, origin in enumerate(cors_origins):
        print(f"   {i+1}. {origin}")

    # Check if Vercel domain is included
    vercel_domain = "https://aiforce-assess.vercel.app"
    if vercel_domain in cors_origins:
        print("\n✅ Vercel domain IS included in CORS origins")
    else:
        print("\n❌ Vercel domain NOT included in CORS origins")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    check_environment()
