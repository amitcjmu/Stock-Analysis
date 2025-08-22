#!/bin/bash

# Docker Health Check Script
# This script verifies the Docker environment is healthy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root directory
cd "$(dirname "$0")"

echo "🔍 Docker Environment Health Check"
echo "=================================="
echo ""

# Check Docker status
echo -e "${BLUE}Docker Status:${NC}"
if docker info >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker is running"
    docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "  ${GREEN}✓${NC} Docker version: $docker_version"
else
    echo -e "  ${RED}✗${NC} Docker is not running"
    exit 1
fi

echo ""

# Check Docker Compose
echo -e "${BLUE}Docker Compose Status:${NC}"
if docker-compose version >/dev/null 2>&1; then
    compose_version=$(docker-compose version --short)
    echo -e "  ${GREEN}✓${NC} Docker Compose version: $compose_version"
else
    echo -e "  ${RED}✗${NC} Docker Compose not found"
    exit 1
fi

echo ""

# Check containers
echo -e "${BLUE}Container Status:${NC}"
running_containers=$(docker ps --filter "name=migration_" --format "{{.Names}}" 2>/dev/null | wc -l | tr -d ' ')

if [ "$running_containers" -eq "0" ]; then
    echo -e "  ${YELLOW}⚠${NC} No containers running. Run ./docker-start.sh to start"
else
    # Check each service
    services=("migration_postgres" "migration_redis" "migration_backend" "migration_frontend")
    all_healthy=true

    for service in "${services[@]}"; do
        if docker ps --filter "name=$service" --format "{{.Names}}" | grep -q "$service"; then
            status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "unknown")
            if [ "$status" = "running" ]; then
                echo -e "  ${GREEN}✓${NC} $service: running"
            else
                echo -e "  ${RED}✗${NC} $service: $status"
                all_healthy=false
            fi
        else
            echo -e "  ${RED}✗${NC} $service: not found"
            all_healthy=false
        fi
    done
fi

echo ""

# Check service endpoints
echo -e "${BLUE}Service Endpoints:${NC}"
if [ "$running_containers" -gt "0" ]; then
    # Check backend
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
        echo -e "  ${GREEN}✓${NC} Backend API: http://localhost:8000/docs"
    else
        echo -e "  ${RED}✗${NC} Backend API not responding"
    fi

    # Check frontend
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8081 | grep -q "200"; then
        echo -e "  ${GREEN}✓${NC} Frontend: http://localhost:8081"
    else
        echo -e "  ${RED}✗${NC} Frontend not responding"
    fi

    # Check database
    if docker exec migration_postgres pg_isready -U postgres >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL: localhost:5433"
    else
        echo -e "  ${RED}✗${NC} PostgreSQL not ready"
    fi

    # Check Redis
    if docker exec migration_redis redis-cli ping >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Redis: localhost:6379"
    else
        echo -e "  ${RED}✗${NC} Redis not responding"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Services not running"
fi

echo ""

# Check disk usage
echo -e "${BLUE}Docker Disk Usage:${NC}"
disk_usage=$(docker system df --format "table {{.Type}}\t{{.Size}}" | tail -n +2)
while IFS= read -r line; do
    echo "  • $line"
done <<< "$disk_usage"

echo ""

# Check for common issues
echo -e "${BLUE}Configuration Check:${NC}"

# Check backend/.env
if [ -f "backend/.env" ]; then
    echo -e "  ${GREEN}✓${NC} backend/.env exists"
    # Check for API keys
    if grep -q "OPENAI_API_KEY=your-key-here\|ANTHROPIC_API_KEY=your-key-here" backend/.env; then
        echo -e "  ${YELLOW}⚠${NC} API keys not configured in backend/.env"
    fi
else
    echo -e "  ${RED}✗${NC} backend/.env missing"
fi

# Check init.sql
if [ -f "backend/init.sql" ]; then
    echo -e "  ${GREEN}✓${NC} backend/init.sql exists"
else
    echo -e "  ${RED}✗${NC} backend/init.sql missing"
fi

# Check docker-compose files
if [ -f "config/docker/docker-compose.yml" ]; then
    echo -e "  ${GREEN}✓${NC} docker-compose.yml exists"
else
    echo -e "  ${RED}✗${NC} docker-compose.yml missing"
fi

echo ""
echo "=================================="

# Summary
if [ "$running_containers" -eq "4" ] && [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✅ All systems operational!${NC}"
    echo ""
    echo "🌐 Access your application at:"
    echo "   • Frontend: http://localhost:8081"
    echo "   • API Docs: http://localhost:8000/docs"
else
    echo -e "${YELLOW}⚠️  Some issues detected${NC}"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Run: ./docker-stop.sh --clean-volumes"
    echo "   2. Run: ./docker-start.sh"
    echo "   3. Check logs: docker-compose -f config/docker/docker-compose.yml logs"
fi
