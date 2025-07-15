#!/bin/bash

# Demo Script for Multi-Agent Issue Resolution System Custom Command

set -e

echo "🚀 Multi-Agent Issue Resolution System - Demo"
echo "============================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOLVE_COMMAND="$SCRIPT_DIR/resolve-issue"

# Check if command exists
if [ ! -f "$RESOLVE_COMMAND" ]; then
    echo "❌ Error: resolve-issue command not found"
    exit 1
fi

echo ""
echo "📋 Demo Scenarios:"
echo "1. Manual issue description"
echo "2. Error logs simulation"
echo "3. Check issue status"
echo ""

# Demo 1: Manual issue description
echo "🔍 Demo 1: Manual Issue Description"
echo "-----------------------------------"
echo "Creating issue from manual description..."

ISSUE_ID=$($RESOLVE_COMMAND --description "The login button on the authentication page is not responding to clicks. Users are unable to log in to the application. This started happening after the recent UI update." --launch | grep "Created issue:" | cut -d' ' -f3)

if [ -n "$ISSUE_ID" ]; then
    echo "✅ Created issue: $ISSUE_ID"
else
    echo "❌ Failed to create issue"
    exit 1
fi

echo ""
echo "📊 Checking issue status..."
$RESOLVE_COMMAND --status "$ISSUE_ID"

echo ""
echo "📁 Session files created:"
SESSION_DIR=$(find /Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e -type d -name "session_*" | head -1)
if [ -n "$SESSION_DIR" ]; then
    echo "Session directory: $SESSION_DIR"
    ls -la "$SESSION_DIR"
    echo ""
    echo "Agent instructions:"
    ls -la "$SESSION_DIR/agent_instructions/"
fi

echo ""
echo "-----------------------------------"
echo ""

# Demo 2: Error logs simulation
echo "🔍 Demo 2: Error Logs Simulation"
echo "--------------------------------"
echo "Creating issue from error logs..."

ERROR_LOGS="ERROR: Database connection timeout after 30 seconds
Stack trace:
  File '/app/services/database.py', line 45, in connect
  sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
  Connection timeout occurred while trying to connect to PostgreSQL database
  
Context: User authentication flow
Time: 2025-01-15 16:30:00
Environment: Production"

ISSUE_ID_2=$($RESOLVE_COMMAND --logs "$ERROR_LOGS" --launch | grep "Created issue:" | cut -d' ' -f3)

if [ -n "$ISSUE_ID_2" ]; then
    echo "✅ Created issue: $ISSUE_ID_2"
else
    echo "❌ Failed to create issue"
    exit 1
fi

echo ""
echo "📊 Checking issue status..."
$RESOLVE_COMMAND --status "$ISSUE_ID_2"

echo ""
echo "-----------------------------------"
echo ""

# Demo 3: Help documentation
echo "🔍 Demo 3: Help Documentation"
echo "-----------------------------"
$RESOLVE_COMMAND --help

echo ""
echo "-----------------------------------"
echo ""

# Summary
echo "📋 Demo Summary"
echo "==============="
echo "✅ Created UI issue: $ISSUE_ID"
echo "✅ Created Backend issue: $ISSUE_ID_2"
echo "✅ Generated agent instructions for both issues"
echo "✅ Workflow enforcement system engaged"
echo ""
echo "🔄 Next Steps:"
echo "1. Review agent instructions in session directories"
echo "2. Agents follow the workflow enforcement system"
echo "3. Original reporters validate resolutions"
echo "4. Issues marked complete after validation"
echo ""
echo "💡 Usage Tips:"
echo "• Use --screenshot for UI issues with visual problems"
echo "• Use --logs for backend/database errors"
echo "• Use --description for manual issue reporting"
echo "• Use --status to check progress anytime"
echo ""
echo "🚀 Demo completed successfully!"

# Show final session structure
echo ""
echo "📁 Final Session Structure:"
LATEST_SESSION=$(find /Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e -type d -name "session_*" | sort | tail -1)
if [ -n "$LATEST_SESSION" ]; then
    echo "Latest session: $LATEST_SESSION"
    tree "$LATEST_SESSION" 2>/dev/null || ls -la "$LATEST_SESSION"
fi