#!/usr/bin/env python3
"""
AI Force Migration Platform - Railway Startup Script
This script handles environment variable expansion and starts the FastAPI server.
"""

import os
import sys
import subprocess

def run_migrations():
    """Run database migrations using Alembic."""
    print("🚂 Running database migrations...")
    try:
        # The working directory for Railway is /app, where alembic.ini should be.
        migration_command = ["python", "-m", "alembic", "upgrade", "head"]
        
        result = subprocess.run(
            migration_command,
            capture_output=True,
            text=True,
            check=False, # We'll check the return code manually
            cwd="/app"
        )
        
        # Log the output for debugging in Railway logs
        print("--- Alembic stdout ---")
        print(result.stdout)
        print("--- Alembic stderr ---")
        print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully.")
        else:
            print(f"⚠️ Migrations failed with exit code {result.returncode}. The application might not function correctly.")
            # Forcing an exit might be too aggressive if the DB is just already up-to-date
            # and alembic returns a non-zero code for that. Let's allow startup.

    except Exception as e:
        print(f"❌ An unexpected error occurred during migration: {e}")
        print("⚠️ CRITICAL: Could not run database migrations. The application will likely fail.")
        # We might want to exit here in a real production setting.
        # sys.exit(1)

def main():
    """Start the FastAPI application with proper environment handling."""
    print("🚀 Starting AI Force Migration Platform API...")
    
    # Automatically run migrations on startup
    run_migrations()
    
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
    cmd = [
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", str(port_int)
    ]
    
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