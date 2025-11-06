#!/bin/bash

# Docker Stop Helper Script
# This script stops the application and optionally cleans up resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root directory
cd "$(dirname "$0")"

echo "🛑 Stopping AI Modernize Migration Platform..."
echo ""

# Parse command line arguments
CLEAN_VOLUMES=false
CLEAN_ALL=false
INCLUDE_OBSERVABILITY=false

for arg in "$@"; do
    case $arg in
        --clean-volumes|-v)
            CLEAN_VOLUMES=true
            shift
            ;;
        --clean-all|-a)
            CLEAN_ALL=true
            shift
            ;;
        --with-observability|-o)
            INCLUDE_OBSERVABILITY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --clean-volumes        Remove volumes (database data will be lost)"
            echo "  -a, --clean-all           Remove everything including images"
            echo "  -o, --with-observability  Also stop observability stack (Grafana, Loki, etc.)"
            echo "  -h, --help               Show this help message"
            exit 0
            ;;
    esac
done

# Build compose file list
COMPOSE_FILES="-f config/docker/docker-compose.yml"
if [ "$INCLUDE_OBSERVABILITY" = true ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f config/docker/docker-compose.observability.yml"
    echo -e "${YELLOW}📊 Including observability stack in shutdown${NC}"
fi

# Stop the services
echo "📦 Stopping services..."
DOCKER_COMMAND="docker-compose $COMPOSE_FILES down"

if [ "$INCLUDE_OBSERVABILITY" = true ]; then
    DOCKER_COMMAND="$DOCKER_COMMAND --remove-orphans"
fi

if eval $DOCKER_COMMAND; then
    echo -e "${GREEN}✅ Services stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Services may not be running${NC}"
fi

# Clean volumes if requested
if [ "$CLEAN_VOLUMES" = true ]; then
    echo ""
    echo -e "${YELLOW}🗑️  Removing volumes (database data will be lost)...${NC}"
    docker-compose $COMPOSE_FILES down -v
    echo -e "${GREEN}✅ Volumes removed${NC}"
fi

# Clean everything if requested
if [ "$CLEAN_ALL" = true ]; then
    echo ""
    echo -e "${YELLOW}🗑️  Removing all containers, volumes, and images...${NC}"
    docker-compose $COMPOSE_FILES down -v --rmi all --remove-orphans
    echo -e "${GREEN}✅ All resources cleaned${NC}"
fi

echo ""
echo -e "${GREEN}✨ Shutdown complete!${NC}"

# Show restart instructions
echo ""
echo "📋 To restart the application:"
echo "  • Basic:              ./docker-start.sh"
echo "  • With observability: ./docker-start.sh --with-observability"
echo "  • Force rebuild:      ./docker-start.sh --rebuild"

if [ "$CLEAN_VOLUMES" = true ] || [ "$CLEAN_ALL" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Note: Database was reset. You'll start with a fresh database.${NC}"
fi
