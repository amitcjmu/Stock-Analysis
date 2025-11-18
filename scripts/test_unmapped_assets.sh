#!/bin/bash

# Test script for unmapped assets API enhancement
# Tests the new include_unmapped_assets parameter

set -e

BASE_URL="http://localhost:8000"
API_ENDPOINT="${BASE_URL}/api/v1/canonical-applications"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing Canonical Applications API with Unmapped Assets ===${NC}\n"

# Test 1: Default behavior (without include_unmapped_assets)
echo -e "${YELLOW}Test 1: Default behavior (include_unmapped_assets=false)${NC}"
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}?page=1&page_size=10" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 00000000-0000-0000-0000-000000000001" \
  -H "X-Engagement-ID: 00000000-0000-0000-0000-000000000001")

echo "Response:"
echo "$RESPONSE" | jq '.'

# Check if response has expected structure
CANONICAL_COUNT=$(echo "$RESPONSE" | jq -r '.canonical_apps_count // "missing"')
UNMAPPED_COUNT=$(echo "$RESPONSE" | jq -r '.unmapped_assets_count // "missing"')

if [ "$CANONICAL_COUNT" = "missing" ]; then
  echo -e "${RED}❌ FAIL: canonical_apps_count missing${NC}\n"
else
  echo -e "${GREEN}✅ PASS: canonical_apps_count present: $CANONICAL_COUNT${NC}\n"
fi

if [ "$UNMAPPED_COUNT" = "missing" ]; then
  echo -e "${RED}❌ FAIL: unmapped_assets_count missing${NC}\n"
else
  echo -e "${GREEN}✅ PASS: unmapped_assets_count present: $UNMAPPED_COUNT${NC}\n"
fi

# Test 2: With include_unmapped_assets=true
echo -e "${YELLOW}Test 2: With include_unmapped_assets=true${NC}"
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}?page=1&page_size=10&include_unmapped_assets=true" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 00000000-0000-0000-0000-000000000001" \
  -H "X-Engagement-ID: 00000000-0000-0000-0000-000000000001")

echo "Response:"
echo "$RESPONSE" | jq '.'

CANONICAL_COUNT=$(echo "$RESPONSE" | jq -r '.canonical_apps_count // "missing"')
UNMAPPED_COUNT=$(echo "$RESPONSE" | jq -r '.unmapped_assets_count // "missing"')
TOTAL=$(echo "$RESPONSE" | jq -r '.total // "missing"')

if [ "$CANONICAL_COUNT" = "missing" ]; then
  echo -e "${RED}❌ FAIL: canonical_apps_count missing${NC}\n"
else
  echo -e "${GREEN}✅ PASS: canonical_apps_count: $CANONICAL_COUNT${NC}\n"
fi

if [ "$UNMAPPED_COUNT" = "missing" ]; then
  echo -e "${RED}❌ FAIL: unmapped_assets_count missing${NC}\n"
else
  echo -e "${GREEN}✅ PASS: unmapped_assets_count: $UNMAPPED_COUNT${NC}\n"
fi

# Check if any unmapped assets exist
APPS=$(echo "$RESPONSE" | jq '.applications[]')
HAS_UNMAPPED=$(echo "$APPS" | jq 'select(.is_unmapped_asset == true)' | head -1)

if [ -n "$HAS_UNMAPPED" ]; then
  echo -e "${GREEN}✅ PASS: Found unmapped assets in response${NC}"
  echo "Sample unmapped asset:"
  echo "$HAS_UNMAPPED" | jq '.'
else
  echo -e "${YELLOW}⚠️  WARNING: No unmapped assets found (may be legitimate if no non-app assets exist)${NC}"
fi

# Test 3: Search with unmapped assets
echo -e "\n${YELLOW}Test 3: Search with unmapped assets${NC}"
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}?page=1&page_size=10&include_unmapped_assets=true&search=test" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 00000000-0000-0000-0000-000000000001" \
  -H "X-Engagement-ID: 00000000-0000-0000-0000-000000000001")

echo "Search response:"
echo "$RESPONSE" | jq '{total, canonical_apps_count, unmapped_assets_count}'

echo -e "\n${GREEN}=== All Tests Completed ===${NC}"
