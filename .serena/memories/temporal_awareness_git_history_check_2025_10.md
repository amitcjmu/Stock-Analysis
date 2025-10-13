# Temporal Awareness: Check Git History Before Re-Implementing Fixes

## Problem Pattern
Agent re-implemented fixes that were already committed hours earlier, wasting 45 minutes duplicating work. The confusion arose because:
1. User reported issues with logs and UI behavior
2. Agent read code and found root causes
3. Agent applied "fixes" without checking git history
4. All fixes were already in commit `eb69099b2` from 4 hours prior
5. Issues persisted only because containers hadn't been restarted

## Core Learning: ALWAYS Check Recent Commits First

### Step 1: Check Recent Git History (MANDATORY)
```bash
# Check last 24 hours of commits
git log --oneline --since="1 day ago" -20

# Check specific file history
git log --oneline -10 -- path/to/file.py

# Show what changed in recent commit
git show <commit-hash> --stat
git show <commit-hash> -- path/to/file.py
```

### Step 2: Verify Current Working Tree
```bash
# Check if there are uncommitted changes
git status

# Show diff of what would be changed
git diff path/to/file.py

# If diff is empty, changes are already committed!
```

### Step 3: Container Restart Check
If code looks correct but behavior is wrong:
```bash
# Backend - Check if container has latest code
docker exec migration_backend bash -c "cd /app && git log -1 --format='%h %s'"

# Compare with local
git log -1 --format='%h %s'

# If mismatch, restart container
docker-compose restart migration_backend migration_frontend
```

## Real Example: ADR-012 Fix Already Applied

### User Report
"Asset conflicts not persisting, flow not completing, UI shows stale data"

### Agent's Wrong Approach (45 min wasted)
```bash
# ❌ Immediately read code and started fixing
Read asset_conflicts.py
Edit asset_conflicts.py  # Changed validation logic
Read phase_transition.py
Edit phase_transition.py  # Added pause recognition
# ... more edits
```

### Correct Approach (5 min investigation)
```bash
# ✅ Check git history FIRST
git log --oneline --since="1 day ago" -10

# OUTPUT:
eb69099b2 fix: Asset inventory UI recognizes paused flows with conflict resolution
10e84f696 fix: Improve bulk approve needs review functionality
...

# Check what was in that commit
git show eb69099b2 --stat

# OUTPUT shows ALL the fixes were already applied:
- asset_conflicts.py: validation logic fixed
- phase_transition.py: pause recognition added
- flow_phase_management.py: ADR-012 compliance
- inventory/content/index.tsx: cache invalidation
```

### Why Issues Persisted
Backend and frontend containers were running **old code** from before the commit. Simply needed restart.

## Decision Tree

```
User reports issue
    ↓
Check git log (last 24 hours)
    ↓
Found recent commits touching same area?
    ↓ YES                           ↓ NO
Review commit content         Investigate code
    ↓                              ↓
Does it fix the issue?        Apply fixes
    ↓ YES                          ↓
Restart containers           Commit changes
    ↓
Verify fix works
```

## Common False Positives

### Scenario 1: Recent Commit Exists But Containers Not Restarted
**Symptom**: Code looks correct, behavior is wrong
**Root Cause**: Running stale container image
**Fix**: Restart containers, don't re-edit code

### Scenario 2: Recent Commit Partially Addressed Issue
**Symptom**: Some issues fixed, others remain
**Root Cause**: Incomplete fix or new edge case
**Solution**: Build on existing fix, don't redo it

### Scenario 3: Recent Commit Introduced Regression
**Symptom**: Issue started after recent commit
**Root Cause**: Unintended side effect
**Solution**: Revert or hotfix the regression

## Prevention Commands

### Add to Investigation Workflow
```bash
#!/bin/bash
# Always run before investigating issues

echo "=== Recent Commits (24h) ==="
git log --oneline --since="1 day ago" -10

echo "\n=== Working Tree Status ==="
git status

echo "\n=== Container Code Version ==="
docker exec migration_backend bash -c "cd /app && git log -1 --format='%h %s %ar'"

echo "\n=== Local Code Version ==="
git log -1 --format='%h %s %ar'
```

### Save as `.claude/commands/check-temporal-state.sh`
Invoke with: `/check-temporal-state` before investigating

## Time Savings

- **This Session**: 45 min wasted re-implementing existing fixes
- **With Check**: 5 min to identify + 2 min to restart containers = **7 min total**
- **Savings**: 38 minutes (84% time reduction)

## Related Patterns
- Container restart workflow
- Git history investigation
- Code review before edit
- Commit message archaeology

## Key Insight
**Code archaeology > code changes**. Spend 5 minutes reading git history to avoid 45 minutes of duplicate work.
