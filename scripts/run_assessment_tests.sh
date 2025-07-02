#!/bin/bash

# Assessment Flow Test Runner
# Comprehensive test execution script for Assessment Flow feature

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"

# Create test results directory
mkdir -p "$TEST_RESULTS_DIR"

# Default test configuration
RUN_UNIT=${RUN_UNIT:-true}
RUN_INTEGRATION=${RUN_INTEGRATION:-false}
RUN_FRONTEND=${RUN_FRONTEND:-false}
RUN_PERFORMANCE=${RUN_PERFORMANCE:-false}
GENERATE_COVERAGE=${GENERATE_COVERAGE:-true}
PARALLEL_TESTS=${PARALLEL_TESTS:-true}

# Function to show usage
show_usage() {
    echo "Assessment Flow Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --unit              Run unit tests (default: true)"
    echo "  --integration       Run integration tests (default: false)"
    echo "  --frontend          Run frontend tests (default: false)"
    echo "  --performance       Run performance tests (default: false)"
    echo "  --all               Run all test types"
    echo "  --coverage          Generate coverage report (default: true)"
    echo "  --no-coverage       Skip coverage report"
    echo "  --parallel          Run tests in parallel (default: true)"
    echo "  --sequential        Run tests sequentially"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --unit                    # Run only unit tests"
    echo "  $0 --all                     # Run all tests"
    echo "  $0 --unit --integration      # Run unit and integration tests"
    echo "  $0 --performance --no-coverage  # Run performance tests without coverage"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit)
                RUN_UNIT=true
                shift
                ;;
            --integration)
                RUN_INTEGRATION=true
                shift
                ;;
            --frontend)
                RUN_FRONTEND=true
                shift
                ;;
            --performance)
                RUN_PERFORMANCE=true
                shift
                ;;
            --all)
                RUN_UNIT=true
                RUN_INTEGRATION=true
                RUN_FRONTEND=true
                RUN_PERFORMANCE=false  # Performance tests run separately
                shift
                ;;
            --coverage)
                GENERATE_COVERAGE=true
                shift
                ;;
            --no-coverage)
                GENERATE_COVERAGE=false
                shift
                ;;
            --parallel)
                PARALLEL_TESTS=true
                shift
                ;;
            --sequential)
                PARALLEL_TESTS=false
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking test prerequisites..."
    
    # Check Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check test database is available
    if ! docker ps --format "table {{.Names}}" | grep -q "migration_test_db"; then
        log_info "Starting test database..."
        docker-compose -f docker-compose.test.yml up -d test-db
        
        # Wait for database to be ready
        log_info "Waiting for test database to be ready..."
        sleep 10
        
        local max_attempts=30
        local attempt=1
        while [ $attempt -le $max_attempts ]; do
            if docker exec migration_test_db pg_isready -U test_user -d test_assessment_db >/dev/null 2>&1; then
                log_success "Test database is ready"
                break
            else
                log_info "Waiting for test database... (attempt $attempt/$max_attempts)"
                sleep 2
                ((attempt++))
            fi
        done
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "Test database failed to start"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

