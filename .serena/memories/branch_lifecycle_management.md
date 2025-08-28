# Git Branch Lifecycle Management

## Complete Branch Workflow from Creation to Deletion

### After PR Merge - Cleanup Process

#### 1. Switch to Main and Update
```bash
git checkout main
git pull origin main  # Get merged changes
```

#### 2. Delete Local Feature Branch
```bash
git branch -d feature/branch-name  # Safe delete (checks if merged)
git branch -D feature/branch-name  # Force delete if needed
```

#### 3. Delete Remote Branch
```bash
# If not auto-deleted by PR merge
git push origin --delete feature/branch-name

# If remote already deleted (common with GitHub PR merges)
git fetch --prune  # Removes stale remote branch references
```

#### 4. Verify Cleanup
```bash
git branch -a | grep feature/branch-name  # Should return nothing
```

### Common Scenarios

#### Remote Branch Already Deleted
**Error**: `error: unable to delete 'branch': remote ref does not exist`
**Solution**: Branch was auto-deleted on merge, just run `git fetch --prune`

#### Can't Delete Current Branch
**Error**: `error: Cannot delete branch 'X' checked out`
**Solution**: Switch to main first with `git checkout main`

#### Unmerged Changes Warning
**Error**: `error: The branch 'X' is not fully merged`
**Solution**:
- Verify PR was merged: `git log main --grep="branch-name"`
- If truly merged, force delete: `git branch -D branch-name`

### Best Practices
1. Always pull main after PR merge before deleting branches
2. Use `git fetch --prune` regularly to clean stale references
3. Configure auto-delete on merge in GitHub repo settings
4. Keep local repo clean - delete branches after merge
