#!/bin/bash

# On-demand health check script for migration platform services
# Usage: ./scripts/health-check.sh [service]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service URLs
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:8081"
POSTGRES_URL="localhost:5433"

check_backend() {
    echo "🔍 Checking Backend API..."
    if curl -s -f "${BACKEND_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend API is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Backend API is not responding${NC}"
        return 1
    fi
}

check_frontend() {
    echo "🔍 Checking Frontend..."
    if curl -s -f "${FRONTEND_URL}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Frontend is not responding${NC}"
        return 1
    fi
}

check_postgres() {
    echo "🔍 Checking PostgreSQL Database..."
    if nc -z localhost 5433 2>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ PostgreSQL is not responding${NC}"
        return 1
    fi
}

check_containers() {
    echo "🔍 Checking Docker Containers..."

    # Check if containers are running
    local backend_running=$(docker ps --filter "name=migration_backend" --format "{{.Names}}" | wc -l)
    local frontend_running=$(docker ps --filter "name=migration_frontend" --format "{{.Names}}" | wc -l)
    local postgres_running=$(docker ps --filter "name=migration_postgres" --format "{{.Names}}" | wc -l)

    if [ "$backend_running" -eq 1 ]; then
        echo -e "${GREEN}✅ Backend container is running${NC}"
    else
        echo -e "${RED}❌ Backend container is not running${NC}"
    fi

    if [ "$frontend_running" -eq 1 ]; then
        echo -e "${GREEN}✅ Frontend container is running${NC}"
    else
        echo -e "${RED}❌ Frontend container is not running${NC}"
    fi

    if [ "$postgres_running" -eq 1 ]; then
        echo -e "${GREEN}✅ PostgreSQL container is running${NC}"
    else
        echo -e "${RED}❌ PostgreSQL container is not running${NC}"
    fi
}

# Main function
main() {
    local service="$1"
    local exit_code=0

    echo "🏥 Migration Platform Health Check"
    echo "=================================="

    case "$service" in
        "backend")
            check_backend || exit_code=1
            ;;
        "frontend")
            check_frontend || exit_code=1
            ;;
        "postgres")
            check_postgres || exit_code=1
            ;;
        "containers")
            check_containers
            ;;
        *)
            # Check all services
            check_containers
            echo ""
            check_postgres || exit_code=1
            check_backend || exit_code=1
            check_frontend || exit_code=1
            ;;
    esac

    echo ""
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}🎉 All requested services are healthy!${NC}"
    else
        echo -e "${RED}⚠️  Some services have issues. Check the output above.${NC}"
    fi

    exit $exit_code
}

# Make sure we have the required tools
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is required but not installed${NC}"
    exit 1
fi

if ! command -v nc &> /dev/null; then
    echo -e "${YELLOW}⚠️  netcat (nc) not found, skipping direct port checks${NC}"
fi

main "$@"
