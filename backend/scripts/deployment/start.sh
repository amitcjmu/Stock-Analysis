#!/bin/bash

# AI Force Migration Platform - Railway Startup Script
# This script handles environment variable expansion for Railway deployment

echo "🚀 Starting AI Force Migration Platform API..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"
echo "Debug: ${DEBUG:-false}"

# --- Run Database Migrations ---
echo "🚂 Running database migrations..."
python -m alembic upgrade head
MIGRATION_STATUS=$? # Capture exit code

if [ $MIGRATION_STATUS -eq 0 ]; then
    echo "✅ Database migrations completed successfully."
else
    echo "⚠️ Database migration failed with exit code $MIGRATION_STATUS. The application might not function correctly."
    # We won't exit here, to allow for inspection of a running container if needed.
fi
# --- Migrations End ---


# Use Railway's PORT environment variable or default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT 