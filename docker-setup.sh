#!/bin/bash

# Docker Setup Script for AI Force Migration Platform
# This script helps with Docker authentication and container management

echo "🐳 AI Force Migration Platform - Docker Setup"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check Docker Hub authentication
echo "🔐 Checking Docker Hub authentication..."
if docker pull hello-world > /dev/null 2>&1; then
    echo "✅ Docker Hub authentication is working"
    docker rmi hello-world > /dev/null 2>&1
else
    echo "❌ Docker Hub authentication failed"
    echo ""
    echo "To fix this, please run:"
    echo "  docker login"
    echo ""
    echo "Or if you don't have a Docker Hub account:"
    echo "  1. Create a free account at https://hub.docker.com"
    echo "  2. Run 'docker login' with your credentials"
    echo ""
    read -p "Would you like to login now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login
    else
        echo "Please login to Docker Hub and run this script again."
        exit 1
    fi
fi

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No process on port 8000"
lsof -ti:8081 | xargs kill -9 2>/dev/null || echo "No process on port 8081"
lsof -ti:5432 | xargs kill -9 2>/dev/null || echo "No process on port 5432"

# Stop and remove existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || echo "No existing containers to stop"

# Build the containers
echo "🔨 Building containers..."
if docker-compose build --no-cache; then
    echo "✅ Containers built successfully"
else
    echo "❌ Container build failed"
    exit 1
fi

# Start the services
echo "🚀 Starting services..."
if docker-compose up -d; then
    echo "✅ Services started successfully"
    
    echo ""
    echo "🌐 Access URLs:"
    echo "   - Frontend: http://localhost:8081"
    echo "   - Backend API: http://localhost:8000"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - PostgreSQL: localhost:5432"
    echo ""
    echo "📊 Container Status:"
    docker-compose ps
    echo ""
    echo "📝 To view logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 To stop services:"
    echo "   docker-compose down"
    
else
    echo "❌ Failed to start services"
    echo "📝 Check logs with: docker-compose logs"
    exit 1
fi 