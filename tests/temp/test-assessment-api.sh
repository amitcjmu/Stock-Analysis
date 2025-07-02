#!/bin/bash

echo "Testing Assessment Flow API..."

# Test health check
echo "1. Testing backend health..."
curl -s http://localhost:8000/health | jq

# Test assessment flow initialization
echo -e "\n2. Testing assessment flow initialization..."
curl -s -X POST http://localhost:8000/api/v1/assessment-flow/initialize \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-Id: 1" \
  -H "X-Engagement-Id: 1" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "selected_application_ids": ["app1", "app2"],
    "architecture_captured": false
  }' | jq

# Check if API v3 is available
echo -e "\n3. Testing API v3 assessment flow..."
curl -s -X POST http://localhost:8000/api/v3/assessment-flow/flows \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-Id: 1" \
  -H "X-Engagement-Id: 1" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "selected_application_ids": ["app1", "app2"],
    "architecture_captured": false
  }' | jq

echo -e "\nAPI test complete!"