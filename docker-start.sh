#!/bin/bash

# Docker Start Helper Script
# This script starts the application using the organized config structure

set -e

# Change to project root directory
cd "$(dirname "$0")"

echo "🚀 Starting AI Modernize Migration Platform with organized config structure..."
echo "Using docker-compose.yml from: config/docker/docker-compose.yml"
echo ""

# Start the services using the config from organized location
docker-compose -f config/docker/docker-compose.yml up -d "$@"

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service Status:"
docker-compose -f config/docker/docker-compose.yml ps

echo ""
echo "📋 Available commands:"
echo "  • View logs: docker-compose -f config/docker/docker-compose.yml logs -f [service]"
echo "  • Stop services: docker-compose -f config/docker/docker-compose.yml down"
echo "  • View status: docker-compose -f config/docker/docker-compose.yml ps"
echo ""
echo "🌐 Frontend: http://localhost:8081"
echo "🔧 Backend API: http://localhost:8000"
echo "🗄️  Database: localhost:5433"
