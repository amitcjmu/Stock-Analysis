#!/usr/bin/env python3
"""
AI Modernize Migration Platform - Railway Startup Script
This script handles environment variable expansion and starts the FastAPI server.
"""

import os
import subprocess
import sys


def run_migrations():
    """Run database migrations before starting the app."""
    print("🔄 Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=300,  # Increase timeout to 5 minutes
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            if result.stdout:
                print(f"Migration output: {result.stdout}")
            return True
        else:
            print(f"❌ Migration failed with code {result.returncode}")
            print(f"Error: {result.stderr}")
            print(f"Output: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Exception running migrations: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Start the FastAPI application with proper environment handling."""
    print("🚀 Starting AI Modernize Migration Platform API...")

    # Migrations are handled by entrypoint.sh/railway_setup.py
    print("📋 Database migrations handled by deployment scripts")

    # Get environment variables
    environment = os.getenv("ENVIRONMENT", "production")
    port = os.getenv("PORT", "8000")
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Environment: {environment}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")

    # Validate port is a number
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValueError("Port must be between 1 and 65535")
    except ValueError as e:
        print(f"❌ Invalid port '{port}': {e}")
        sys.exit(1)

    # Build uvicorn command
    cmd = ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port_int)]

    # Add reload flag for development
    if debug and environment == "development":
        cmd.append("--reload")

    print(f"Starting uvicorn on port {port}...")
    print(f"Command: {' '.join(cmd)}")

    # Execute uvicorn
    try:
        os.execvp(cmd[0], cmd)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
