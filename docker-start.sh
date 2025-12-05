#!/bin/bash

# Docker Start Helper Script with Validation
# This script starts the application using the organized config structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root directory
cd "$(dirname "$0")"

echo "🚀 Starting AI Modernize Migration Platform..."
echo ""

# Parse command line arguments
INCLUDE_OBSERVABILITY=false
FORCE_REBUILD=false
NO_CACHE=false

for arg in "$@"; do
    case $arg in
        --with-observability|-o)
            INCLUDE_OBSERVABILITY=true
            shift
            ;;
        --rebuild|-r)
            FORCE_REBUILD=true
            shift
            ;;
        --no-cache|-n)
            NO_CACHE=true
            FORCE_REBUILD=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -o, --with-observability  Start with observability stack (Grafana, Loki, Prometheus, etc.)"
            echo "  -r, --rebuild            Force rebuild of containers before starting"
            echo "  -n, --no-cache           Force rebuild without using Docker cache (slowest, cleanest)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Start basic services only"
            echo "  $0 --with-observability      # Start with monitoring/logging stack"
            echo "  $0 --rebuild                 # Force rebuild then start"
            echo "  $0 --no-cache                # Clean rebuild from scratch (fixes env issues)"
            exit 0
            ;;
    esac
done

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

        # Check if DEEPINFRA_API_KEY is set
        if grep -q "^DEEPINFRA_API_KEY=" backend/.env && ! grep -q "^DEEPINFRA_API_KEY=$" backend/.env && ! grep -q "^DEEPINFRA_API_KEY=your" backend/.env; then
            echo -e "${GREEN}   ✅ DEEPINFRA_API_KEY is configured${NC}"
        else
            echo -e "${YELLOW}   ⚠️  DEEPINFRA_API_KEY not set in backend/.env${NC}"
            echo -e "${YELLOW}      Add your DeepInfra API key to backend/.env${NC}"
        fi
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

