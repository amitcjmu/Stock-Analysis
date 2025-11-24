#!/bin/bash
#
# sync-with-main.sh
#
# Ensures current branch is synced with latest main branch before operations.
# This prevents merge conflicts and ensures code is always based on latest changes.
#
# Usage:
#   ./scripts/sync-with-main.sh          # Just sync, don't push
#   ./scripts/sync-with-main.sh --push   # Sync and push
#   ./scripts/sync-with-main.sh --check  # Only check, don't sync
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Check if we're on main branch
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo -e "${YELLOW}⚠️  You're on main branch. Switch to a feature branch first.${NC}"
    exit 1
fi

echo -e "${BLUE}🔄 Syncing branch '${CURRENT_BRANCH}' with origin/main...${NC}"

# Fetch latest from main
echo -e "${BLUE}📥 Fetching latest changes from origin/main...${NC}"
git fetch origin main 2>&1 || {
    echo -e "${RED}❌ Failed to fetch from origin/main${NC}"
    exit 1
}

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes. Stashing them...${NC}"
    git stash push -m "Auto-stash before syncing with main $(date +%Y-%m-%d_%H:%M:%S)"
    STASHED=true
else
    STASHED=false
fi

# Count commits behind/ahead
BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")

echo -e "${BLUE}📊 Branch status:${NC}"
echo -e "   Commits behind main: ${BEHIND}"
echo -e "   Commits ahead of main: ${AHEAD}"

# Check if we're behind
if [ "$BEHIND" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Your branch is ${BEHIND} commit(s) behind origin/main${NC}"

    # If --check flag, just warn and exit
    if [ "$1" = "--check" ]; then
        echo -e "${YELLOW}Run './scripts/sync-with-main.sh' to sync with main${NC}"
        if [ "$STASHED" = true ]; then
            git stash pop 2>&1 || true
        fi
        exit 1
    fi

    echo -e "${BLUE}🔄 Rebasing onto origin/main...${NC}"

    # Rebase onto main
    if git pull origin main --rebase 2>&1; then
        echo -e "${GREEN}✅ Successfully rebased onto origin/main${NC}"
    else
        echo -e "${RED}❌ Rebase failed. You have conflicts to resolve.${NC}"
        echo -e "${YELLOW}Resolve conflicts, then run: git rebase --continue${NC}"
        if [ "$STASHED" = true ]; then
            echo -e "${YELLOW}Uncommitted changes are stashed (run 'git stash list' to see)${NC}"
        fi
        exit 1
    fi
else
    echo -e "${GREEN}✅ Branch is up to date with origin/main${NC}"
fi

# Restore stashed changes if any
if [ "$STASHED" = true ]; then
    echo -e "${BLUE}📦 Restoring stashed changes...${NC}"
    git stash pop 2>&1 || {
        echo -e "${YELLOW}⚠️  Stash pop had conflicts. Resolve them manually.${NC}"
    }
fi

# Final status check
BEHIND_FINAL=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
if [ "$BEHIND_FINAL" -eq 0 ]; then
    echo -e "${GREEN}✅ Branch is now fully synced with origin/main${NC}"

    # If --push flag, push after syncing
    if [ "$1" = "--push" ]; then
        echo -e "${BLUE}🚀 Pushing to remote...${NC}"
        git push origin "$CURRENT_BRANCH" 2>&1 || {
            echo -e "${RED}❌ Push failed${NC}"
            exit 1
        }
        echo -e "${GREEN}✅ Successfully pushed to origin/${CURRENT_BRANCH}${NC}"
    fi

    exit 0
else
    echo -e "${RED}❌ Sync incomplete. Still ${BEHIND_FINAL} commit(s) behind.${NC}"
    exit 1
fi
