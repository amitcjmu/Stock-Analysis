#!/bin/bash

# Docker Start Helper Script with Validation
# This script starts the application using the organized config structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root directory
cd "$(dirname "$0")"

echo "🚀 Starting AI Modernize Migration Platform..."
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker Desktop first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to check required files
check_required_files() {
    local missing_files=()

    # Check for essential files
    local required_files=(
        "config/docker/docker-compose.yml"
        "config/docker/Dockerfile.backend"
        "config/docker/Dockerfile.frontend"
        "backend/init.sql"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done

    if [ ${#missing_files[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required files:${NC}"
        for file in "${missing_files[@]}"; do
            echo "   - $file"
        done
        exit 1
    fi
    echo -e "${GREEN}✅ All required files present${NC}"
}

# Function to check environment file
check_env_file() {
    if [ ! -f "backend/.env" ]; then
        echo -e "${YELLOW}⚠️  No backend/.env file found. Creating from template...${NC}"
        if [ -f "backend/.env.example" ] || [ -f "backend/.env.template" ]; then
            cp backend/.env.example backend/.env 2>/dev/null || cp backend/.env.template backend/.env 2>/dev/null
            echo -e "${GREEN}✅ Created backend/.env from template${NC}"
        else
            echo -e "${YELLOW}⚠️  Creating minimal backend/.env file...${NC}"
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
        fi
    else
        echo -e "${GREEN}✅ backend/.env file exists${NC}"
    fi
}

# Function to clean up any problematic state
cleanup_if_needed() {
    # Check if there are any stopped containers
    stopped_containers=$(docker ps -aq -f "name=migration_" -f "status=exited" 2>/dev/null || true)
    if [ ! -z "$stopped_containers" ]; then
        echo -e "${YELLOW}⚠️  Cleaning up stopped containers...${NC}"
        docker rm $stopped_containers >/dev/null 2>&1 || true
    fi
}

# Function to ensure the symlink for init.sql exists (for override compatibility)
ensure_init_sql_link() {
    if [ ! -f "config/docker/backend/init.sql" ] && [ -f "backend/init.sql" ]; then
        echo -e "${YELLOW}⚠️  Creating symlink for init.sql compatibility...${NC}"
        mkdir -p config/docker/backend
        ln -sf ../../../backend/init.sql config/docker/backend/init.sql
        echo -e "${GREEN}✅ Symlink created${NC}"
    fi
}

# Main execution
echo "🔍 Running pre-flight checks..."
echo ""

check_docker
check_required_files
check_env_file
cleanup_if_needed
ensure_init_sql_link

echo ""
echo "📦 Starting services..."
echo ""

# Start the services using the config from organized location
if docker-compose -f config/docker/docker-compose.yml up -d "$@"; then
    echo ""
    echo -e "${GREEN}✅ Services started successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Failed to start services. Checking logs...${NC}"
    docker-compose -f config/docker/docker-compose.yml logs --tail=50
    exit 1
fi

# Wait a moment for services to initialize
sleep 3

echo ""
echo "📊 Service Status:"
docker-compose -f config/docker/docker-compose.yml ps

# Check if all services are running
if docker-compose -f config/docker/docker-compose.yml ps | grep -q "Exit\|exited"; then
    echo ""
    echo -e "${RED}❌ Some services failed to start. Checking logs...${NC}"
    docker-compose -f config/docker/docker-compose.yml logs --tail=50
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
    echo "  1. Check if ports 8000, 8081, 5433, 6379 are already in use"
    echo "  2. Run: docker-compose -f config/docker/docker-compose.yml down -v"
    echo "  3. Then try running this script again"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All services are running!${NC}"
echo ""
echo "📋 Available commands:"
echo "  • View logs: docker-compose -f config/docker/docker-compose.yml logs -f [service]"
echo "  • Stop services: ./docker-stop.sh"
echo "  • View status: docker-compose -f config/docker/docker-compose.yml ps"
echo ""
echo "🌐 Access your application:"
echo "  • Frontend: http://localhost:8081"
echo "  • Backend API: http://localhost:8000/docs"
echo "  • Database: localhost:5433 (user: postgres, password: postgres)"
echo "  • Redis: localhost:6379"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
