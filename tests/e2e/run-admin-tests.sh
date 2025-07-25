#!/bin/bash

# Admin Interface E2E Test Runner
# This script ensures the platform is running and executes comprehensive admin interface tests

set -e

echo "🎯 Admin Interface E2E Test Runner"
echo "=================================="

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is required but not installed"
    exit 1
fi

# Check if Playwright is available
if ! command -v npx &> /dev/null; then
    echo "❌ npx is required but not installed"
    exit 1
fi

echo "📋 Starting Docker services..."
docker-compose up -d --build

echo "⏳ Waiting for services to be ready..."

# Wait for backend to be ready
echo "🔄 Checking backend health..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Backend is ready"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo "❌ Backend failed to start within $timeout seconds"
        echo "📋 Backend logs:"
        docker-compose logs backend
        exit 1
    fi
done

# Wait for frontend to be ready
echo "🔄 Checking frontend health..."
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:8081 >/dev/null 2>&1; then
        echo "✅ Frontend is ready"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo "❌ Frontend failed to start within $timeout seconds"
        echo "📋 Frontend logs:"
        docker-compose logs frontend
        exit 1
    fi
done

# Install Playwright if needed
echo "🔄 Installing Playwright dependencies..."
npm install @playwright/test

# Install browsers if needed
echo "🔄 Installing Playwright browsers..."
npx playwright install chromium

echo "🚀 Running Admin Interface E2E Tests..."
echo "======================================="

# Run the tests with detailed output
npx playwright test tests/e2e/admin-interface.spec.ts --reporter=list --timeout=60000

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ALL ADMIN INTERFACE TESTS PASSED!"
    echo "===================================="
    echo "✅ User deactivation/activation: WORKING"
    echo "✅ Engagement creation: WORKING"
    echo "✅ Client editing: WORKING"
    echo "✅ Navigation: WORKING"
    echo "✅ Error handling: WORKING"
    echo "✅ Form validation: WORKING"
    echo ""
    echo "🎉 The admin interface is fully functional!"
else
    echo ""
    echo "❌ ADMIN INTERFACE TESTS FAILED!"
    echo "================================"
    echo "Some admin interface functionality is not working correctly."
    echo "Please check the test output above for specific failures."
    echo ""
    echo "📋 Common issues to check:"
    echo "- Frontend-backend field mapping mismatches"
    echo "- Missing API endpoints"
    echo "- Authentication issues"
    echo "- UUID format problems"
    echo "- Database constraint violations"
    echo ""
    echo "🔧 To debug:"
    echo "1. Check browser developer tools in test artifacts"
    echo "2. Review backend logs: docker-compose logs backend"
    echo "3. Review frontend logs: docker-compose logs frontend"
    echo "4. Check network requests in Playwright trace files"
    exit 1
fi

echo ""
echo "🧹 Cleaning up..."
# Keep services running for manual testing if needed
echo "ℹ️ Services are still running for manual verification"
echo "ℹ️ Frontend: http://localhost:8081"
echo "ℹ️ Backend: http://localhost:8000"
echo "ℹ️ Run 'docker-compose down' to stop services"
