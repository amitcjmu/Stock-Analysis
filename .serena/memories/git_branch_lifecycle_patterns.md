# Git Branch Lifecycle Management Patterns

## Insight 1: Complete Feature Branch Cleanup
**Problem**: Merged feature branches remain in local and remote tracking
**Solution**: Full cleanup sequence after PR merge
**Code**:
```bash
# 1. Switch to main
git checkout main

# 2. Pull latest changes
git pull origin main

# 3. Delete local feature branch
git branch -d feature/branch-name

# 4. Prune deleted remote branches
git remote prune origin

# 5. Verify cleanup
git branch -a | grep branch-name
```
**Usage**: After PR approval and merge to keep repo clean

## Insight 2: Handling Uncommitted Documentation Changes
**Problem**: Trailing whitespace in docs files creates noise
**Solution**: Identify and discard non-meaningful changes
**Code**:
```bash
# Check what's changed
git status
git diff --stat docs/

# If only whitespace (shown as blank additions):
git diff --minimal docs/planning/

# Discard whitespace-only changes
git restore docs/planning/
```
**Usage**: Before committing, to avoid meaningless doc changes

## Insight 3: Pre-commit Compliance with Detailed Messages
**Problem**: Generic commit messages don't explain fixes
**Solution**: Structured commit with clear problem/solution format
**Code**:
```bash
git commit -m "$(cat <<'EOF'
fix: Address critical code issues from Qodo bot review

- Fix logger.bind() AttributeError by using LoggerAdapter for context
- Fix parameter shadowing of imported 'status' module in governance handlers
- Convert user_id to UUID before passing to conflict resolution
- Fix created_at timestamp to return ISO format instead of empty string
- Update collection forms to use asset-agnostic terminology
- Make current_phase Optional in CollectionFlowResponse schema

These fixes resolve runtime errors and improve code quality based on
static analysis feedback.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```
**Usage**: For clear, traceable commits that pass review
