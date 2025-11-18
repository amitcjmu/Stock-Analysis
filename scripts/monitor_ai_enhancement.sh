#!/bin/bash

# AI Enhancement Test Monitoring Script
# Monitors backend logs for critical AI enhancement events

echo "=================================================="
echo "AI Enhancement Test Monitoring"
echo "Flow ID: f54241f6-4ed5-40fa-b85f-216ceda28f38"
echo "=================================================="
echo ""
echo "Monitoring backend logs for AI enhancement activity..."
echo "Press Ctrl+C to stop"
echo ""
echo "Watching for:"
echo "  ✅ Tools removal confirmation"
echo "  ✅ JSON candidate selection"
echo "  ✅ Enhancement completion"
echo "  ❌ Tool usage errors"
echo "  ❌ Multi-task creation"
echo ""
echo "--------------------------------------------------"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Follow backend logs and highlight key events
docker logs migration_backend -f --tail 0 2>&1 | while IFS= read -r line; do
    case "$line" in
        *"🔧 Removed all tools from agent"*)
            echo -e "${GREEN}✅ CRITICAL: ${line}${NC}"
            ;;
        *"Selected JSON with"*"gaps from"*)
            echo -e "${GREEN}✅ JSON SELECTION: ${line}${NC}"
            ;;
        *"✅ AI analysis complete"*)
            echo -e "${GREEN}✅ COMPLETION: ${line}${NC}"
            echo ""
            echo "=================================================="
            echo "ENHANCEMENT COMPLETE - Check results above"
            echo "=================================================="
            ;;
        *"APIStatusError"*)
            echo -e "${RED}❌ TOOL ERROR: ${line}${NC}"
            ;;
        *"Readiness Assessment"*)
            echo -e "${RED}❌ MULTI-TASK: ${line}${NC}"
            ;;
        *"No valid gaps data in AI output"*)
            echo -e "${RED}❌ PARSING FAILED: ${line}${NC}"
            ;;
        *"gap analysis"*|*"AI enhancement"*|*"agentic"*)
            echo -e "${BLUE}INFO: ${line}${NC}"
            ;;
        *"ERROR"*|*"error"*)
            echo -e "${YELLOW}WARN: ${line}${NC}"
            ;;
    esac
done
