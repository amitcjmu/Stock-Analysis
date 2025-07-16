#!/bin/bash

# Fix Frontend NPM Container Issues
# This script addresses npm null path errors in the frontend Docker container

set -e

echo "🔧 Starting Frontend NPM Container Fix..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Stop and remove existing frontend container
print_status "Stopping existing frontend container..."
docker-compose stop frontend || true
docker-compose rm -f frontend || true

# Step 2: Remove any existing volumes that might cause conflicts
print_status "Cleaning up existing volumes..."
docker volume rm migrate-ui-orchestrator_frontend_node_modules || true

# Step 3: Remove any host node_modules that might cause conflicts
if [ -d "node_modules" ]; then
    print_warning "Found existing node_modules directory, backing up..."
    if [ -d "node_modules.backup" ]; then
        rm -rf node_modules.backup
    fi
    mv node_modules node_modules.backup
    print_status "Backed up node_modules to node_modules.backup"
fi

# Step 4: Clean npm cache on host (if any)
if command -v npm &> /dev/null; then
    print_status "Cleaning local npm cache..."
    npm cache clean --force || true
fi

# Step 5: Remove any existing docker images to force rebuild
print_status "Removing existing frontend Docker image..."
docker rmi migrate-ui-orchestrator-frontend || true

# Step 6: Build fresh frontend image
print_status "Building fresh frontend container..."
docker-compose build --no-cache frontend

# Step 7: Start the frontend service
print_status "Starting frontend service..."
docker-compose up -d frontend

# Step 8: Wait for container to be ready and check logs
print_status "Waiting for frontend container to start..."
sleep 10

# Step 9: Check if container is running
if docker ps | grep -q "migration_frontend"; then
    print_status "✅ Frontend container is running successfully!"
    
    # Show recent logs
    print_status "Recent frontend container logs:"
    docker-compose logs --tail=20 frontend
    
    print_status "🎉 Frontend NPM fix completed successfully!"
    print_status "You can now access the application at: http://localhost:8081"
else
    print_error "❌ Frontend container failed to start. Checking logs..."
    docker-compose logs frontend
    
    print_error "Frontend container failed to start. Please check the logs above."
    exit 1
fi

# Step 10: Cleanup old backup if everything works
if [ -d "node_modules.backup" ]; then
    print_status "Removing old node_modules backup..."
    rm -rf node_modules.backup
fi

print_status "🔧 Frontend NPM container fix completed!"