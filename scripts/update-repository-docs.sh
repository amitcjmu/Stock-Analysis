#!/bin/bash
#
# update-repository-docs.sh
#
# Updates code review and testing repository documents with new patterns from PR comments.
# This ensures the repositories stay current with review feedback and testing patterns.
#
# Usage:
#   ./scripts/update-repository-docs.sh                    # Check for updates needed
#   ./scripts/update-repository-docs.sh --pr <pr_number>   # Update from specific PR
#   ./scripts/update-repository-docs.sh --review           # Prompt for review comment entry
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

CODE_REVIEW_REPO="docs/code-reviews/review-comments-repository.md"
TESTING_REPO_DIR="docs/testing"
TESTING_STRATEGY="$TESTING_REPO_DIR/testing-strategy.md"
QA_GUIDE="$TESTING_REPO_DIR/QA_GUIDE.md"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📚 Repository Documents Update${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if files exist
if [ ! -f "$CODE_REVIEW_REPO" ]; then
    echo -e "${RED}❌ Code review repository not found: $CODE_REVIEW_REPO${NC}"
    exit 1
fi

if [ ! -d "$TESTING_REPO_DIR" ]; then
    echo -e "${RED}❌ Testing repository directory not found: $TESTING_REPO_DIR${NC}"
    exit 1
fi

echo -e "${CYAN}📋 Repository Documents:${NC}"
echo -e "  ✅ Code Review: $CODE_REVIEW_REPO"
echo -e "  ✅ Testing Strategy: $TESTING_STRATEGY"
echo -e "  ✅ QA Guide: $QA_GUIDE"
echo ""

# If PR number provided, fetch PR comments
if [ "$1" = "--pr" ] && [ -n "$2" ]; then
    PR_NUMBER="$2"
    echo -e "${CYAN}📥 Fetching PR #$PR_NUMBER comments...${NC}"

    if command -v gh >/dev/null 2>&1; then
        PR_BODY=$(gh pr view "$PR_NUMBER" --json body,comments --jq '{body: .body, comments: [.comments[] | {author: .author.login, body: .body}]}')
        echo -e "${GREEN}✅ PR comments fetched${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Review PR comments and update repository documents manually:${NC}"
        echo -e "  - Check for new code review patterns in comments"
        echo -e "  - Check for new testing patterns or issues"
        echo -e "  - Update $CODE_REVIEW_REPO if pattern is generalizable"
        echo -e "  - Update $TESTING_STRATEGY or $QA_GUIDE if testing-related"
        echo ""
        echo -e "${CYAN}See PR comments:${NC}"
        echo "$PR_BODY" | jq -r '.comments[] | "  - @\(.author): \(.body)"' 2>/dev/null || echo "  (Unable to parse PR comments)"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI (gh) not installed. Install with: brew install gh${NC}"
        echo -e "${CYAN}Manually review PR #$PR_NUMBER and update repository documents.${NC}"
    fi
    exit 0
fi

# If --review flag, prompt for manual entry
if [ "$1" = "--review" ]; then
    echo -e "${CYAN}📝 Manual Review Comment Entry${NC}"
    echo ""
    echo -e "${YELLOW}This will help you document a new review pattern.${NC}"
    echo ""
    read -p "Enter review comment summary: " COMMENT_SUMMARY
    read -p "Is this a code review pattern (c) or testing pattern (t)? [c/t]: " PATTERN_TYPE

    if [ "$PATTERN_TYPE" = "c" ]; then
        echo ""
        echo -e "${CYAN}Add this pattern to $CODE_REVIEW_REPO:${NC}"
        echo ""
        echo "## [Category]"
        echo ""
        echo "### ❌ [Pattern Name]"
        echo "**Issue:** $COMMENT_SUMMARY"
        echo "**Why:** [Reason this matters]"
        echo "**Example:** [Code example]"
        echo "**Check:** [How to verify]"
        echo ""
        echo "**Reference:** PR #XXX"
    elif [ "$PATTERN_TYPE" = "t" ]; then
        echo ""
        echo -e "${CYAN}Add this pattern to $TESTING_STRATEGY or $QA_GUIDE:${NC}"
        echo ""
        echo "## [Testing Pattern Category]"
        echo ""
        echo "### Pattern Description"
        echo "$COMMENT_SUMMARY"
        echo ""
        echo "### Implementation"
        echo "[How to test this pattern]"
        echo ""
        echo "**Reference:** PR #XXX"
    fi
    exit 0
fi

# Default: Check for updates needed
echo -e "${CYAN}🔍 Checking repository documents for updates...${NC}"
echo ""

LAST_UPDATED=$(grep -i "Last Updated" "$CODE_REVIEW_REPO" | head -1 || echo "")
echo -e "${BLUE}Code Review Repository:${NC}"
echo -e "  $LAST_UPDATED"
echo ""

echo -e "${BLUE}Testing Repository:${NC}"
if [ -f "$TESTING_STRATEGY" ]; then
    STRATEGY_UPDATED=$(grep -i "Last Updated\|Updated:" "$TESTING_STRATEGY" | head -1 || echo "  No update date found")
    echo -e "  Strategy: $STRATEGY_UPDATED"
fi
echo ""

echo -e "${YELLOW}⚠️  Repository Update Reminder:${NC}"
echo ""
echo -e "${CYAN}After addressing PR review comments:${NC}"
echo -e "  1. Identify if comment represents a generalizable pattern"
echo -e "  2. If yes, add to $CODE_REVIEW_REPO"
echo -e "  3. If testing-related, update $TESTING_STRATEGY or $QA_GUIDE"
echo -e "  4. Include: Issue, Why, Example, Check, Reference PR #"
echo ""
echo -e "${CYAN}How to update:${NC}"
echo -e "  - Review PR comments: ./scripts/update-repository-docs.sh --pr <number>"
echo -e "  - Manual entry: ./scripts/update-repository-docs.sh --review"
echo -e "  - Edit directly: Open $CODE_REVIEW_REPO in editor"
echo ""
echo -e "${GREEN}✅ Repository documents are ready for updates${NC}"
