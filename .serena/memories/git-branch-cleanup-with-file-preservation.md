# Git Branch Cleanup with File Preservation

## Problem
Need to delete merged branch but preserve unstaged/untracked work (docs, test scripts, analysis files) that hasn't made it to main.

## Solution
Use `git stash push -u` before branch deletion, then restore with `git stash pop`.

## Implementation Pattern

```bash
# 1. Stash all unstaged and untracked files with descriptive message
git stash push -u -m "Preserve unstaged files before deleting branch-name - includes docs, test scripts, analysis"

# 2. Verify stash created
git stash list
# Output: stash@{0}: On branch-name: Preserve unstaged files...

# 3. Switch to main and pull latest
git checkout main
git pull origin main

# 4. Delete local branch
git branch -D branch-name

# 5. Delete remote branch (if exists)
git push origin --delete branch-name
# Note: GitHub auto-deletes after PR merge, so this may error (safe to ignore)

# 6. Restore all stashed files
git stash pop
# Output: Files restored to working directory

# 7. Verify files restored
git status
ls -la docs/analysis/  # Check specific directories
```

## Flags Explained
- `git stash push -u`: Stash **untracked** files too (not just modified)
- `-m "message"`: Descriptive message for easy identification
- `git stash pop`: Apply stash and remove from stash list

## When to Apply
- Deleting feature branches after PR merge
- Switching contexts while preserving WIP
- Cleaning up after branch squash/rebase

## Common Files to Preserve
- Documentation updates: `docs/analysis/**`, `*.md`
- Test scripts: `backend/test_*.py`, `*.sql`
- Configuration: `config/tools/**`, `.ignore` files
- Formatting changes from Black/Prettier

## Verification Checklist
```bash
# Before stash
git status  # Note all unstaged/untracked files

# After stash pop
git status  # Verify same files restored
ls -la docs/analysis/  # Check critical directories exist
```

## Benefits
- Preserves all uncommitted work across branch operations
- Avoids accidental file loss during cleanup
- Maintains workflow continuity
- Enables clean branch deletion without losing context

## Real-World Example
Preserved 8 files during branch cleanup:
- 5 modified test scripts
- 3 untracked directories (docs/analysis/backend_cleanup/, backend/scripts/analysis/)
All files successfully restored after branch deletion.

## Related Commands
```bash
# List all stashes
git stash list

# Apply specific stash without removing
git stash apply stash@{0}

# Drop specific stash
git stash drop stash@{0}

# Clear all stashes
git stash clear
```
