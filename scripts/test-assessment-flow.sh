#!/bin/bash

# Test Assessment Flow Feature with Playwright
# This script starts the application and runs browser-based tests

set -e

echo "🚀 Starting Assessment Flow Testing..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Function to wait for service
wait_for_service() {
    local url=$1
    local service=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for $service to be ready...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|302"; then
            echo -e "${GREEN}✅ $service is ready!${NC}"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ $service failed to start after $max_attempts attempts${NC}"
    return 1
}

# Start services
echo -e "${YELLOW}🐳 Starting Docker services...${NC}"
docker-compose up -d

# Wait for backend
wait_for_service "http://localhost:8000/health" "Backend API"

# Wait for frontend
wait_for_service "http://localhost:3000" "Frontend"

# Install Playwright if needed
echo -e "${YELLOW}📦 Checking Playwright installation...${NC}"
cd frontend
if ! npx playwright --version > /dev/null 2>&1; then
    echo "Installing Playwright..."
    npm install -D @playwright/test
    npx playwright install chromium
fi

# Run database migrations
echo -e "${YELLOW}🗄️ Running database migrations...${NC}"
docker exec migration_backend alembic upgrade head

# Initialize test data
echo -e "${YELLOW}📊 Initializing test data...${NC}"
docker exec migration_backend python -c "
import asyncio
from app.core.database_initialization import initialize_database
from app.core.database import AsyncSessionLocal

async def init():
    async with AsyncSessionLocal() as db:
        await initialize_database(db)
        print('✅ Database initialized with assessment tables')

asyncio.run(init())
"

# Create test applications
echo -e "${YELLOW}🏗️ Creating test applications...${NC}"
docker exec migration_backend python -c "
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
import uuid

async def create_test_apps():
    async with AsyncSessionLocal() as db:
        # Create test applications
        apps = [
            Asset(
                id=str(uuid.uuid4()),
                name='Customer Portal',
                type='Application',
                category='Web Application',
                client_account_id=1,
                ready_for_assessment=True,
                metadata={
                    'frontend_technologies': ['React', 'TypeScript'],
                    'backend_technologies': ['Java', 'Spring Boot'],
                    'database_systems': ['PostgreSQL']
                }
            ),
            Asset(
                id=str(uuid.uuid4()),
                name='Order Management System',
                type='Application',
                category='Enterprise Application',
                client_account_id=1,
                ready_for_assessment=True,
                metadata={
                    'frontend_technologies': ['Angular'],
                    'backend_technologies': ['.NET Core'],
                    'database_systems': ['SQL Server']
                }
            )
        ]

        for app in apps:
            db.add(app)

        await db.commit()
        print(f'✅ Created {len(apps)} test applications')

asyncio.run(create_test_apps())
"

# Run Playwright tests
echo -e "${YELLOW}🎭 Running Playwright tests...${NC}"
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator/frontend

# Set test environment variables
export PLAYWRIGHT_BASE_URL="http://localhost:3000"
export API_URL="http://localhost:8000"

# Run tests with headed browser for visual verification
npx playwright test tests/e2e/assessment-flow.test.ts --headed --project=chromium --reporter=list

# Check test results
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All Assessment Flow tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"

    # Show logs for debugging
    echo -e "${YELLOW}📋 Backend logs:${NC}"
    docker-compose logs --tail=50 backend

    echo -e "${YELLOW}📋 Frontend logs:${NC}"
    docker-compose logs --tail=50 frontend
fi

# Cleanup option
read -p "Do you want to stop the services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    docker-compose down
fi

echo -e "${GREEN}✨ Assessment Flow testing complete!${NC}"
