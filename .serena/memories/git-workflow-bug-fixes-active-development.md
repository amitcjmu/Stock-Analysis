# Git Workflow: Bug Fixes on Active Codebases

## Problem Pattern
When fixing bugs while other PRs are being merged to main, creating a fix branch from the wrong base can:
- Include unrelated commits from other developers
- Overwrite recently merged functionality
- Create contaminated PRs requiring complete rework

## Critical Mistake Example (Session 2025-11-11)
```bash
# WRONG - Created from feature branch instead of main
git checkout fix/context-refresh
git checkout -b fix/bug-batch-20251111-142727

# Result: PR contained 6 commits from ramayyalaraju + overwrote PR #1001 changes
```

## Correct Workflow

### 1. Always Start From Main
```bash
# Verify current branch
git branch --show-current

# Switch to main FIRST
git checkout main
git pull origin main

# Create bug fix branch from main
git checkout -b fix/bugs-ISSUE-NUMBERS-correct
```

### 2. When You Discover Wrong Base
```bash
# Stash uncommitted work
git stash push -m "WIP: Bug fixes before branch cleanup"

# Switch to main
git checkout main
git pull origin main

# Create clean branch
git checkout -b fix/bugs-clean-TIMESTAMP

# Cherry-pick ONLY your commits (verify with git log first)
git cherry-pick COMMIT_HASH

# If merge conflicts: prioritize MAIN's code over your old fixes
# Re-implement fixes on top of current main code
```

### 3. Verify Before Pushing
```bash
# Check commit history (should only show YOUR commits)
git log --oneline --not origin/main

# Check file changes (verify no unexpected files)
git diff origin/main --stat

# Verify remote tracking
git branch -vv
```

## Key Principles

### Priority Order
1. **Current main functionality** (recently merged PRs)
2. **Your bug fixes** (implemented on top of #1)
3. NEVER prioritize old fix code over new features

### Pre-Implementation Checks
- [ ] Read current main code FIRST
- [ ] Check recent merged PRs (e.g., `gh pr list --state merged --limit 5`)
- [ ] Identify signature changes (async/sync, parameters)
- [ ] Re-implement fixes on current code, don't cherry-pick blindly

### Red Flags
- PR shows more commits than expected
- PR additions/deletions much larger than your changes
- Other developer names in commit history
- Files you didn't modify appear in diff

## Recovery Pattern

If contaminated PR already created:
```bash
# 1. Close incorrect PR
gh pr close WRONG_PR_NUMBER --comment "Closing - wrong base branch"

# 2. Delete contaminated branches
git branch -D wrong-branch-name
git push origin --delete wrong-branch-name

# 3. Start over from main with correct workflow above
```

## Application to Bug Fixes

When fixing bugs like #996, #1000, #1011:
- Main had PR #1001 with new async patterns
- Initial fix removed `await` (assumed sync from old code)
- Correct approach: Check current deduplication.py, see it's async, preserve `await`

**Code Example**:
```python
# Check current main FIRST:
async def should_reuse_questionnaire(...) -> tuple[bool, str]:
    # Function is async in current main (PR #1001)

# Your fix MUST preserve this:
should_reuse, reason = await should_reuse_questionnaire(existing)  # ✅
# NOT: should_reuse, reason = should_reuse_questionnaire(existing)  # ❌
```

## Automation Recommendation

Add to `~/.gitconfig`:
```gitconfig
[alias]
    # Verify branch before creating new one
    safe-branch = "!f() { git checkout main && git pull origin main && git checkout -b \"$1\"; }; f"
    
    # Check if current branch diverged from main
    check-base = "!git log --oneline --graph --decorate --all | head -20"
```

Usage: `git safe-branch fix/bug-123` instead of `git checkout -b`
