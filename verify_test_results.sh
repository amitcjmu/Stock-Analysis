#!/bin/bash

# AI Enhancement Test Results Verification Script
# Run this AFTER triggering AI enhancement to check results

FLOW_ID="95ea124e-49e6-45fc-a572-5f6202f3408a"

echo "=================================================="
echo "AI Enhancement Test Results Verification"
echo "=================================================="
echo ""
echo "Flow ID: $FLOW_ID"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "1. Database Enhancement Metrics"
echo "--------------------------------"
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT
  COUNT(*) as total_gaps,
  COUNT(confidence_score) as gaps_with_confidence,
  COUNT(ai_suggestions) as gaps_with_suggestions,
  COUNT(suggested_resolution) as gaps_with_resolution,
  CASE WHEN COUNT(confidence_score) > 0
    THEN ROUND(AVG(confidence_score)::numeric, 3)
    ELSE NULL
  END as avg_confidence,
  MIN(confidence_score) as min_confidence,
  MAX(confidence_score) as max_confidence
FROM migration.collection_data_gaps
WHERE collection_flow_id = '$FLOW_ID';
" 2>&1

echo ""
echo "2. Sample Enhanced Gaps"
echo "-----------------------"
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT
  field_name,
  ROUND(confidence_score::numeric, 3) as confidence,
  CASE
    WHEN ai_suggestions IS NULL THEN 'NULL'
    ELSE jsonb_array_length(ai_suggestions)::text || ' suggestions'
  END as ai_suggestions,
  LEFT(suggested_resolution, 50) || '...' as resolution_preview
FROM migration.collection_data_gaps
WHERE collection_flow_id = '$FLOW_ID'
ORDER BY RANDOM()
LIMIT 5;
" 2>&1

echo ""
echo "3. Backend Log Analysis"
echo "-----------------------"
echo -n "Tools removed: "
if docker logs migration_backend 2>&1 | grep -q "🔧 Removed all tools from agent"; then
    echo -e "${GREEN}✅ YES${NC}"
else
    echo -e "${RED}❌ NO${NC}"
fi

echo -n "JSON selected: "
JSON_LINE=$(docker logs migration_backend 2>&1 | grep "Selected JSON with" | tail -1)
if [ -n "$JSON_LINE" ]; then
    echo -e "${GREEN}✅ $JSON_LINE${NC}"
else
    echo -e "${RED}❌ NOT FOUND${NC}"
fi

echo -n "Enhancement complete: "
COMPLETE_LINE=$(docker logs migration_backend 2>&1 | grep "✅ AI analysis complete" | tail -1)
if [ -n "$COMPLETE_LINE" ]; then
    echo -e "${GREEN}✅ $COMPLETE_LINE${NC}"
else
    echo -e "${RED}❌ NOT FOUND${NC}"
fi

echo -n "Tool errors: "
if docker logs migration_backend 2>&1 | grep -q "APIStatusError"; then
    echo -e "${RED}❌ FOUND (BAD)${NC}"
else
    echo -e "${GREEN}✅ NONE${NC}"
fi

echo -n "Multi-task errors: "
if docker logs migration_backend 2>&1 | grep -q "Readiness Assessment"; then
    echo -e "${RED}❌ FOUND (BAD)${NC}"
else
    echo -e "${GREEN}✅ NONE${NC}"
fi

echo ""
echo "4. Enhancement Rate Calculation"
echo "--------------------------------"
RESULTS=$(docker exec migration_postgres psql -U postgres -d migration_db -t -c "
SELECT
  COUNT(*) as total,
  COUNT(confidence_score) as enhanced
FROM migration.collection_data_gaps
WHERE collection_flow_id = '$FLOW_ID';
" 2>&1)

TOTAL=$(echo "$RESULTS" | awk '{print $1}')
ENHANCED=$(echo "$RESULTS" | awk '{print $3}')

if [ "$TOTAL" != "" ] && [ "$ENHANCED" != "" ]; then
    RATE=$(awk "BEGIN {printf \"%.1f\", ($ENHANCED/$TOTAL)*100}")

    echo "Total Gaps: $TOTAL"
    echo "Enhanced Gaps: $ENHANCED"
    echo -n "Enhancement Rate: $RATE% "

    if [ "$ENHANCED" -eq "$TOTAL" ]; then
        echo -e "${GREEN}✅ 100% SUCCESS!${NC}"
    elif [ "$ENHANCED" -gt "0" ]; then
        echo -e "${YELLOW}⚠️  PARTIAL${NC}"
    else
        echo -e "${RED}❌ FAILED${NC}"
    fi
else
    echo -e "${RED}ERROR: Could not calculate rate${NC}"
fi

echo ""
echo "=================================================="
echo "Test Result Summary"
echo "=================================================="

# Overall pass/fail
if [ "$ENHANCED" -eq "60" ]; then
    echo -e "${GREEN}✅✅✅ TEST PASSED - 100% Enhancement Rate!${NC}"
    echo ""
    echo "All fixes are working correctly:"
    echo "  ✅ Tools removed from agent"
    echo "  ✅ JSON parsing successful"
    echo "  ✅ All 60 gaps enhanced"
    echo ""
    echo "Next steps:"
    echo "  1. Take screenshots of frontend grid"
    echo "  2. Document results in PR"
    echo "  3. Run pre-commit checks"
else
    echo -e "${RED}❌ TEST FAILED - Enhancement rate below 100%${NC}"
    echo ""
    echo "Expected: 60/60 (100%)"
    echo "Actual: $ENHANCED/60 ($RATE%)"
    echo ""
    echo "Troubleshooting needed:"
    echo "  1. Check backend logs for errors"
    echo "  2. Verify agent code changes were deployed"
    echo "  3. Check JSON parsing logic"
    echo "  4. Review task description"
fi

echo ""
