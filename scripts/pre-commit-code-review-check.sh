#!/bin/bash
#
# pre-commit-code-review-check.sh
#
# Reviews changed code against common patterns in the code review repository.
# This helps catch issues before they reach PR review, making check-ins more efficient.
#
# Usage:
#   ./scripts/pre-commit-code-review-check.sh          # Check all changed files
#   ./scripts/pre-commit-code-review-check.sh --staged # Only check staged files
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

echo -e "${BLUE}📋 Running code review repository checks...${NC}"
echo ""

# Check if review repository exists
if [ ! -f "$REVIEW_REPO" ]; then
    echo -e "${RED}❌ Code review repository not found: $REVIEW_REPO${NC}"
    exit 1
fi

# Determine which files to check
if [ "$1" = "--staged" ]; then
    FILES_CMD="git diff --cached --name-only --diff-filter=ACMR"
    CHECK_TYPE="staged"
else
    FILES_CMD="git diff --name-only --diff-filter=ACMR"
    CHECK_TYPE="modified"
fi

echo -e "${CYAN}Checking $CHECK_TYPE files against code review patterns...${NC}"
echo ""

ISSUES_FOUND=0
FILES_CHECKED=0

# Check each file (using process substitution to handle filenames with spaces)
# Process substitution allows variable persistence outside the loop
while IFS= read -r FILE; do
    if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
        continue
    fi

    FILES_CHECKED=$((FILES_CHECKED + 1))
    FILE_ISSUES=0

    echo -e "${CYAN}🔍 Checking: $FILE${NC}"

    # Read the file content
    FILE_CONTENT=$(cat "$FILE")

    # Pattern 1: Check for local imports inside functions (Python)
    if [[ "$FILE" == *.py ]]; then
        # Check for imports after line 50 (should be at top)
        LOCAL_IMPORTS=$(grep -n "^[[:space:]]*from\|^[[:space:]]*import" "$FILE" | awk -F: '$1 > 50 {print $1}' | head -5)
        if [ -n "$LOCAL_IMPORTS" ]; then
            echo -e "  ${YELLOW}⚠️  Potential local imports detected after line 50:${NC}"
            echo "$LOCAL_IMPORTS" | while read line; do
                echo -e "    ${YELLOW}  Line $line${NC}"
            done
            FILE_ISSUES=$((FILE_ISSUES + 1))
        fi
    fi

    # Pattern 2: Check for str(exc) exposed to users (Python)
    if [[ "$FILE" == *.py ]]; then
        STR_EXC_COUNT=$(grep -n 'str(exc)' "$FILE" | grep -v '#.*sanitize\|#.*TODO\|#.*FIXME' | wc -l | tr -d ' ')
        if [ "$STR_EXC_COUNT" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠️  Found str(exc) that may expose internal errors:${NC}"
            grep -n 'str(exc)' "$FILE" | grep -v '#.*sanitize\|#.*TODO\|#.*FIXME' | while read line; do
                echo -e "    ${YELLOW}  $line${NC}"
            done
            echo -e "  ${CYAN}    → Consider sanitizing error messages before exposing to users${NC}"
            FILE_ISSUES=$((FILE_ISSUES + 1))
        fi
    fi

    # Pattern 3: Check for SimpleNamespace usage (Python)
    if [[ "$FILE" == *.py ]]; then
        SIMPLENAMESPACE=$(grep -n "SimpleNamespace\|from types import SimpleNamespace" "$FILE" | wc -l | tr -d ' ')
        if [ "$SIMPLENAMESPACE" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠️  Found SimpleNamespace usage (consider using dataclasses):${NC}"
            grep -n "SimpleNamespace\|from types import SimpleNamespace" "$FILE" | while read line; do
                echo -e "    ${YELLOW}  $line${NC}"
            done
            echo -e "  ${CYAN}    → Prefer @dataclass for type safety and IDE support${NC}"
            FILE_ISSUES=$((FILE_ISSUES + 1))
        fi
    fi

    # Pattern 4: Check for missing error handling (Python try-except)
    if [[ "$FILE" == *.py ]]; then
        # Look for database/external service calls without try-except
        DB_CALLS=$(grep -n "await.*query\|await.*execute\|await.*fetch\|db\." "$FILE" | grep -v "try:\|except:" | head -5)
        if [ -n "$DB_CALLS" ]; then
            # Check if these are inside try blocks (rough check)
            echo -e "  ${BLUE}ℹ️  Review database calls for error handling:${NC}"
            echo "$DB_CALLS" | while read line; do
                echo -e "    ${BLUE}  $line${NC}"
            done
            echo -e "  ${CYAN}    → Ensure external calls are wrapped in try-except${NC}"
        fi
    fi

    # Pattern 5: Check for magic numbers
    MAGIC_NUMBERS=$(grep -nE '\b[0-9]{2,}\b' "$FILE" | grep -vE '0x[0-9a-fA-F]+|#[0-9a-fA-F]{6}|:[0-9]{4}|version|line|PR #|issue #|# [0-9]+' | head -3)
    if [ -n "$MAGIC_NUMBERS" ]; then
        echo -e "  ${BLUE}ℹ️  Potential magic numbers found (consider named constants):${NC}"
        echo "$MAGIC_NUMBERS" | while read line; do
            echo -e "    ${BLUE}  $line${NC}"
        done
    fi

    # Pattern 6: Check for audit logging (critical operations)
    if [[ "$FILE" == *.py ]]; then
        CRITICAL_OPS=$(grep -nE "upload|import|export|delete|create.*flow|store.*data" "$FILE" | grep -iE "def |async def " | grep -v "test_\|_test" | head -5)
        if [ -n "$CRITICAL_OPS" ]; then
            HAS_AUDIT=$(grep -i "audit\|log_user_action\|log_security_event" "$FILE" | wc -l | tr -d ' ')
            if [ "$HAS_AUDIT" -eq 0 ]; then
                echo -e "  ${YELLOW}⚠️  Critical operations found without audit logging:${NC}"
                echo "$CRITICAL_OPS" | while read line; do
                    echo -e "    ${YELLOW}  $line${NC}"
                done
                echo -e "  ${CYAN}    → Add audit logging for security compliance${NC}"
                FILE_ISSUES=$((FILE_ISSUES + 1))
            fi
        fi
    fi

    # Pattern 7: Check for logging sensitive data (Python)
    if [[ "$FILE" == *.py ]]; then
        SENSITIVE_LOG=$(grep -nE 'logger\.(info|error|debug).*raw_|logger\.(info|error|debug).*user_|logger\.(info|error|debug).*file_contents' "$FILE" | grep -v "#.*safe\|#.*sanitized" | head -3)
        if [ -n "$SENSITIVE_LOG" ]; then
            echo -e "  ${YELLOW}⚠️  Potential logging of sensitive data:${NC}"
            echo "$SENSITIVE_LOG" | while read line; do
                echo -e "    ${YELLOW}  $line${NC}"
            done
            echo -e "  ${CYAN}    → Log metadata only, not raw user data or file contents${NC}"
            FILE_ISSUES=$((FILE_ISSUES + 1))
        fi
    fi

    if [ "$FILE_ISSUES" -gt 0 ]; then
        ISSUES_FOUND=$((ISSUES_FOUND + FILE_ISSUES))
        echo -e "  ${RED}❌ Found $FILE_ISSUES issue(s)${NC}"
    else
        echo -e "  ${GREEN}✅ No obvious issues detected${NC}"
    fi
    echo ""
done < <($FILES_CMD | grep -E '\.(py|ts|tsx|js|jsx)$')

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo -e "  Files checked: $FILES_CHECKED"
echo -e "  Issues found: $ISSUES_FOUND"
echo ""

if [ "$ISSUES_FOUND" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Please review the issues above${NC}"
    echo -e "${CYAN}Reference: $REVIEW_REPO${NC}"
    echo -e "${CYAN}Review checklist: docs/code-reviews/review-comments-repository.md#review-checklist-template${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  These are pattern-based checks. Review manually before committing.${NC}"
    exit 0  # Don't fail - just warn
else
    echo -e "${GREEN}✅ Code review checks passed!${NC}"
    echo -e "${CYAN}Still review manually against: $REVIEW_REPO${NC}"
    exit 0
fi
