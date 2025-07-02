#!/bin/bash

echo "Testing Assessment Flow API with Authentication..."

# First, login to get auth token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chocka@gmail.com",
    "password": "Password123!"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token.access_token')
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "Login failed:"
  echo $LOGIN_RESPONSE | jq
  exit 1
fi

echo "Login successful! Token: ${TOKEN:0:20}..."

# Test assessment flow initialization with auth
echo -e "\n2. Testing assessment flow initialization..."
curl -s -X POST http://localhost:8000/api/v1/assessment-flow/initialize \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-Id: 55f4a7eb-de00-de00-de00-888ed4f8e05d" \
  -H "X-Engagement-Id: 59e0e675-de00-de00-de00-29245dcbc79f" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "selected_application_ids": ["app1", "app2"],
    "architecture_captured": false
  }' | jq

echo -e "\nAPI test complete!"