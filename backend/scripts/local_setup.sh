#!/bin/bash
# AI Modernize Migration Platform - Local Development Setup Script
# This script helps developers set up the platform locally

set -e

echo "🚀 AI Modernize Migration Platform - Local Development Setup"
echo "==========================================================="

# Check if running from backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   cd backend && ./scripts/local_setup.sh"
    exit 1
fi

# Function to check if PostgreSQL is running
check_postgres() {
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h localhost -p 5432 &> /dev/null; then
            echo "✅ PostgreSQL is running on localhost:5432"
            return 0
        elif pg_isready -h localhost -p 5433 &> /dev/null; then
            echo "✅ PostgreSQL is running on localhost:5433"
            POSTGRES_PORT=5433
            return 0
        fi
    fi
    return 1
}

# Function to check Docker
check_docker() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        echo "✅ Docker is installed and running"
        return 0
    fi
    return 1
}

# Step 1: Environment Setup
echo ""
echo "📋 Step 1: Environment Setup"
echo "----------------------------"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/migration_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=migration_db

# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
FRONTEND_URL=http://localhost:8081

# AI/LLM Configuration (optional)
DEEPINFRA_API_KEY=

# Feature Flags
SKIP_DB_INIT=false
EOF
    echo "✅ Created .env file with default settings"
else
    echo "✅ .env file already exists"
fi

# Step 2: Database Setup
echo ""
echo "🗄️  Step 2: Database Setup"
echo "------------------------"

# Check if PostgreSQL is available
if check_postgres; then
    echo "📊 Using existing PostgreSQL installation"

    # Update .env with correct port if needed
    if [ "$POSTGRES_PORT" = "5433" ]; then
        sed -i.bak 's/localhost:5432/localhost:5433/g' .env
        sed -i.bak 's/POSTGRES_PORT=5432/POSTGRES_PORT=5433/g' .env
        echo "📝 Updated .env to use port 5433"
    fi
elif check_docker; then
    echo "🐳 PostgreSQL not found, using Docker..."

    # Start PostgreSQL in Docker
    docker run -d \
        --name migration_postgres \
        -e POSTGRES_DB=migration_db \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -p 5432:5432 \
        postgres:16-alpine || echo "⚠️  PostgreSQL container already exists"

    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 5
else
    echo "❌ Error: Neither PostgreSQL nor Docker is available"
    echo "   Please install either PostgreSQL or Docker"
    echo "   - PostgreSQL: https://www.postgresql.org/download/"
    echo "   - Docker: https://www.docker.com/get-started"
    exit 1
fi

# Step 3: Python Environment
echo ""
echo "🐍 Step 3: Python Environment"
echo "----------------------------"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Database Migrations
echo ""
echo "🔄 Step 4: Database Migrations"
echo "-----------------------------"

# Run Alembic migrations
echo "📋 Running database migrations..."
alembic upgrade head || {
    echo "⚠️  Migration failed, trying to create initial migration..."
    alembic revision --autogenerate -m "Initial migration"
    alembic upgrade head
}

# Step 5: Initialize Database
echo ""
echo "📦 Step 5: Database Initialization"
echo "---------------------------------"

echo "🌱 Initializing database with test data..."
python -c "
import asyncio
from app.core.database_initialization import initialize_database
from app.core.database import AsyncSessionLocal

async def init():
    async with AsyncSessionLocal() as db:
        await initialize_database(db)
        print('✅ Database initialized with test data')

asyncio.run(init())
"

# Step 6: Start Backend
echo ""
echo "🚀 Step 6: Starting Backend Server"
echo "---------------------------------"

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📝 Test Accounts:"
echo "   Platform Admin: chocka@gmail.com / Password123!"
echo "   Demo Users: Created automatically in development mode"
echo ""
echo "🔧 Starting backend server..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "💡 To start the frontend (in a new terminal):"
echo "   cd .. && npm install && npm run dev"
echo ""

# Start the backend
exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
