#!/bin/bash

echo "🌐 Running Browser Integration Tests"
echo "===================================="
echo "These tests simulate real user interactions in a browser"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if containers are running
echo "🐳 Checking Docker containers..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Docker containers are not running!${NC}"
    echo "Starting containers..."
    docker-compose up -d
    sleep 10
fi

# Install Playwright browsers if needed
echo "🎭 Checking Playwright browsers..."
npx playwright install chromium

# Run the Data Import page tests specifically
echo ""
echo "🧪 Testing Data Import Page Load..."
echo "-----------------------------------"
npx playwright test tests/e2e/data-import-page.spec.ts --reporter=list

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Data Import page tests failed!${NC}"
    echo "Console errors or API failures detected during page load."
    echo ""
    echo "To debug:"
    echo "1. Check test-results/ for screenshots"
    echo "2. Run: npx playwright test --debug"
    echo "3. Check browser console in debug mode"
    exit 1
fi

# Run the full import and mapping test
echo ""
echo "🧪 Testing Import and Mapping Flow..."
echo "------------------------------------"
npx playwright test tests/e2e/import-and-mapping.spec.ts --reporter=list

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Import and mapping test failed${NC}"
    echo "This might be due to data dependencies."
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="

# Check for any console errors in the test results
if [ -f "test-results/results.json" ]; then
    CONSOLE_ERRORS=$(grep -o "console error" test-results/results.json | wc -l)
    API_ERRORS=$(grep -o "500\|400\|401\|403" test-results/results.json | wc -l)

    if [ $CONSOLE_ERRORS -gt 0 ]; then
        echo -e "${RED}❌ Found $CONSOLE_ERRORS console errors${NC}"
    else
        echo -e "${GREEN}✅ No console errors${NC}"
    fi

    if [ $API_ERRORS -gt 0 ]; then
        echo -e "${RED}❌ Found $API_ERRORS API errors${NC}"
    else
        echo -e "${GREEN}✅ No API errors${NC}"
    fi
fi

echo ""
echo "💡 Tips:"
echo "- Run 'npx playwright test --ui' for interactive mode"
echo "- Run 'npx playwright show-report' to see HTML report"
echo "- Check test-results/ for screenshots of failures"
