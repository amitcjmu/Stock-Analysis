#!/bin/bash

# Test CMDB Import Process
# Simulates the frontend flow to debug import issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test data
TEST_DATA='{
  "analysis_type": "data_source_analysis",
  "data_source": {
    "file_data": [
      {"Asset_Name": "server-01", "CI_Type": "Server", "Environment": "Production", "Owner": "IT Team"},
      {"Asset_Name": "app-web-01", "CI_Type": "Application", "Environment": "Development", "Owner": "Dev Team"},
      {"Asset_Name": "db-prod-01", "CI_Type": "Database", "Environment": "Production", "Owner": "DBA Team"}
    ],
    "headers": ["Asset_Name", "CI_Type", "Environment", "Owner"],
    "filename": "test_cmdb_export.csv",
    "total_records": 3,
    "sample_size": 3
  },
  "options": {
    "include_field_mapping": true,
    "include_quality_assessment": true,
    "confidence_threshold": 0.7
  }
}'

FLOW_DATA='{
  "headers": ["Asset_Name", "CI_Type", "Environment", "Owner"],
  "sample_data": [
    {"Asset_Name": "server-01", "CI_Type": "Server", "Environment": "Production", "Owner": "IT Team"},
    {"Asset_Name": "app-web-01", "CI_Type": "Application", "Environment": "Development", "Owner": "Dev Team"},
    {"Asset_Name": "db-prod-01", "CI_Type": "Database", "Environment": "Production", "Owner": "DBA Team"}
  ],
  "filename": "test_cmdb_export.csv",
  "options": {
    "auto_proceed": true,
    "include_recommendations": true,
    "enable_learning": true
  }
}'

# Test backend health
test_backend_health() {
    print_status "Testing backend health..."

    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend is healthy"
    else
        print_error "Backend is not accessible"
        exit 1
    fi
}

