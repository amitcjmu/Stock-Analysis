#!/usr/bin/env python3
"""
Setup script for AI Modernize Migration Platform backend.
Handles database initialization, environment setup, and development tools.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import init_db


async def create_database_tables():
    """Create all database tables."""
    print("🔧 Creating database tables...")
    try:
        await init_db()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
    return True


def check_environment():
    """Check if environment is properly configured."""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        "DATABASE_URL",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("📝 Please copy env.example to .env and configure the missing variables")
        return False
    
    print("✅ Environment configuration looks good!")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, cwd=backend_dir)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def create_env_file():
    """Create .env file from example if it doesn't exist."""
    env_file = backend_dir / ".env"
    env_example = backend_dir / "env.example"
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from example...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created! Please update it with your configuration.")
        return True
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ No env.example file found")
        return False


async def test_database_connection():
    """Test database connectivity."""
    print("🔌 Testing database connection...")
    try:
        from app.core.database import db_manager
        is_healthy = await db_manager.health_check()
        if is_healthy:
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup completed! Next steps:")
    print("1. Update your .env file with proper configuration")
    print("2. Ensure PostgreSQL is running locally (or configure Railway database)")
    print("3. Start the development server:")
    print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("\n📚 Useful commands:")
    print("   - API Documentation: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    print("   - WebSocket Test: ws://localhost:8000/ws/test-client")


async def main():
    """Main setup function."""
    print("🚀 AI Modernize Migration Platform - Backend Setup")
    print("=" * 50)
    
    # Step 1: Create .env file
    if not create_env_file():
        return
    
    # Step 2: Install dependencies
    if not install_dependencies():
        return
    
    # Step 3: Check environment
    if not check_environment():
        return
    
    # Step 4: Test database connection
    if not await test_database_connection():
        print("⚠️  Database connection failed. Please check your DATABASE_URL configuration.")
        print("   For local development, ensure PostgreSQL is running.")
        print("   For Railway deployment, the DATABASE_URL will be provided automatically.")
    
    # Step 5: Create database tables
    if await test_database_connection():
        await create_database_tables()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    asyncio.run(main()) 