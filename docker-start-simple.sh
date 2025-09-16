#!/bin/bash

# Simple Docker Start Script for SSL-restricted environments
# This script uses simplified Dockerfiles that bypass SSL verification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root directory
cd "$(dirname "$0")"

echo "🚀 Starting AI Modernize Migration Platform (SSL Bypass Mode)..."
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running or you don't have permission.${NC}"
        echo -e "${YELLOW}💡 Try running with: sudo $0${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to check environment file
check_env_file() {
    if [ ! -f "backend/.env" ]; then
        echo -e "${YELLOW}⚠️  No backend/.env file found. Creating from template...${NC}"
        cat > backend/.env << 'EOF'
# Minimal environment configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-here-change-in-production
ENVIRONMENT=development
DEBUG=true

# Add your API keys here
# OPENAI_API_KEY=your-key-here
# ANTHROPIC_API_KEY=your-key-here
# DEEPINFRA_API_KEY=your-key-here
EOF
        echo -e "${GREEN}✅ Created minimal backend/.env file${NC}"
        echo -e "${YELLOW}   Please add your API keys to backend/.env${NC}"
    else
        echo -e "${GREEN}✅ backend/.env file exists${NC}"
    fi
}

# Main execution
echo "🔍 Running pre-flight checks..."
echo ""

check_docker
check_env_file

echo ""
echo "🔧 Stopping any existing containers..."
docker-compose -f config/docker/docker-compose.simple.yml down 2>/dev/null || true

echo ""
echo "📦 Building and starting services (SSL bypass mode)..."
echo -e "${YELLOW}Note: This may take a while on first run as it builds the containers${NC}"
echo ""

# Start the services using the simplified config
if docker-compose -f config/docker/docker-compose.simple.yml up -d --build; then
    echo ""
    echo -e "${GREEN}✅ Services started successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Failed to start services. Checking logs...${NC}"
    docker-compose -f config/docker/docker-compose.simple.yml logs --tail=50
    exit 1
fi

# Wait a moment for services to initialize
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

echo ""
echo "📊 Service Status:"
docker-compose -f config/docker/docker-compose.simple.yml ps

# Check if all services are running
if docker-compose -f config/docker/docker-compose.simple.yml ps | grep -q "Exit\|exited"; then
    echo ""
    echo -e "${RED}❌ Some services failed to start. Checking logs...${NC}"
    docker-compose -f config/docker/docker-compose.simple.yml logs --tail=50
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
    echo "  1. Check if ports 8000, 8081, 5433, 6379 are already in use"
    echo "  2. Run: docker-compose -f config/docker/docker-compose.simple.yml logs -f [service]"
    echo "  3. Try: docker-compose -f config/docker/docker-compose.simple.yml down -v"
    echo "  4. Then try running this script again"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All services are running!${NC}"
echo ""
echo "📋 Available commands:"
echo "  • View logs: docker-compose -f config/docker/docker-compose.simple.yml logs -f [service]"
echo "  • Stop services: docker-compose -f config/docker/docker-compose.simple.yml down"
echo "  • View status: docker-compose -f config/docker/docker-compose.simple.yml ps"
echo ""
echo "🌐 Access your application:"
echo "  • Frontend: http://localhost:8081"
echo "  • Backend API: http://localhost:8000/docs"
echo "  • Database: localhost:5433 (user: postgres, password: postgres)"
echo "  • Redis: localhost:6379"
echo ""
echo -e "${YELLOW}⚠️  Note: Running in SSL bypass mode for restricted networks${NC}"
echo -e "${GREEN}Happy coding! 🚀${NC}"