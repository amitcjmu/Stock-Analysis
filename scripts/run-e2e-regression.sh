#!/bin/bash

# Script to run E2E regression tests with proper environment setup

echo "🚀 Starting E2E Regression Test Suite"
echo "======================================"

# Set E2E test mode to enable diagnostics endpoint
export E2E_TEST_MODE=true
echo "✅ E2E_TEST_MODE enabled"

# Ensure Docker containers are running
echo "🐳 Checking Docker containers..."
docker-compose ps | grep -q "migrate-backend" || {
    echo "⚠️  Backend container not running. Starting containers..."
    docker-compose up -d
    echo "⏳ Waiting for services to be ready..."
    sleep 10
}

# Rebuild backend to include diagnostics endpoint
echo "🔨 Rebuilding backend with E2E test mode..."
docker-compose exec -e E2E_TEST_MODE=true migrate-backend bash -c "cd /app && python -m app.api.v1.api"

# Install Playwright browsers if needed
echo "🎭 Checking Playwright browsers..."
npx playwright install chromium 2>/dev/null || echo "✅ Browsers already installed"

# Run the enhanced E2E regression test
echo "🧪 Running Enhanced E2E Regression Test..."
echo "==========================================="

npm run test:e2e -- \
    tests/e2e/regression/discovery/discovery-flow-full-e2e-regression.spec.ts \
    --timeout=60000 \
    --reporter=list

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ E2E Regression Tests PASSED!"
    echo ""
    echo "📊 Check the detailed report at:"
    echo "   tests/e2e/test-results/e2e-regression-report-*.json"
else
    echo ""
    echo "❌ E2E Regression Tests FAILED"
    echo ""
    echo "📋 Check the error details above and the report at:"
    echo "   tests/e2e/test-results/e2e-regression-report-*.json"
fi

# Unset E2E test mode
unset E2E_TEST_MODE
echo ""
echo "🏁 E2E Regression Test Suite Complete"
