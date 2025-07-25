#!/bin/bash
"""
Docker Validation Runner for CrewAI Flow Migration
Starts Docker containers and runs comprehensive validation tests.
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
VALIDATION_SCRIPT="$SCRIPT_DIR/validate_crewai_flow_migration.py"

# Default values
VERBOSE=false
QUICK=false
CLEANUP=true
WAIT_TIME=30

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if containers are healthy
wait_for_containers() {
    print_status "Waiting for containers to be healthy..."

    local max_attempts=60  # 5 minutes max
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        print_status "Health check attempt $attempt/$max_attempts"

        # Check backend health
        if curl -s -f "$BACKEND_URL/health" >/dev/null 2>&1; then
            print_success "Backend is healthy"

            # Check CrewAI Flow service health
            if curl -s -f "$BACKEND_URL/api/v1/discovery/flow/health" >/dev/null 2>&1; then
                print_success "CrewAI Flow service is healthy"
                return 0
            else
                print_warning "CrewAI Flow service not ready yet..."
            fi
        else
            print_warning "Backend not ready yet..."
        fi

        sleep 5
        ((attempt++))
    done

    print_error "Containers failed to become healthy within timeout"
    return 1
}

# Function to start Docker containers
start_containers() {
    print_status "Starting Docker containers..."

    cd "$PROJECT_ROOT"

    # Stop any existing containers
    docker-compose down --remove-orphans >/dev/null 2>&1 || true

    # Build and start containers
    print_status "Building and starting containers..."
    docker-compose up -d --build

    if [ $? -eq 0 ]; then
        print_success "Containers started successfully"

        # Wait for containers to be healthy
        if wait_for_containers; then
            print_success "All containers are healthy and ready"
            return 0
        else
            print_error "Containers failed health checks"
            return 1
        fi
    else
        print_error "Failed to start containers"
        return 1
    fi
}

# Function to stop Docker containers
stop_containers() {
    if [ "$CLEANUP" = true ]; then
        print_status "Stopping Docker containers..."
        cd "$PROJECT_ROOT"
        docker-compose down --remove-orphans
        print_success "Containers stopped"
    else
        print_status "Skipping container cleanup (--no-cleanup specified)"
    fi
}

# Function to run validation tests
run_validation() {
    print_status "Running CrewAI Flow migration validation tests..."

    # Prepare validation command
    local validation_cmd="python3 $VALIDATION_SCRIPT --url $BACKEND_URL"

    if [ "$VERBOSE" = true ]; then
        validation_cmd="$validation_cmd --verbose"
    fi

    if [ "$QUICK" = true ]; then
        validation_cmd="$validation_cmd --quick"
    fi

    # Add output file
    local output_file="$PROJECT_ROOT/validation_results_$(date +%Y%m%d_%H%M%S).json"
    validation_cmd="$validation_cmd --output $output_file"

    print_status "Running: $validation_cmd"

    # Run validation
    if eval "$validation_cmd"; then
        print_success "All validation tests passed!"
        print_status "Results saved to: $output_file"
        return 0
    else
        print_error "Some validation tests failed"
        print_status "Results saved to: $output_file"
        return 1
    fi
}

# Function to show container logs
show_logs() {
    print_status "Showing container logs..."
    cd "$PROJECT_ROOT"

    echo -e "\n${BLUE}=== Backend Logs ===${NC}"
    docker-compose logs --tail=50 backend

    echo -e "\n${BLUE}=== Database Logs ===${NC}"
    docker-compose logs --tail=20 db
}

# Function to run quick health check
quick_health_check() {
    print_status "Running quick health check..."

    # Check backend
    if curl -s -f "$BACKEND_URL/health" >/dev/null 2>&1; then
        print_success "Backend is responding"
    else
        print_error "Backend is not responding"
        return 1
    fi

    # Check CrewAI Flow service
    if curl -s -f "$BACKEND_URL/api/v1/discovery/flow/health" >/dev/null 2>&1; then
        print_success "CrewAI Flow service is responding"
    else
        print_error "CrewAI Flow service is not responding"
        return 1
    fi

    return 0
}

# Function to show usage
show_usage() {
    cat << EOF
Docker Validation Runner for CrewAI Flow Migration

Usage: $0 [OPTIONS]

OPTIONS:
    --verbose, -v       Enable verbose output
    --quick, -q         Run quick validation (skip performance tests)
    --no-cleanup        Don't stop containers after validation
    --logs              Show container logs after validation
    --health-only       Only run health checks, don't start containers
    --help, -h          Show this help message

EXAMPLES:
    $0                  # Run full validation with container startup
    $0 --verbose        # Run with verbose output
    $0 --quick          # Run quick validation
    $0 --health-only    # Only check if existing containers are healthy
    $0 --no-cleanup     # Keep containers running after validation

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --quick|-q)
            QUICK=true
            shift
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --health-only)
            HEALTH_ONLY=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Starting Docker Validation for CrewAI Flow Migration"
    print_status "Project root: $PROJECT_ROOT"
    print_status "Backend URL: $BACKEND_URL"

    # Check Docker
    check_docker

    # Check if validation script exists
    if [ ! -f "$VALIDATION_SCRIPT" ]; then
        print_error "Validation script not found: $VALIDATION_SCRIPT"
        exit 1
    fi

    # Health-only mode
    if [ "$HEALTH_ONLY" = true ]; then
        print_status "Running health-only check..."
        if quick_health_check; then
            print_success "Health check passed"
            exit 0
        else
            print_error "Health check failed"
            exit 1
        fi
    fi

    # Trap to ensure cleanup on exit
    if [ "$CLEANUP" = true ]; then
        trap stop_containers EXIT
    fi

    # Start containers
    if ! start_containers; then
        print_error "Failed to start containers"
        exit 1
    fi

    # Run validation
    local validation_result=0
    if ! run_validation; then
        validation_result=1
    fi

    # Show logs if requested
    if [ "$SHOW_LOGS" = true ]; then
        show_logs
    fi

    # Final status
    if [ $validation_result -eq 0 ]; then
        print_success "🎉 Docker validation completed successfully!"
        print_status "CrewAI Flow migration is working correctly in Docker environment"
    else
        print_error "🚨 Docker validation failed"
        print_status "Check the logs and validation results for details"
    fi

    exit $validation_result
}

# Run main function
main "$@"
