#!/bin/bash

# Fix PostgreSQL Volume Mounting Issues
# This script addresses postgres volume mounting errors in Docker

set -e

echo "🔧 Starting PostgreSQL Volume Fix..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Stop all services
print_status "Stopping all Docker services..."
docker-compose down || true

# Step 2: Remove any problematic volumes
print_status "Removing problematic volumes..."
docker volume rm aiforce-modernize_postgres_data || true
docker volume rm migrate-ui-orchestrator_postgres_data || true

# Step 3: Check for and backup existing postgres-data-volume directory
if [ -d "postgres-data-volume" ]; then
    print_warning "Found existing postgres-data-volume directory"
    print_status "Creating backup of existing postgres data..."

    # Create backups directory if it doesn't exist
    mkdir -p backups

    # Create timestamped backup
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    tar -czf "backups/postgres-data-backup_${TIMESTAMP}.tar.gz" postgres-data-volume/

    print_status "PostgreSQL data backed up to: backups/postgres-data-backup_${TIMESTAMP}.tar.gz"

    # Remove the problematic directory
    print_status "Removing problematic postgres-data-volume directory..."
    rm -rf postgres-data-volume
fi

# Step 4: Clean up any Docker system artifacts
print_status "Cleaning up Docker system artifacts..."
docker system prune -f --volumes || true

# Step 5: Verify config/docker/docker-compose.override.yml configuration
print_status "Verifying config/docker/docker-compose.override.yml configuration..."
if grep -q "device: \${PWD}/postgres-data-volume" config/docker/docker-compose.override.yml; then
    print_error "Found problematic bind mount configuration in config/docker/docker-compose.override.yml"
    print_error "This should have been fixed. Please check the override file."
    exit 1
else
    print_status "✅ Docker-compose override configuration looks correct"
fi

# Step 6: Create fresh volumes and start services
print_status "Creating fresh volumes and starting services..."
docker-compose up -d postgres

# Step 7: Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
sleep 15

# Step 8: Check if PostgreSQL is running
if docker ps | grep -q "migration_postgres.*Up"; then
    print_status "✅ PostgreSQL container is running successfully!"

    # Test database connection
    print_status "Testing database connection..."
    if docker-compose exec -T postgres pg_isready -U postgres; then
        print_status "✅ Database connection successful!"
    else
        print_warning "Database connection test failed, but container is running"
    fi

    # Show PostgreSQL logs
    print_status "Recent PostgreSQL logs:"
    docker-compose logs --tail=10 postgres

else
    print_error "❌ PostgreSQL container failed to start. Checking logs..."
    docker-compose logs postgres
    exit 1
fi

# Step 9: Start remaining services
print_status "Starting remaining services..."
docker-compose up -d

# Step 10: Final verification
print_status "Final verification - checking all services..."
sleep 10

if docker-compose ps | grep -q "Up"; then
    print_status "🎉 All services are running successfully!"
    print_status "PostgreSQL volume fix completed successfully!"

    # Show status
    print_status "Service status:"
    docker-compose ps

    print_status "You can now access:"
    print_status "- Frontend: http://localhost:8081"
    print_status "- Backend API: http://localhost:8000"
    print_status "- PostgreSQL: localhost:5433"

else
    print_error "Some services failed to start. Please check the logs:"
    docker-compose logs
    exit 1
fi

print_status "🔧 PostgreSQL volume fix completed!"
