#!/bin/bash

# Discovery Flow Test Runner
# This script provides convenient commands for running Discovery Flow tests

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
CONTAINER_NAME="migration_backend_dev"
TEST_PATH="tests/"
COVERAGE=false
VERBOSE=false
MARKERS=""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[Discovery Tests]${NC} $1"
}

print_error() {
    echo -e "${RED}[Error]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[Warning]${NC} $1"
}

# Function to check if container is running
check_container() {
    if ! docker ps | grep -q $CONTAINER_NAME; then
        print_error "Container $CONTAINER_NAME is not running!"
        print_status "Starting development environment..."
        docker-compose -f docker-compose.dev.yml up -d
        sleep 5
    fi
}

# Function to run tests
run_tests() {
    local cmd="pytest $TEST_PATH"

    if [ "$VERBOSE" = true ]; then
        cmd="$cmd -v"
    fi

    if [ ! -z "$MARKERS" ]; then
        cmd="$cmd -m \"$MARKERS\""
    fi

    if [ "$COVERAGE" = true ]; then
        cmd="$cmd --cov=app --cov-report=html --cov-report=term"
    fi

    print_status "Running: $cmd"
    docker exec -it $CONTAINER_NAME bash -c "$cmd"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            echo "Discovery Flow Test Runner"
            echo ""
            echo "Usage: $0 [options] [test_path]"
            echo ""
            echo "Options:"
            echo "  -h, --help          Show this help message"
            echo "  -v, --verbose       Run tests in verbose mode"
            echo "  -c, --coverage      Run with coverage report"
            echo "  -m, --markers       Run tests with specific markers (e.g., 'integration')"
            echo "  -u, --unit          Run unit tests only"
            echo "  -i, --integration   Run integration tests only"
            echo "  -s, --slow          Include slow tests"
            echo "  -a, --all           Run all tests including slow ones"
            echo "  --sse               Run SSE event tests"
            echo "  --agent             Run agent decision tests"
            echo "  --container NAME    Use specific container (default: $CONTAINER_NAME)"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run all discovery tests"
            echo "  $0 -v -c                              # Verbose with coverage"
            echo "  $0 -i                                 # Integration tests only"
            echo "  $0 tests/integration/test_discovery_agent_decisions.py  # Specific file"
            echo ""
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -u|--unit)
            MARKERS="unit"
            shift
            ;;
        -i|--integration)
            MARKERS="integration"
            shift
            ;;
        -s|--slow)
            MARKERS="slow"
            shift
            ;;
        -a|--all)
            MARKERS=""
            shift
            ;;
        --sse)
            TEST_PATH="tests/ -k sse"
            shift
            ;;
        --agent)
            TEST_PATH="tests/integration/test_discovery_agent_decisions.py"
            shift
            ;;
        --container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

# Main execution
print_status "Discovery Flow Test Runner"
print_status "Checking container status..."
check_container

print_status "Running tests..."
run_tests

if [ "$COVERAGE" = true ]; then
    print_status "Coverage report generated in htmlcov/index.html"
    print_status "To view: docker cp $CONTAINER_NAME:/app/htmlcov ./htmlcov"
fi

print_status "Tests completed!"
