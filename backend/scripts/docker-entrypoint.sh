#!/bin/bash
set -e

# AI Force Migration Platform - Docker Entrypoint Script
# Ensures proper database initialization before starting the application

echo "🚀 AI Force Migration Platform - Starting Backend Services"
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

# Function to check if database initialization is needed
check_database_state() {
    echo "🔍 Checking database state..."
    
    # Try to connect and check if tables exist
    if python -c "
import asyncio
import asyncpg
import sys
import os

async def check():
    try:
        # Get database URL and convert format for asyncpg
        db_url = os.getenv('DATABASE_URL', '')
        if 'postgresql+asyncpg://' in db_url:
            db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
            
        conn = await asyncpg.connect(db_url)
        
        # Check if any tables exist
        result = await conn.fetchval(\"\"\"
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema IN ('migration', 'public') 
            AND table_type = 'BASE TABLE'
        \"\"\")
        
        await conn.close()
        
        if result > 0:
            print(f'TABLES_EXIST:{result}')
            sys.exit(0)  # Tables exist
        else:
            print('TABLES_EXIST:0')
            sys.exit(1)  # No tables
            
    except Exception as e:
        print(f'DATABASE_ERROR:{e}')
        sys.exit(2)  # Database connection error

asyncio.run(check())
" 2>/dev/null; then
        echo "✅ Database appears to be initialized"
        return 0
    else
        echo "⚠️  Database needs initialization"
        return 1
    fi
}

# Function to initialize database
initialize_database() {
    echo "🔧 Initializing database..."
    
    # Run database initialization script
    if python scripts/init_database.py; then
        echo "✅ Database initialization completed successfully!"
    else
        echo "❌ Database initialization failed!"
        exit 1
    fi
}

# Function to run health check
run_health_check() {
    echo "🏥 Running health check..."
    
    if python scripts/init_database.py --validate-only; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed!"
        exit 1
    fi
}

# Main execution flow
main() {
    echo "Starting initialization process..."
    
    # Step 1: Wait for PostgreSQL
    wait_for_postgres
    
    # Step 2: Check if database is already initialized
    if check_database_state; then
        echo "📊 Database appears to be initialized, running health check..."
        run_health_check
    else
        echo "🔧 Database needs initialization..."
        initialize_database
    fi
    
    echo ""
    echo "✅ Database setup complete! Starting application..."
    echo "============================================================="
    
    # Execute the main application command
    exec "$@"
}

# Handle different scenarios based on command
case "${1}" in
    "init-only")
        echo "🔧 Running database initialization only..."
        wait_for_postgres
        initialize_database
        echo "✅ Database initialization complete"
        exit 0
        ;;
    "validate-only")
        echo "🏥 Running database validation only..."
        wait_for_postgres
        run_health_check
        echo "✅ Database validation complete"
        exit 0
        ;;
    "force-init")
        echo "🔥 Force initializing database..."
        wait_for_postgres
        python scripts/init_database.py --force
        echo "✅ Force initialization complete"
        exit 0
        ;;
    *)
        # Normal startup
        main "$@"
        ;;
esac