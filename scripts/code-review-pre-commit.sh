#!/bin/bash
#
# code-review-pre-commit.sh
#
# Pre-commit hook for code review checks
# Runs code review pattern checks on staged files before commit
#
# This integrates with:
# - Code review repository (docs/code-reviews/review-comments-repository.md)
# - Optional: AI code review tools (Qodo Merge, CodeRabbit, etc.)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

REVIEW_REPO="docs/code-reviews/review-comments-repository.md"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${BLUE}🔍 Running code review checks on staged files...${NC}"
echo ""

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(py|ts|tsx|js|jsx)$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}✅ No code files staged for review${NC}"
    exit 0
fi

echo -e "${CYAN}Found $(echo "$STAGED_FILES" | wc -l | tr -d ' ') staged file(s) to review${NC}"
echo ""

ISSUES_FOUND=0
FILES_CHECKED=0

# Check if review repository exists
if [ ! -f "$REVIEW_REPO" ]; then
    echo -e "${YELLOW}⚠️  Code review repository not found: $REVIEW_REPO${NC}"
    echo -e "${YELLOW}   Skipping pattern-based review checks${NC}"
    echo ""
else
    # Run pattern-based code review checks
    echo -e "${CYAN}📋 Checking against code review patterns...${NC}"

    while IFS= read -r file; do
        if [ -z "$file" ]; then
            continue
        fi

        # Skip if file doesn't exist (might be deleted)
        if [ ! -f "$file" ]; then
            continue
        fi

        FILES_CHECKED=$((FILES_CHECKED + 1))

        # Check file against review patterns
        # Look for common issues from review repository
        PATTERN_ISSUES=0

        # Check for hardcoded values that should use agents
        if grep -qE "(if.*==|if.*!=|if.*>|if.*<)" "$file" 2>/dev/null; then
            # Check if it's a simple heuristic (not a complex condition)
            if grep -qE "(if.*len\(|if.*count\(|if.*>.*5|if.*<.*3)" "$file" 2>/dev/null; then
                echo -e "${YELLOW}⚠️  $file: Potential hardcoded heuristic detected${NC}"
                echo -e "   Consider using CrewAI agents instead of hardcoded rules"
                PATTERN_ISSUES=$((PATTERN_ISSUES + 1))
            fi
        fi

        # Check for missing multi-tenant filters in database queries
        if grep -qE "(select|SELECT).*from|FROM" "$file" 2>/dev/null; then
            if ! grep -qE "(client_account_id|engagement_id)" "$file" 2>/dev/null; then
                echo -e "${YELLOW}⚠️  $file: Database query may be missing multi-tenant filters${NC}"
                echo -e "   Ensure queries include client_account_id and engagement_id"
                PATTERN_ISSUES=$((PATTERN_ISSUES + 1))
            fi
        fi

        # Check for direct LLM calls (should use multi_model_service)
        if grep -qE "(openai\.|anthropic\.|google\.generativeai\.)" "$file" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  $file: Direct LLM API call detected${NC}"
            echo -e "   Consider using multi_model_service for cost tracking"
            PATTERN_ISSUES=$((PATTERN_ISSUES + 1))
        fi

        if [ $PATTERN_ISSUES -gt 0 ]; then
            ISSUES_FOUND=$((ISSUES_FOUND + PATTERN_ISSUES))
        fi

    done <<< "$STAGED_FILES"
fi

# AI Code Review Integration
# Qodo Merge / PR-Agent integration
# Note: PR-Agent is designed for PR reviews, not pre-commit hooks
# Full AI review happens automatically when you create a PR
# This section provides information about AI review availability

if [ "${QODO_ENABLED:-false}" = "true" ] || [ -n "${QODO_API_KEY:-}" ] || command -v pr-agent &> /dev/null; then
    echo ""
    echo -e "${CYAN}🤖 AI Code Review Status${NC}"

    # Check if PR-Agent is installed
    if command -v pr-agent &> /dev/null; then
        echo -e "${GREEN}   ✅ PR-Agent is installed${NC}"
        echo -e "${CYAN}   📝 Note: PR-Agent reviews pull requests, not pre-commit changes${NC}"
        echo -e "${CYAN}   💡 Full AI review will run automatically when you create a PR${NC}"
        echo -e "${CYAN}   🔗 Install GitHub App: https://github.com/apps/qodo-merge${NC}"

    # Check for API key
    elif [ -n "${QODO_API_KEY:-}" ]; then
        echo -e "${GREEN}   ✅ Qodo Merge API key configured${NC}"
        echo -e "${CYAN}   📝 Full AI review available in pull requests${NC}"
        echo -e "${CYAN}   🔗 Install GitHub App: https://github.com/apps/qodo-merge${NC}"

    # GitHub environment
    elif [ -n "${GITHUB_TOKEN:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
        echo -e "${GREEN}   ✅ GitHub environment detected${NC}"
        echo -e "${CYAN}   📝 PR-Agent will review your pull requests automatically${NC}"
        echo -e "${CYAN}   🔗 Install PR-Agent GitHub App: https://github.com/apps/qodo-merge${NC}"
    fi

    echo -e "${BLUE}   ℹ️  Pattern-based review (above) runs in pre-commit${NC}"
    echo -e "${BLUE}   ℹ️  Full AI review runs automatically in pull requests${NC}"
fi

# Summary
echo ""
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ Code review passed${NC}"
    echo -e "${GREEN}   Checked $FILES_CHECKED file(s)${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Code review found $ISSUES_FOUND potential issue(s)${NC}"
    echo -e "${YELLOW}   Please review the suggestions above${NC}"
    echo -e "${YELLOW}   These are warnings and won't block the commit${NC}"
    echo ""
    echo -e "${CYAN}💡 Tip: Review patterns in $REVIEW_REPO${NC}"
    # Exit with 0 to allow commit (warnings only)
    # Change to exit 1 if you want to block commits with issues
    exit 0
fi
