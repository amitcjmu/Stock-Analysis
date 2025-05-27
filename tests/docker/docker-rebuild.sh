#!/bin/bash

echo "🐳 Rebuilding Docker containers to sync code changes..."

# Stop all containers
echo "📦 Stopping existing containers..."
docker-compose down

# Remove existing containers and images to force rebuild
echo "🗑️  Removing existing containers and images..."
docker-compose rm -f
docker rmi migrate-ui-orchestrator-backend 2>/dev/null || true
docker rmi migrate-ui-orchestrator-frontend 2>/dev/null || true

# Clean up any dangling images
echo "🧹 Cleaning up dangling images..."
docker image prune -f

# Rebuild and start containers
echo "🔨 Rebuilding containers with latest code..."
docker-compose build --no-cache

echo "🚀 Starting containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check container status
echo "📊 Container status:"
docker-compose ps

echo ""
echo "✅ Docker rebuild complete!"
echo "🌐 Frontend: http://localhost:8081"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 Backend Health: http://localhost:8000/health"
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f frontend" 