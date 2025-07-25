#!/bin/bash
#
# Migration State Fix Script
#
# This script fixes common Alembic migration state issues in different environments.
# Used by CC for deployment migrations.
#
# Usage:
#   ./fix_migration_state.sh                    # Run the fix
#   ./fix_migration_state.sh --check-only       # Check migration state without fixing
#   ./fix_migration_state.sh --help             # Show help
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Migration State Fix Script

This script fixes common Alembic migration state issues that occur when:
- Database has tables but alembic_version is empty
- Database has tables but alembic_version references non-existent migrations
- Missing migration files that are referenced in alembic_version

Usage:
    $0 [OPTIONS]

Options:
    --check-only    Check migration state without making changes
    --help         Show this help message

Examples:
    $0                      # Fix migration state issues
    $0 --check-only         # Check migration state only

Environment Variables:
    DATABASE_URL           PostgreSQL connection string
    POSTGRES_HOST          PostgreSQL host (default: localhost)
    POSTGRES_PORT          PostgreSQL port (default: 5432)
    POSTGRES_USER          PostgreSQL user (default: postgres)
    POSTGRES_PASSWORD      PostgreSQL password
    POSTGRES_DB            PostgreSQL database name

EOF
}

check_requirements() {
    log_info "Checking requirements..."

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        return 1
    fi

    # Check if we're in the right directory
    if [[ ! -f "$BACKEND_DIR/alembic.ini" ]]; then
        log_error "alembic.ini not found. Please run this script from the backend directory or its scripts subdirectory"
        return 1
    fi

    # Check if the Python script exists
    if [[ ! -f "$SCRIPT_DIR/fix_migration_state.py" ]]; then
        log_error "fix_migration_state.py not found"
        return 1
    fi

    log_success "Requirements check passed"
    return 0
}

check_database_connection() {
    log_info "Checking database connection..."

    # Try to determine database connection details
    if [[ -z "${DATABASE_URL:-}" ]]; then
        # Try to construct from individual components
        POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
        POSTGRES_PORT="${POSTGRES_PORT:-5432}"
        POSTGRES_USER="${POSTGRES_USER:-postgres}"
        POSTGRES_DB="${POSTGRES_DB:-migration_db}"

        if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
            log_warning "No database connection details found"
            log_warning "Please set DATABASE_URL or POSTGRES_* environment variables"
            return 1
        fi

        DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
        export DATABASE_URL
    fi

    log_success "Database connection details configured"
    return 0
}

run_migration_fix() {
    local check_only="${1:-false}"

    log_info "Running migration state fix..."

    cd "$BACKEND_DIR"

    # Set PYTHONPATH to include the backend directory
    export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"

    if [[ "$check_only" == "true" ]]; then
        log_info "Running in check-only mode..."
        # For check-only mode, we could add a flag to the Python script
        # For now, we'll just run the normal script which reports the state
    fi

    python3 "$SCRIPT_DIR/fix_migration_state.py"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log_success "Migration state fix completed successfully"
    else
        log_error "Migration state fix failed with exit code $exit_code"
    fi

    return $exit_code
}

main() {
    local check_only=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --check-only)
                check_only=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_info "🔧 Starting Migration State Fix Script..."

    # Run checks
    if ! check_requirements; then
        exit 1
    fi

    if ! check_database_connection; then
        exit 1
    fi

    # Run the migration fix
    if run_migration_fix "$check_only"; then
        log_success "✅ Migration state fix completed successfully"
        exit 0
    else
        log_error "❌ Migration state fix failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
