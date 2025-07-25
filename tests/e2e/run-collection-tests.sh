#!/bin/bash

# Run Collection Flow E2E Tests with Playwright
# This script runs the collection flow tests using the Playwright MCP server

echo "🧪 Running Collection Flow E2E Tests..."
echo "=================================="

# Set test environment
export NODE_ENV=test
export PLAYWRIGHT_HEADLESS=false  # Set to true for CI/headless mode

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if services are running
check_services() {
    echo -e "${YELLOW}Checking if required services are running...${NC}"

    # Check if frontend is running
    if curl -s http://localhost:5173 > /dev/null; then
        echo -e "${GREEN}✓ Frontend is running${NC}"
    else
        echo -e "${RED}✗ Frontend is not running. Please start it with 'npm run dev'${NC}"
        exit 1
    fi

    # Check if backend is running
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend is running${NC}"
    else
        echo -e "${RED}✗ Backend is not running. Please start it${NC}"
        exit 1
    fi
}

# Check services before running tests
check_services

echo -e "\n${YELLOW}Starting Collection Flow tests...${NC}\n"

# Run the collection flow tests
npx playwright test tests/e2e/collection-flow.spec.ts \
    --config=tests/e2e/playwright.config.ts \
    --reporter=list \
    --retries=1 \
    --timeout=120000

# Capture exit code
TEST_EXIT_CODE=$?

# Generate HTML report if tests were run
if [ -d "playwright-report" ]; then
    echo -e "\n${YELLOW}Test report generated at: playwright-report/index.html${NC}"
fi

# Summary
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ All Collection Flow tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some Collection Flow tests failed. Check the report for details.${NC}"

    # Option to open the HTML report
    echo -e "\n${YELLOW}Would you like to open the test report? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        npx playwright show-report
    fi
fi

exit $TEST_EXIT_CODE