# Test monitoring endpoints
test_monitoring() {
    print_status "Testing monitoring endpoints..."

    # Test agent status
    print_status "Checking agent status..."
    AGENT_STATUS=$(curl -s http://localhost:8000/api/v1/monitoring/status)
    TOTAL_AGENTS=$(echo "$AGENT_STATUS" | jq -r '.agents.total_registered // 0')
    ACTIVE_AGENTS=$(echo "$AGENT_STATUS" | jq -r '.agents.active_agents // 0')

    print_success "Total agents: $TOTAL_AGENTS, Active agents: $ACTIVE_AGENTS"

    # Test CrewAI flows
    print_status "Checking CrewAI flow service..."
    FLOW_STATUS=$(curl -s http://localhost:8000/api/v1/monitoring/crewai-flows)
    SERVICE_STATUS=$(echo "$FLOW_STATUS" | jq -r '.crewai_flows.service_health.status // "unknown"')
    ACTIVE_FLOWS=$(echo "$FLOW_STATUS" | jq -r '.crewai_flows.active_flows | length')

    print_success "CrewAI service status: $SERVICE_STATUS, Active flows: $ACTIVE_FLOWS"
}

# Test file analysis endpoint
test_file_analysis() {
    print_status "Testing file analysis endpoint..."

    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "X-Client-Account-Id: bafd5b46-aaaf-4c95-8142-573699d93171" \
        -H "X-Engagement-Id: 6e9c8133-4169-4b79-b052-106dc93d0208" \
        -d "$TEST_DATA" \
        http://localhost:8000/api/v1/unified-discovery/flow/agent/analysis)

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        print_success "File analysis endpoint working"
        ANALYSIS_ID=$(echo "$RESPONSE" | jq -r '.analysis_id // "unknown"')
        print_status "Analysis ID: $ANALYSIS_ID"
    else
        print_error "File analysis failed"
        echo "Response: $RESPONSE" | jq '.' || echo "$RESPONSE"
        return 1
    fi
}

# Test discovery flow initiation
test_discovery_flow() {
    print_status "Testing discovery flow initiation..."

    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "X-Client-Account-Id: bafd5b46-aaaf-4c95-8142-573699d93171" \
        -H "X-Engagement-Id: 6e9c8133-4169-4b79-b052-106dc93d0208" \
        -d "$FLOW_DATA" \
        http://localhost:8000/api/v1/unified-discovery/flow/run)

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        print_success "Discovery flow initiated"
        SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id // .flow_id // "unknown"')
        print_status "Session ID: $SESSION_ID"

        # Test flow status polling
        test_flow_status "$SESSION_ID"
    else
        print_error "Discovery flow initiation failed"
        echo "Response: $RESPONSE" | jq '.' || echo "$RESPONSE"
        return 1
    fi
}

# Test flow status polling
test_flow_status() {
    local session_id="$1"
    print_status "Testing flow status polling for session: $session_id"

    # Poll status for up to 60 seconds
    for i in {1..12}; do
        print_status "Polling attempt $i/12..."

        RESPONSE=$(curl -s \
            -H "X-Client-Account-Id: bafd5b46-aaaf-4c95-8142-573699d93171" \
            -H "X-Engagement-Id: 6e9c8133-4169-4b79-b052-106dc93d0208" \
            "http://localhost:8000/api/v1/unified-discovery/flow/$session_id/status")

        if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
            STATUS=$(echo "$RESPONSE" | jq -r '.flow_status.status // "unknown"')
            PHASE=$(echo "$RESPONSE" | jq -r '.flow_status.current_phase // "unknown"')
            PROGRESS=$(echo "$RESPONSE" | jq -r '.flow_status.progress_percentage // 0')

            print_status "Status: $STATUS, Phase: $PHASE, Progress: $PROGRESS%"

            if [ "$STATUS" = "completed" ]; then
                print_success "Flow completed successfully!"

                # Get final results
                print_status "Retrieving final results..."
                RESULTS=$(curl -s \
                    -H "X-Client-Account-Id: bafd5b46-aaaf-4c95-8142-573699d93171" \
                    -H "X-Engagement-Id: 6e9c8133-4169-4b79-b052-106dc93d0208" \
                    "http://localhost:8000/api/v1/unified-discovery/flow/$session_id/status")

                if echo "$RESULTS" | jq -e '.success' > /dev/null 2>&1; then
                    print_success "Results retrieved successfully"
                    MAPPED_FIELDS=$(echo "$RESULTS" | jq -r '.flow_state.results.field_mapping.mapped_fields // 0')
                    CLASSIFIED_ASSETS=$(echo "$RESULTS" | jq -r '.flow_state.results.asset_classification.classified_assets // 0')
                    print_status "Mapped fields: $MAPPED_FIELDS, Classified assets: $CLASSIFIED_ASSETS"
                else
                    print_warning "Could not retrieve final results"
                    echo "$RESULTS" | jq '.' || echo "$RESULTS"
                fi
                return 0
            elif [ "$STATUS" = "failed" ] || [ "$STATUS" = "error" ]; then
                print_error "Flow failed with status: $STATUS"
                echo "$RESPONSE" | jq '.flow_status.errors // []'
                return 1
            fi
        else
            print_warning "Status polling failed"
            echo "Response: $RESPONSE" | jq '.' || echo "$RESPONSE"
        fi

        sleep 5
    done

    print_warning "Flow did not complete within 60 seconds"
    return 1
}

# Main execution
main() {
    echo "🧪 CMDB Import Process Testing"
    echo "=============================="

    test_backend_health
    test_monitoring

    print_status "Starting CMDB import simulation..."

    # Test the full flow
    if test_file_analysis; then
        print_status "File analysis passed, proceeding to discovery flow..."
        test_discovery_flow
    else
        print_error "File analysis failed, cannot proceed"
        exit 1
    fi

    print_success "CMDB import testing completed!"
}

# Run main function
main "$@"
