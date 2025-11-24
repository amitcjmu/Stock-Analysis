#!/bin/bash
#
# run-pr-tests.sh
#
# Runs tests before PR review based on testing repository guidelines.
# This is typically run toward the end of PR when ready for manual review.
#
# Usage:
#   ./scripts/run-pr-tests.sh                    # Run all PR-ready tests
#   ./scripts/run-pr-tests.sh --unit             # Unit tests only
#   ./scripts/run-pr-tests.sh --integration      # Integration tests only
#   ./scripts/run-pr-tests.sh --smoke            # Smoke tests only
#   ./scripts/run-pr-tests.sh --coverage         # With coverage report
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

TESTING_REPO="docs/testing"
QA_GUIDE="$TESTING_REPO/QA_GUIDE.md"
TESTING_STRATEGY="$TESTING_REPO/testing-strategy.md"
TESTING_README="$TESTING_REPO/README.md"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 Running PR-Ready Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Docker containers are running
echo -e "${CYAN}📋 Checking test environment...${NC}"
if ! docker ps | grep -q migration_backend; then
    echo -e "${YELLOW}⚠️  Backend container not running. Starting services...${NC}"
    docker compose -f config/docker/docker-compose.yml up -d
    echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
    sleep 5
fi

# Verify services are healthy
if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${RED}❌ Backend service not healthy. Please check Docker containers.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Services are healthy${NC}"
echo ""

# Detect test directory inside container
TEST_DIR=$(docker exec migration_backend bash -lc 'ls -1d backend/tests tests/backend tests 2>/dev/null | head -1' || echo "")
if [ -z "$TEST_DIR" ]; then
    echo -e "${RED}❌ Could not detect test directory in container${NC}"
    exit 1
fi

echo -e "${CYAN}📁 Test directory: $TEST_DIR${NC}"
echo ""

# Determine which tests to run
if [ "$1" = "--unit" ]; then
    TEST_SUITE="unit"
    PYTEST_ARGS="-m unit"
    echo -e "${BLUE}🎯 Running unit tests only${NC}"
elif [ "$1" = "--integration" ]; then
    TEST_SUITE="integration"
    PYTEST_ARGS="-m integration"
    echo -e "${BLUE}🎯 Running integration tests only${NC}"
elif [ "$1" = "--smoke" ]; then
    TEST_SUITE="smoke"
    PYTEST_ARGS="-m smoke"
    echo -e "${BLUE}🎯 Running smoke tests only${NC}"
elif [ "$1" = "--coverage" ]; then
    TEST_SUITE="all"
    PYTEST_ARGS="--cov=app --cov-report=html --cov-report=term-missing"
    echo -e "${BLUE}🎯 Running all tests with coverage${NC}"
else
    TEST_SUITE="pr-ready"
    PYTEST_ARGS="-m 'smoke or unit' --maxfail=5"
    echo -e "${BLUE}🎯 Running PR-ready tests (smoke + unit)${NC}"
fi

echo ""
echo -e "${CYAN}📚 Testing Repository References:${NC}"
echo -e "  - Strategy: $TESTING_STRATEGY"
echo -e "  - QA Guide: $QA_GUIDE"
echo -e "  - README: $TESTING_README"
echo ""

# Run tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Executing tests...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TEST_CMD="python -m pytest \"$TEST_DIR\" $PYTEST_ARGS -v --tb=short"

if docker exec migration_backend bash -lc "$TEST_CMD"; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}📊 Test Summary:${NC}"
    echo -e "  Suite: $TEST_SUITE"
    echo -e "  Status: ✅ PASSED"
    echo ""

    if [ "$1" = "--coverage" ]; then
        echo -e "${CYAN}📈 Coverage report:${NC}"
        echo -e "  HTML: tests/coverage/html/index.html"
        echo -e "  Open in browser: file://$(pwd)/tests/coverage/html/index.html"
        echo ""
    fi

    echo -e "${GREEN}✅ Ready for PR review!${NC}"
    echo -e "${CYAN}📝 Next steps:${NC}"
    echo -e "  1. Review test results above"
    echo -e "  2. Address any warnings or deprecations"
    echo -e "  3. Update PR description with test results"
    echo -e "  4. Request manual code review"
    exit 0
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Tests failed!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Please fix failing tests before PR review${NC}"
    echo -e "${CYAN}📚 Reference testing documentation:${NC}"
    echo -e "  - $TESTING_STRATEGY"
    echo -e "  - $QA_GUIDE"
    echo -e "  - $TESTING_README"
    echo ""
    echo -e "${CYAN}🔍 Debugging tips:${NC}"
    echo -e "  - Run with verbose output: ./scripts/run-pr-tests.sh --unit -vv"
    echo -e "  - Run specific test: docker exec migration_backend python -m pytest \"$TEST_DIR\" -k 'test_name' -v"
    echo -e "  - View backend logs: docker logs migration_backend"
    echo ""
    exit 1
fi
