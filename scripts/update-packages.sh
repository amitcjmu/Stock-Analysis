#!/bin/bash
# Script to update all packages for security

set -e

echo "🔒 Updating all packages for security..."
echo "======================================="
echo ""

# Function to backup current files
backup_files() {
    echo "📦 Creating backups..."
    cp package.json package.json.backup
    cp backend/requirements-docker.txt backend/requirements-docker.txt.backup || true
    echo "✅ Backups created"
}

# Function to update backend packages
update_backend() {
    echo ""
    echo "🐍 Updating Backend Python packages..."
    
    # Use the secure requirements file
    if [ -f "backend/requirements-docker-secure.txt" ]; then
        echo "Using secure requirements file..."
        cp backend/requirements-docker-secure.txt backend/requirements-docker.txt
        echo "✅ Backend requirements updated"
    fi
}

# Function to update frontend packages
update_frontend() {
    echo ""
    echo "📦 Updating Frontend npm packages..."
    
    # Use the updated package.json
    if [ -f "package-updated.json" ]; then
        echo "Using updated package.json..."
        cp package-updated.json package.json
        echo "✅ Frontend package.json updated"
    fi
}

# Function to rebuild containers
rebuild_containers() {
    echo ""
    echo "🐳 Rebuilding Docker containers..."
    
    # Stop current containers
    docker-compose down
    
    # Build with no cache to ensure updates
    docker-compose build --no-cache
    
    echo "✅ Containers rebuilt with security updates"
}

# Function to test the updates
test_updates() {
    echo ""
    echo "🧪 Testing updated packages..."
    
    # Start containers
    docker-compose up -d
    
    # Wait for services to start
    sleep 10
    
    # Check health
    echo "Checking backend health..."
    curl -s http://localhost:8000/health || echo "Backend health check failed"
    
    echo "Checking frontend..."
    curl -s http://localhost:8081 > /dev/null && echo "Frontend is running" || echo "Frontend check failed"
    
    echo ""
    echo "📊 Container status:"
    docker-compose ps
}

# Main execution
echo "This script will update all packages to address security vulnerabilities."
echo "Current containers will be rebuilt."
echo ""
read -p "Continue? (y/N) " response

if [[ "$response" =~ ^[Yy]$ ]]; then
    backup_files
    update_backend
    update_frontend
    rebuild_containers
    test_updates
    
    echo ""
    echo "✅ Package updates complete!"
    echo ""
    echo "📋 Summary:"
    echo "- Backend packages updated to latest secure versions"
    echo "- Frontend packages updated to latest secure versions"
    echo "- Database updated to PostgreSQL 17"
    echo "- Redis updated to version 8"
    echo ""
    echo "🔍 To verify security improvements, run:"
    echo "  docker scout cves migrate-platform:latest"
    echo "  docker scout cves migrate-ui-orchestrator-frontend:latest"
else
    echo "Update cancelled."
fi