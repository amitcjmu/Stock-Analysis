#!/bin/bash

# Test script for unmapped assets API enhancement
# Tests with Demo Corporation tenant data

set -e

BASE_URL="http://localhost:8000"
API_ENDPOINT="${BASE_URL}/api/v1/canonical-applications"

# Use Demo Corporation tenant IDs
CLIENT_ACCOUNT_ID="11111111-1111-1111-1111-111111111111"
ENGAGEMENT_ID="22222222-2222-2222-2222-222222222222"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing Canonical Applications API with Demo Corporation ===${NC}\n"

# Test 1: Default behavior (without include_unmapped_assets)
echo -e "${YELLOW}Test 1: Default behavior (include_unmapped_assets=false)${NC}"
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}?page=1&page_size=10" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: ${CLIENT_ACCOUNT_ID}" \
  -H "X-Engagement-ID: ${ENGAGEMENT_ID}")

echo "Response structure:"
echo "$RESPONSE" | jq '{total, canonical_apps_count, unmapped_assets_count, page, page_size, total_pages, app_count: (.applications | length)}'

CANONICAL_COUNT=$(echo "$RESPONSE" | jq -r '.canonical_apps_count // "missing"')
UNMAPPED_COUNT=$(echo "$RESPONSE" | jq -r '.unmapped_assets_count // "missing"')

if [ "$CANONICAL_COUNT" != "missing" ]; then
  echo -e "${GREEN}✅ PASS: canonical_apps_count present: $CANONICAL_COUNT${NC}"
else
  echo -e "${RED}❌ FAIL: canonical_apps_count missing${NC}"
fi

if [ "$UNMAPPED_COUNT" != "missing" ]; then
  echo -e "${GREEN}✅ PASS: unmapped_assets_count present: $UNMAPPED_COUNT${NC}"
  if [ "$UNMAPPED_COUNT" = "0" ]; then
    echo -e "${GREEN}✅ PASS: No unmapped assets included (as expected)${NC}"
  fi
else
  echo -e "${RED}❌ FAIL: unmapped_assets_count missing${NC}"
fi

echo ""

# Test 2: With include_unmapped_assets=true
echo -e "${YELLOW}Test 2: With include_unmapped_assets=true${NC}"
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}?page=1&page_size=20&include_unmapped_assets=true" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: ${CLIENT_ACCOUNT_ID}" \
  -H "X-Engagement-ID: ${ENGAGEMENT_ID}")

echo "Response structure:"
echo "$RESPONSE" | jq '{total, canonical_apps_count, unmapped_assets_count, page, page_size, total_pages, app_count: (.applications | length)}'

CANONICAL_COUNT=$(echo "$RESPONSE" | jq -r '.canonical_apps_count // "missing"')
UNMAPPED_COUNT=$(echo "$RESPONSE" | jq -r '.unmapped_assets_count // "missing"')
TOTAL=$(echo "$RESPONSE" | jq -r '.total // "missing"')

if [ "$CANONICAL_COUNT" != "missing" ]; then
  echo -e "${GREEN}✅ PASS: canonical_apps_count: $CANONICAL_COUNT${NC}"
else
  echo -e "${RED}❌ FAIL: canonical_apps_count missing${NC}"
fi

if [ "$UNMAPPED_COUNT" != "missing" ]; then
  echo -e "${GREEN}✅ PASS: unmapped_assets_count: $UNMAPPED_COUNT${NC}"

  if [ "$UNMAPPED_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ SUCCESS: Found $UNMAPPED_COUNT unmapped assets!${NC}"
  else
    echo -e "${YELLOW}⚠️  WARNING: No unmapped assets found${NC}"
  fi
else
  echo -e "${RED}❌ FAIL: unmapped_assets_count missing${NC}"
fi

# Show unmapped assets details
UNMAPPED_ASSETS=$(echo "$RESPONSE" | jq -r '.applications[] | select(.is_unmapped_asset == true)')
if [ -n "$UNMAPPED_ASSETS" ]; then
  echo -e "\n${BLUE}Unmapped Assets Found:${NC}"
  echo "$UNMAPPED_ASSETS" | jq -s '.[] | {asset_name, asset_type, discovery_status, assessment_readiness, mapped_to_application_name}'

  # Check for mapped assets
  MAPPED_ASSETS=$(echo "$UNMAPPED_ASSETS" | jq -s '[.[] | select(.mapped_to_application_id != null)]')
  MAPPED_COUNT=$(echo "$MAPPED_ASSETS" | jq 'length')

  if [ "$MAPPED_COUNT" -gt "0" ]; then
    echo -e "\n${BLUE}Assets Already Mapped to Applications:${NC}"
    echo "$MAPPED_ASSETS" | jq '.[] | {asset_name, asset_type, mapped_to_application_name}'
  fi
else
  echo -e "${YELLOW}No unmapped assets found in response${NC}"
fi

echo ""

# Test 3: Search for specific asset types
echo -e "${YELLOW}Test 3: Search for 'Database' with unmapped assets${NC}"
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}?page=1&page_size=20&include_unmapped_assets=true&search=Database" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: ${CLIENT_ACCOUNT_ID}" \
  -H "X-Engagement-ID: ${ENGAGEMENT_ID}")

echo "Search results:"
echo "$RESPONSE" | jq '{total, canonical_apps_count, unmapped_assets_count}'

DATABASE_ASSETS=$(echo "$RESPONSE" | jq -r '.applications[] | select(.is_unmapped_asset == true and .asset_type == "database")')
if [ -n "$DATABASE_ASSETS" ]; then
  echo -e "${GREEN}✅ PASS: Found database assets in search${NC}"
  echo "$DATABASE_ASSETS" | jq -s '.[] | {asset_name, asset_type}'
else
  echo -e "${YELLOW}⚠️  No database assets found${NC}"
fi

echo ""

# Test 4: Verify asset type filtering
echo -e "${YELLOW}Test 4: Verify only non-application assets are returned${NC}"
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}?page=1&page_size=20&include_unmapped_assets=true" \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: ${CLIENT_ACCOUNT_ID}" \
  -H "X-Engagement-ID: ${ENGAGEMENT_ID}")

APPLICATION_TYPE_IN_UNMAPPED=$(echo "$RESPONSE" | jq -r '.applications[] | select(.is_unmapped_asset == true and .asset_type == "application")')
if [ -z "$APPLICATION_TYPE_IN_UNMAPPED" ]; then
  echo -e "${GREEN}✅ PASS: No application-type assets in unmapped assets${NC}"
else
  echo -e "${RED}❌ FAIL: Found application-type assets in unmapped section${NC}"
  echo "$APPLICATION_TYPE_IN_UNMAPPED" | jq -s '.'
fi

echo ""
echo -e "${GREEN}=== All Tests Completed ===${NC}"