# Function to run unit tests
run_unit_tests() {
    log_info "Running Assessment Flow unit tests..."
    
    local coverage_args=""
    if [ "$GENERATE_COVERAGE" = true ]; then
        coverage_args="--cov=app --cov-report=html:$TEST_RESULTS_DIR/coverage/html --cov-report=xml:$TEST_RESULTS_DIR/coverage/coverage.xml --cov-report=term"
    fi
    
    local parallel_args=""
    if [ "$PARALLEL_TESTS" = true ]; then
        parallel_args="-n auto"
    fi
    
    local test_command="pytest tests/assessment_flow/ -v --tb=short $coverage_args $parallel_args --junit-xml=$TEST_RESULTS_DIR/unit-test-results.xml"
    
    log_info "Running: $test_command"
    
    if docker-compose -f docker-compose.test.yml run --rm test-backend $test_command; then
        log_success "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    log_info "Running Assessment Flow integration tests..."
    
    # Check if integration tests are enabled
    if [ "${DEEPINFRA_API_KEY:-}" = "" ]; then
        log_warning "DEEPINFRA_API_KEY not set - skipping integration tests that require real API"
    fi
    
    local test_command="pytest tests/integration/assessment_flow/ -v --tb=short -m integration --junit-xml=$TEST_RESULTS_DIR/integration-test-results.xml"
    
    log_info "Running: $test_command"
    
    if docker-compose -f docker-compose.test.yml --profile integration run --rm integration-test-backend $test_command; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Function to run frontend tests
run_frontend_tests() {
    log_info "Running Assessment Flow frontend tests..."
    
    # Start backend for frontend tests
    log_info "Starting backend for frontend tests..."
    docker-compose -f docker-compose.test.yml up -d test-backend
    
    # Wait for backend to be ready
    sleep 5
    
    local test_command="npm run test:assessment-flow"
    
    log_info "Running: $test_command"
    
    if docker-compose -f docker-compose.test.yml --profile frontend run --rm test-frontend $test_command; then
        log_success "Frontend tests passed"
        return 0
    else
        log_error "Frontend tests failed"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    log_info "Running Assessment Flow performance tests..."
    
    local test_command="pytest tests/performance/assessment_flow/ -v --tb=short -m performance --junit-xml=$TEST_RESULTS_DIR/performance-test-results.xml"
    
    log_info "Running: $test_command"
    
    if docker-compose -f docker-compose.test.yml --profile performance run --rm performance-test-backend $test_command; then
        log_success "Performance tests passed"
        return 0
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Function to generate test reports
generate_reports() {
    log_info "Generating test reports..."
    
    # Create test summary
    local summary_file="$TEST_RESULTS_DIR/test-summary.txt"
    
    {
        echo "Assessment Flow Test Summary"
        echo "=========================="
        echo "Generated: $(date)"
        echo ""
        
        echo "Test Results:"
        if [ -f "$TEST_RESULTS_DIR/unit-test-results.xml" ]; then
            echo "✓ Unit tests: COMPLETED"
        fi
        
        if [ -f "$TEST_RESULTS_DIR/integration-test-results.xml" ]; then
            echo "✓ Integration tests: COMPLETED"
        fi
        
        if [ -f "$TEST_RESULTS_DIR/performance-test-results.xml" ]; then
            echo "✓ Performance tests: COMPLETED"
        fi
        
        echo ""
        echo "Reports Location:"
        echo "- Test Results: $TEST_RESULTS_DIR/"
        
        if [ "$GENERATE_COVERAGE" = true ] && [ -d "$TEST_RESULTS_DIR/coverage" ]; then
            echo "- Coverage Report: $TEST_RESULTS_DIR/coverage/html/index.html"
        fi
        
    } > "$summary_file"
    
    log_success "Test summary generated: $summary_file"
    
    # Display summary
    cat "$summary_file"
}

# Function to cleanup
cleanup() {
    log_info "Cleaning up test environment..."
    
    # Stop test containers
    docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
    
    # Clean up any temporary files
    docker system prune -f >/dev/null 2>&1 || true
    
    log_success "Cleanup completed"
}

# Main execution function
main() {
    echo "=========================================="
    echo "Assessment Flow Test Runner"
    echo "=========================================="
    
    # Parse command line arguments
    parse_args "$@"
    
    # Setup
    check_prerequisites
    
    # Test execution tracking
    local tests_run=0
    local tests_passed=0
    local tests_failed=0
    
    # Run selected test suites
    if [ "$RUN_UNIT" = true ]; then
        ((tests_run++))
        if run_unit_tests; then
            ((tests_passed++))
        else
            ((tests_failed++))
        fi
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        ((tests_run++))
        if run_integration_tests; then
            ((tests_passed++))
        else
            ((tests_failed++))
        fi
    fi
    
    if [ "$RUN_FRONTEND" = true ]; then
        ((tests_run++))
        if run_frontend_tests; then
            ((tests_passed++))
        else
            ((tests_failed++))
        fi
    fi
    
    if [ "$RUN_PERFORMANCE" = true ]; then
        ((tests_run++))
        if run_performance_tests; then
            ((tests_passed++))
        else
            ((tests_failed++))
        fi
    fi
    
    # Generate reports
    generate_reports
    
    # Final summary
    echo ""
    echo "=========================================="
    echo "Test Execution Summary"
    echo "=========================================="
    echo "Tests Run: $tests_run"
    echo "Tests Passed: $tests_passed"
    echo "Tests Failed: $tests_failed"
    
    if [ $tests_failed -gt 0 ]; then
        log_error "Some tests failed!"
        cleanup
        exit 1
    else
        log_success "All tests passed!"
        cleanup
        exit 0
    fi
}

# Trap for cleanup on exit
trap cleanup EXIT

# Run main function with all arguments
main "$@"