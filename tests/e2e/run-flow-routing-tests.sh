#!/bin/bash

##
# Quick Flow Routing Intelligence Test Runner
#
# Runs the specific Playwright test for flow routing intelligence validation
# without the full validation suite (for faster development iteration)
##

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$TEST_DIR")")"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Flow Routing Intelligence Tests       ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Function to log with timestamp
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if Docker services are running
check_services() {
    log "${BLUE}Checking if services are running...${NC}"

    # Check frontend
    if curl -f -s http://localhost:8081 > /dev/null; then
        log "${GREEN}✅ Frontend service is accessible${NC}"
    else
        log "${RED}❌ Frontend service is not accessible at http://localhost:8081${NC}"
        log "${YELLOW}Please start Docker services with: docker-compose up -d${NC}"
        exit 1
    fi

    # Check backend
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log "${GREEN}✅ Backend service is accessible${NC}"
    else
        log "${RED}❌ Backend service is not accessible at http://localhost:8000${NC}"
        log "${YELLOW}Please start Docker services with: docker-compose up -d${NC}"
        exit 1
    fi
}

# Run specific test
run_test() {
    local test_name="$1"
    local test_file="flow-routing-intelligence-comprehensive.spec.ts"

    cd "$TEST_DIR"

    log "${BLUE}Running Flow Routing Intelligence Test: $test_name${NC}"

    if [ -n "$test_name" ]; then
        # Run specific test by name
        npx playwright test "$test_file" --grep "$test_name" --headed
    else
        # Run all tests in the file
        npx playwright test "$test_file" --headed
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 [test_name]"
    echo ""
    echo "Available tests:"
    echo "  1. 'Test 1: Original Failing Flow Recovery'"
    echo "  2. 'Test 2: Automatic Flow State Detection'"
    echo "  3. 'Test 3: Phase Transition Interception'"
    echo "  4. 'Test 4: Self-Healing Flow Navigation'"
    echo "  5. 'Test 5: Recovery Progress UI'"
    echo "  6. 'Test 6: Flow Recovery API Integration'"
    echo "  7. 'Test 7: Graceful Fallbacks'"
    echo "  8. 'Test 8: Complete E2E Flow'"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests"
    echo "  $0 'Test 1'                         # Run Test 1 specifically"
    echo "  $0 'Original Failing Flow Recovery' # Run Test 1 by partial name"
}

# Main execution
main() {
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_usage
        exit 0
    fi

    # Check if services are running
    check_services

    # Run the test
    local test_name="$1"

    if run_test "$test_name"; then
        log "${GREEN}✅ Flow Routing Intelligence Tests PASSED${NC}"
        exit 0
    else
        log "${RED}❌ Flow Routing Intelligence Tests FAILED${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
