#!/bin/bash

# Docker Stop Helper Script
# This script stops the application using the organized config structure

set -e

# Change to project root directory
cd "$(dirname "$0")"

echo "🛑 Stopping AI Modernize Migration Platform services..."
echo "Using docker-compose.yml from: config/docker/docker-compose.yml"
echo ""

# Stop the services using the config from organized location
docker-compose -f config/docker/docker-compose.yml down "$@"

echo ""
echo "✅ Services stopped successfully!"
