#!/bin/bash

echo "🧪 Running Complete Test Suite"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track failures
FAILURES=0

# 1. Backend Unit Tests
echo -e "${BLUE}1. Running Backend Unit Tests...${NC}"
echo "--------------------------------"
docker exec migration_backend python -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backend unit tests failed${NC}"
    FAILURES=$((FAILURES + 1))
else
    echo -e "${GREEN}✅ Backend unit tests passed${NC}"
fi
echo ""

# 2. Frontend Unit Tests
echo -e "${BLUE}2. Running Frontend Unit Tests...${NC}"
echo "---------------------------------"
# Check if test script exists
if npm run | grep -q "test[[:space:]]"; then
    npm test -- --watchAll=false
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Frontend unit tests failed${NC}"
        FAILURES=$((FAILURES + 1))
    else
        echo -e "${GREEN}✅ Frontend unit tests passed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No frontend unit test script found, skipping...${NC}"
fi
echo ""

# 3. API Integration Tests
echo -e "${BLUE}3. Running API Integration Tests...${NC}"
echo "-----------------------------------"
# Create the integration test file if it doesn't exist
if [ ! -f "backend/tests/api/test_flows_endpoint_integration.py" ]; then
    echo -e "${YELLOW}⚠️  Integration tests not found, skipping...${NC}"
else
    docker exec migration_backend python -m pytest tests/api/test_flows_endpoint_integration.py -v
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ API integration tests failed${NC}"
        FAILURES=$((FAILURES + 1))
    else
        echo -e "${GREEN}✅ API integration tests passed${NC}"
    fi
fi
echo ""

# 4. Browser E2E Tests
echo -e "${BLUE}4. Running Browser E2E Tests...${NC}"
echo "-------------------------------"
echo "Testing real page loads and user interactions..."

# Ensure test-results directory exists
mkdir -p test-results

# Install Playwright if needed
npx playwright install chromium 2>/dev/null || true

# Run specific page load test
npx playwright test tests/e2e/data-import-page.spec.ts --reporter=list
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Browser page load tests failed${NC}"
    echo "Console errors or API failures detected!"
    FAILURES=$((FAILURES + 1))

    # Show screenshot if exists
    if [ -f "test-results/data-import-errors.png" ]; then
        echo "Error screenshot saved at: test-results/data-import-errors.png"
    fi
else
    echo -e "${GREEN}✅ Browser page load tests passed${NC}"
fi
echo ""

# 5. Summary
echo -e "${BLUE}Test Summary${NC}"
echo "============"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "The application is ready for deployment."
else
    echo -e "${RED}❌ $FAILURES test suite(s) failed${NC}"
    echo ""
    echo "Fix these issues before marking as complete:"
    echo "- Console errors during page loads"
    echo "- API errors (500, 400, etc.)"
    echo "- Integration failures between components"
    echo ""
    echo "Debug tips:"
    echo "1. Run individual test suites to isolate issues"
    echo "2. Check docker logs: docker-compose logs backend frontend"
    echo "3. Run browser tests with UI: npx playwright test --ui"
    echo "4. Check test-results/ for screenshots"
    exit 1
fi

# Clean up
echo ""
echo "🧹 Cleaning up test artifacts..."
find test-results -name "*.png" -mtime +1 -delete 2>/dev/null || true

echo ""
echo "✨ Test suite complete!"
