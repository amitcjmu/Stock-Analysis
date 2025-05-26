#!/bin/bash

# AI Force Migration Platform Setup Script
# This script sets up the development environment for both local and Docker deployment

set -e

echo "🚀 Setting up AI Force Migration Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose are available"

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Detected Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    print_warning "Python $PYTHON_VERSION detected. CrewAI requires Python 3.10+."
    print_warning "Local development will use placeholder AI logic."
    print_warning "Docker will use Python 3.11 with full CrewAI support."
fi

# Setup backend virtual environment
echo "📦 Setting up Python virtual environment..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_status "Python dependencies installed in virtual environment (without CrewAI for Python < 3.10)"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp env.example .env
    print_status "Environment file created from template"
    print_warning "Please update .env file with your configuration"
fi

cd ..

# Setup frontend dependencies
echo "📦 Setting up Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    npm install
    print_status "Node.js dependencies installed"
fi

echo ""
echo "🎉 Setup complete! Choose your deployment method:"
echo ""
echo "📋 OPTION 1: Local Development (with your existing PostgreSQL)"
echo "   1. Make sure PostgreSQL is running locally"
echo "   2. Create database: createdb migration_db"
echo "   3. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "   4. Start frontend: npm run dev"
echo ""
echo "📋 OPTION 2: Docker Development (recommended)"
echo "   1. Start all services: docker-compose up -d"
echo "   2. View logs: docker-compose logs -f"
echo "   3. Stop services: docker-compose down"
echo ""
echo "📋 OPTION 3: Railway Deployment"
echo "   1. Connect your GitHub repo to Railway"
echo "   2. Add PostgreSQL service in Railway"
echo "   3. Set environment variables in Railway dashboard"
echo "   4. Deploy automatically on git push"
echo ""
echo "🌐 Access URLs:"
echo "   - Frontend: http://localhost:8081 (Fixed Port)"
echo "   - Backend API: http://localhost:8000 (Fixed Port)"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
print_status "Setup script completed successfully!" 