# Function to stop orphaned containers
stop_orphaned_containers() {
    echo -e "${YELLOW}🔍 Checking for orphaned observability containers...${NC}"

    local orphans
    orphans=$(docker ps -a --filter "name=migration_grafana" --filter "name=migration_loki" --filter "name=migration_prometheus" --filter "name=migration_tempo" --filter "name=migration_alloy" --format "{{.Names}}" 2>/dev/null || true)

    if [ ! -z "$orphans" ]; then
        echo -e "${YELLOW}⚠️  Found orphaned observability containers. Stopping them...${NC}"
        docker stop $orphans 2>/dev/null || true
        docker rm $orphans 2>/dev/null || true
        echo -e "${GREEN}✅ Orphaned containers removed${NC}"
    else
        echo -e "${GREEN}✅ No orphaned containers found${NC}"
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

# Stop orphaned containers if not including observability
if [ "$INCLUDE_OBSERVABILITY" = false ]; then
    stop_orphaned_containers
fi

echo ""

# Build compose file list as array
COMPOSE_ARGS=(-f config/docker/docker-compose.yml)
if [ "$INCLUDE_OBSERVABILITY" = true ]; then
    if [ ! -f "config/docker/docker-compose.observability.yml" ]; then
        echo -e "${RED}❌ Observability compose file not found${NC}"
        exit 1
    fi
    # CRITICAL: --env-file must be BEFORE -f flags for variable substitution
    # Without this, Grafana gets localhost defaults instead of Azure domain values
    # See: .serena/memories/observability-grafana-dashboard-debugging.md
    if [ -f "config/docker/.env.observability" ]; then
        COMPOSE_ARGS=(--env-file config/docker/.env.observability "${COMPOSE_ARGS[@]}")
        echo -e "${GREEN}✅ Loading observability environment from .env.observability${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env.observability file found - Grafana will use localhost defaults${NC}"
        echo -e "${YELLOW}   Create config/docker/.env.observability with GF_SERVER_* variables for production${NC}"
    fi
    COMPOSE_ARGS+=(-f config/docker/docker-compose.observability.yml)
    echo -e "${BLUE}📊 Including observability stack (Grafana, Loki, Prometheus, Tempo)${NC}"
    echo ""
fi

# Rebuild if requested
if [ "$FORCE_REBUILD" = true ]; then
    echo "🔨 Rebuilding containers..."
    echo ""

    BUILD_ARGS=(build)
    if [ "$NO_CACHE" = true ]; then
        echo -e "${YELLOW}⚡ Building without cache (this will take longer but ensures clean build)${NC}"
        BUILD_ARGS+=(--no-cache)
    fi

    if docker compose "${COMPOSE_ARGS[@]}" "${BUILD_ARGS[@]}"; then
        echo ""
        echo -e "${GREEN}✅ Containers rebuilt successfully${NC}"
    else
        echo ""
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    fi
    echo ""
fi

echo "📦 Starting services..."
echo ""

# Start the services
START_ARGS=(up -d)
if [ "$FORCE_REBUILD" = true ]; then
    START_ARGS+=(--force-recreate)
fi

if [ "$INCLUDE_OBSERVABILITY" = false ]; then
    START_ARGS+=(--remove-orphans)
fi

if docker compose "${COMPOSE_ARGS[@]}" "${START_ARGS[@]}"; then
    echo ""
    echo -e "${GREEN}✅ Services started successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Failed to start services. Checking logs...${NC}"
    docker compose "${COMPOSE_ARGS[@]}" logs --tail=50
    exit 1
fi

# Wait a moment for services to initialize
sleep 3

echo ""
echo "📊 Service Status:"
docker compose "${COMPOSE_ARGS[@]}" ps

# Check if all services are running
if docker compose "${COMPOSE_ARGS[@]}" ps | grep -q "Exit\|exited"; then
    echo ""
    echo -e "${RED}❌ Some services failed to start. Checking logs...${NC}"
    docker compose "${COMPOSE_ARGS[@]}" logs --tail=50
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
    echo "  1. Check if ports 8000, 8081, 5433, 6379 are already in use"
    echo "  2. Try: ./docker-stop.sh --with-observability"
    echo "  3. Then: ./docker-start.sh --no-cache"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All services are running!${NC}"

# Apply BYPASSRLS for Grafana if observability is enabled
# This is required after every PostgreSQL restart for RLS-enabled tables
if [ "$INCLUDE_OBSERVABILITY" = true ]; then
    echo ""
    echo -e "${BLUE}🔐 Configuring PostgreSQL for Grafana access...${NC}"

    # Wait for PostgreSQL to be ready
    sleep 2

    # Check if grafana_readonly user exists and apply BYPASSRLS
    if docker exec migration_postgres psql -U postgres -d migration_db -tAc "SELECT 1 FROM pg_roles WHERE rolname='grafana_readonly'" 2>/dev/null | grep -q 1; then
        if docker exec migration_postgres psql -U postgres -d migration_db -c "ALTER ROLE grafana_readonly BYPASSRLS;" 2>/dev/null; then
            echo -e "${GREEN}✅ BYPASSRLS applied to grafana_readonly user${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not apply BYPASSRLS (non-critical if user doesn't exist yet)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  grafana_readonly user not found - run create-grafana-user.sql first${NC}"
        echo -e "${YELLOW}   See: config/docker/observability/create-grafana-user.sql${NC}"
    fi
fi

echo ""
echo "📋 Available commands:"
if [ "$INCLUDE_OBSERVABILITY" = true ]; then
    echo "  • View logs:   docker compose --env-file config/docker/.env.observability -f config/docker/docker-compose.yml -f config/docker/docker-compose.observability.yml logs -f [service]"
    echo "  • Stop (all):  ./docker-stop.sh --with-observability"
    echo "  • Status:      docker compose --env-file config/docker/.env.observability -f config/docker/docker-compose.yml -f config/docker/docker-compose.observability.yml ps"
else
    echo "  • View logs:   docker compose -f config/docker/docker-compose.yml logs -f [service]"
    echo "  • Stop:        ./docker-stop.sh"
    echo "  • Status:      docker compose -f config/docker/docker-compose.yml ps"
fi
echo ""
echo "🌐 Access your application:"
echo "  • Frontend:    http://localhost:8081"
echo "  • Backend API: http://localhost:8000/docs"
echo "  • Database:    localhost:5433 (user: postgres, password: postgres)"
echo "  • Redis:       localhost:6379"

if [ "$INCLUDE_OBSERVABILITY" = true ]; then
    echo ""
    echo "📊 Observability Stack:"
    echo "  • Grafana:     http://localhost:9999 (admin/admin)"
    echo "  • Prometheus:  http://localhost:9090"
    echo "  • Loki:        http://localhost:3100"
    echo "  • Tempo:       http://localhost:3200"
fi

echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

# Verify environment variables are loaded (if --no-cache was used)
if [ "$NO_CACHE" = true ]; then
    echo ""
    echo -e "${BLUE}🔍 Verifying environment configuration...${NC}"

    # Check if we need sudo for docker commands
    # Use SUDO_USER to detect if script was invoked with sudo, or check if running as root
    if [ -n "$SUDO_USER" ] || [ "$(id -u)" -eq 0 ]; then
        # Script was run with sudo or as root, use sudo for docker exec
        DEEPINFRA_CHECK=$(sudo docker exec migration_backend env 2>/dev/null | grep "^DEEPINFRA_API_KEY=" || echo "NOT_FOUND")
    else
        # Check if user has docker group access or socket write permission
        if groups | grep -q docker || [ -w /var/run/docker.sock ]; then
            DEEPINFRA_CHECK=$(docker exec migration_backend env 2>/dev/null | grep "^DEEPINFRA_API_KEY=" || echo "NOT_FOUND")
        else
            # Fallback to sudo if user lacks docker permissions
            DEEPINFRA_CHECK=$(sudo docker exec migration_backend env 2>/dev/null | grep "^DEEPINFRA_API_KEY=" || echo "NOT_FOUND")
        fi
    fi

    if [ "$DEEPINFRA_CHECK" != "NOT_FOUND" ] && [ ! -z "$DEEPINFRA_CHECK" ]; then
        echo -e "${GREEN}✅ DEEPINFRA_API_KEY loaded successfully in container${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not verify DEEPINFRA_API_KEY in container (may need sudo)${NC}"
        echo -e "${BLUE}   Manual check: sudo docker exec migration_backend env | grep DEEPINFRA_API_KEY${NC}"
    fi
fi
