#!/bin/bash
set -e

# AI Modernize Migration Platform - Docker Entrypoint Script
# Ensures proper database initialization before starting the application

echo "🚀 AI Modernize Migration Platform - Starting Backend Services"
echo "============================================================="

# Environment variables with defaults
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-migration_db}
DATABASE_URL=${DATABASE_URL:-postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB}

# Export for use by other scripts
export DATABASE_URL

echo "Database Configuration:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"
echo ""

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL to be ready..."

    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            return 0
        fi

        echo "   Attempt $attempt/$max_attempts: PostgreSQL not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "❌ PostgreSQL did not become ready within timeout"
    exit 1
}

# Main execution flow
main() {
    echo "Starting initialization process..."

    # Step 1: Wait for PostgreSQL
    wait_for_postgres

    # Step 2: Fix alembic version table if needed
    echo "🔧 Fixing alembic version table..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /app/scripts/fix_alembic_version.sql 2>/dev/null || true

    # Step 3: Run Alembic migrations
    # This is the standard and idempotent way to ensure the database schema is up to date.
    echo "🔧 Running database migrations..."
    alembic upgrade head

    echo ""
    echo "✅ Database setup complete! Starting application..."
    echo "============================================================="

    # Execute the main application command
    exec "$@"
}

# Handle different scenarios based on command
case "${1}" in
    "uvicorn")
        # Normal startup
        main "$@"
        ;;
    *)
        # Allows running other commands like `bash` for debugging
        exec "$@"
        ;;
esac
