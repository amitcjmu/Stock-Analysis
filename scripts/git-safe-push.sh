#!/bin/bash
#
# git-safe-push.sh
#
# Wrapper around git push that ensures branch is synced with main first.
# This prevents pushing code that's behind main, reducing merge conflicts in PRs.
#
# Usage:
#   ./scripts/git-safe-push.sh                    # Push current branch
#   ./scripts/git-safe-push.sh origin feature-branch  # Push specific branch
#   ./scripts/git-safe-push.sh --force             # Force push (after syncing)
#
# You can alias this in your shell:
#   alias gpush='./scripts/git-safe-push.sh'
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-with-main.sh"

# If sync script exists, run it first
if [ -f "$SYNC_SCRIPT" ]; then
    echo "🔄 Ensuring branch is synced with main before pushing..."
    if ! "$SYNC_SCRIPT" --check 2>&1; then
        echo "⏳ Syncing with main..."
        if ! "$SYNC_SCRIPT" 2>&1; then
            echo "❌ Sync failed. Fix conflicts before pushing."
            exit 1
        fi
    fi
fi

# Pass all arguments to git push
git push "$@"
