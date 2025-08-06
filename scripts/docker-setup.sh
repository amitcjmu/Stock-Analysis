#!/bin/bash
# Docker Setup Helper Script
# Helps developers choose the right Docker build method based on their environment

set -e

echo "🐳 AI Modernize Migration Platform - Docker Setup Helper"
echo "======================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if BuildKit is available
check_buildkit() {
    echo "🔍 Checking Docker BuildKit availability..."
    
    # Check Docker version
    DOCKER_VERSION=$(docker version --format '{{.Client.Version}}' 2>/dev/null || echo "unknown")
    echo "Docker version: $DOCKER_VERSION"
    
    # Check if DOCKER_BUILDKIT is set
    if [ "${DOCKER_BUILDKIT:-}" = "1" ]; then
        echo -e "${GREEN}✅ DOCKER_BUILDKIT is enabled via environment variable${NC}"
        return 0
    fi
    
    # Check if Docker Desktop has BuildKit enabled by default (version 18.06+)
    if command -v docker buildx >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Buildx is available (BuildKit supported)${NC}"
        return 0
    fi
    
    # Try to detect BuildKit support
    if docker info 2>/dev/null | grep -q "BuildKit"; then
        echo -e "${GREEN}✅ BuildKit appears to be available${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}⚠️  BuildKit availability uncertain${NC}"
    return 1
}

# Function to test BuildKit with a simple build
test_buildkit() {
    echo "🧪 Testing BuildKit with a simple build..."
    
    # Create a temporary Dockerfile to test BuildKit
    cat > /tmp/test-buildkit.dockerfile << 'EOF'
FROM alpine:latest
RUN --mount=type=cache,target=/tmp/cache echo "BuildKit test"
EOF
    
    # Try to build with the test Dockerfile
    if DOCKER_BUILDKIT=1 docker build -f /tmp/test-buildkit.dockerfile . -t buildkit-test >/dev/null 2>&1; then
        echo -e "${GREEN}✅ BuildKit test successful${NC}"
        docker rmi buildkit-test >/dev/null 2>&1 || true
        rm /tmp/test-buildkit.dockerfile
        return 0
    else
        echo -e "${RED}❌ BuildKit test failed${NC}"
        rm /tmp/test-buildkit.dockerfile
        return 1
    fi
}

# Main execution
echo ""
echo "Checking your Docker environment..."
echo ""

# Check if Docker is installed and running
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
    echo "Please install Docker Desktop and try again."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed and running${NC}"
echo ""

# Check BuildKit availability
if check_buildkit && test_buildkit; then
    echo ""
    echo -e "${GREEN}🎉 BuildKit is available and working!${NC}"
    echo ""
    echo "You can use the standard docker-compose.yml file:"
    echo -e "${BLUE}  docker-compose up --build${NC}"
    echo ""
    echo "Or enable BuildKit explicitly:"
    echo -e "${BLUE}  DOCKER_BUILDKIT=1 docker-compose up --build${NC}"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  BuildKit is not available or not working${NC}"
    echo ""
    echo "Use the local development version instead:"
    echo -e "${BLUE}  docker-compose -f docker-compose.local.yml up --build${NC}"
    echo ""
    echo "This uses Dockerfile.backend.local which doesn't require BuildKit."
    echo ""
fi

echo "📝 Available build options:"
echo ""
echo "1. Standard build (requires BuildKit):"
echo -e "   ${BLUE}docker-compose up --build${NC}"
echo ""
echo "2. Local build (no BuildKit required):"
echo -e "   ${BLUE}docker-compose -f docker-compose.local.yml up --build${NC}"
echo ""
echo "3. Enable BuildKit for current session:"
echo -e "   ${BLUE}export DOCKER_BUILDKIT=1${NC}"
echo -e "   ${BLUE}docker-compose up --build${NC}"
echo ""
echo "4. One-time BuildKit enable:"
echo -e "   ${BLUE}DOCKER_BUILDKIT=1 docker-compose up --build${NC}"
echo ""

echo "🔧 To enable BuildKit permanently:"
echo "   • Docker Desktop: Settings > Docker Engine > set '\"features\": {\"buildkit\": true}'"
echo "   • Linux: Add 'export DOCKER_BUILDKIT=1' to ~/.bashrc or ~/.zshrc"
echo ""

echo -e "${GREEN}Setup complete! Choose the appropriate build command above.${NC}"