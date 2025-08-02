#!/bin/bash

# Docker test runner for AI Modernize Migration Platform Backend
# This script starts the backend with test environment variables

set -e

echo "Starting AI Modernize Migration Platform Backend in Docker..."

# Create minimal test environment
cat > .env.docker <<EOF
# Minimal test configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=test-secret-key-for-docker-environment-32-chars-long
JWT_SECRET_KEY=test-jwt-secret-key-for-docker-environment-32-chars

# Demo data for testing
DEMO_DATA=true
DEMO_CLIENT_NAME=Docker Test Corp
DEMO_ENGAGEMENT_NAME=Docker Test Engagement

# Database (connecting to existing migration_postgres container)
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5433/migration_db

# AI Configuration (mock for testing)
DEEPINFRA_API_KEY=test-key
OPENAI_API_KEY=test-key
DEEPINFRA_MODEL=meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8

# CORS settings
FRONTEND_URL=http://localhost:8081
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8081

# Redis configuration (optional for testing)
REDIS_URL=redis://host.docker.internal:6379/0

# Performance settings
LOG_LEVEL=INFO
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
EOF

# Stop any existing container
docker stop migrate-backend-test 2>/dev/null || true
docker rm migrate-backend-test 2>/dev/null || true

echo "Starting Docker container..."

# Run the container with test environment
docker run -d \
  --name migrate-backend-test \
  --env-file .env.docker \
  -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  migrate-ui-orchestrator-backend:latest

echo "Container started successfully!"
echo "Backend will be available at: http://localhost:8000"
echo "Health check: curl http://localhost:8000/health"
echo ""
echo "To view logs, use: docker logs -f migrate-backend-test"
echo "To stop the container: docker stop migrate-backend-test"

# Wait a moment and show initial logs
sleep 3
echo ""
echo "Initial container logs:"
docker logs migrate-backend-test --tail 20
