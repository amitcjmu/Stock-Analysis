#!/bin/bash

# AI Force Migration Platform - Railway Startup Script
# This script handles environment variable expansion for Railway deployment

echo "🚀 Starting AI Force Migration Platform API..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"
echo "Debug: ${DEBUG:-false}"

# Use Railway's PORT environment variable or default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT 