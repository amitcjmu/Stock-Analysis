#!/bin/bash

# Script to regenerate questionnaire for collection flow
# This will trigger gap analysis which creates a new MCQ-formatted questionnaire

FLOW_ID="b7ba1f33-c463-4962-9c0b-6295effd224b"
API_URL="http://localhost:8081/api/v1/collection/flows/${FLOW_ID}/rerun-gap-analysis"

echo "Regenerating questionnaire for flow: $FLOW_ID"
echo "Triggering gap analysis..."

# Note: Run this from the browser console or use valid auth token
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Cookie: $(cat /tmp/session_cookie 2>/dev/null || echo 'session=none')" \
  -v

echo ""
echo "After running this:"
echo "1. Check the flow at http://localhost:8081/collection/flows/$FLOW_ID"
echo "2. The questionnaire should now have MCQ format"
echo "3. Question 5 should display correctly"
