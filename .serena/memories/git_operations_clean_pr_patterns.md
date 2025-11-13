# Git Operations for Clean PR Creation

## Problem
Temporary analysis files (.claude/commands/*.md, TEST_REPORT_*.md, ISSUE_*_SUMMARY.md) were committed to PR. Need to remove without showing deletions in PR diff.

## Root Cause Understanding

**Why `git rm --cached` Fails**:
```bash
# If file exists in parent commit:
git rm --cached unwanted_file.md
git commit --amend

# Problem: Shows as deletion in PR diff
# Because: File existed in parent, now we're deleting it
# PR diff: Shows red "deleted file" line
```

**Why Files Shouldn't Be There**:
- `.gitignore` contains `.claude/commands/`
- But file was already tracked before gitignore rule added
- Or file was force-added with `git add -f`

## Correct Solution: Soft Reset Method

```bash
# Step 1: Find parent commit (before your changes)
git log --oneline -5
# Example output:
# f2b5aa6f6 (HEAD -> fix/bug-batch) Your latest commit
# 761bd391f Your previous commit
# bf89a488a (origin/main) Merge pull request #966

# Step 2: Soft reset to parent (keeps changes in working tree)
git reset --soft bf89a488a

# Step 3: Unstage unwanted files
git restore --staged .claude/commands/fix-bugs.md
git restore --staged ISSUE_962_FIX_SUMMARY.md
git restore --staged TEST_REPORT_*.md

# Step 4: Verify only desired files staged
git status
# Should show:
# Changes to be committed: (only your actual bug fixes)
# Untracked files: (temporary analysis files)

# Step 5: Create clean commit
git commit -m "fix: Resolve multiple bug issues

Issues addressed:
- #964: React controlled component warning
- #963: Type annotation UUID migration
- #962: Database test data cleanup
- #961: Query parameter preservation
- #929: Application name display
- #928: API field name alignment"

# Step 6: Force push (with safety check)
git push --force-with-lease origin fix/bug-batch-20251106-133816
```

## Alternative: Interactive Rebase (For Multiple Commits)

```bash
# If you have multiple commits with unwanted files scattered
git rebase -i HEAD~3

# In editor, mark commits to edit:
# edit abc1234 First commit
# pick def5678 Second commit
# edit ghi9012 Third commit

# For each "edit" stop:
git reset HEAD~1  # Unstage everything
git add <only-wanted-files>
git commit -c ORIG_HEAD
git rebase --continue
```

## File Exclusion Patterns

```bash
# Exclude by pattern (all test reports)
git restore --staged TEST_REPORT_*.md

# Exclude by directory
git restore --staged .claude/commands/

# Exclude multiple specific files
git restore --staged \
  ISSUE_962_FIX_SUMMARY.md \
  PR884_ARCHITECTURE_REVIEW.md \
  /tmp/fix-bugs-original.md
```

## Verification Checklist

```bash
# 1. Check what's staged
git diff --cached --name-only
# Should show ONLY bug fix files

# 2. Check what's in PR diff (after push)
gh pr view 967 --web
# Or: gh pr diff 967

# 3. Verify file count matches expected
# Example: 17 bug fix files (6 frontend, 11 backend)

# 4. Ensure temporary files are untracked
git status | grep -E "(TEST_REPORT|ISSUE_.*SUMMARY|\.claude/commands)"
# Should show as "Untracked files" NOT "deleted"
```

## Common Mistakes

### ❌ Wrong: Amending with git rm
```bash
git rm --cached unwanted.md
git commit --amend
# Shows deletion in PR if file existed in parent
```

### ❌ Wrong: Deleting files then committing
```bash
rm unwanted.md
git add -u
git commit
# Creates deletion commit, clutters PR history
```

### ❌ Wrong: Hard reset (loses changes)
```bash
git reset --hard HEAD~1
# DANGER: Loses all uncommitted work
```

### ✅ Correct: Soft reset + selective staging
```bash
git reset --soft <parent-commit>
git restore --staged <unwanted-files>
git commit -m "Clean commit message"
git push --force-with-lease
```

## Edge Cases

### Files Already in Parent Commit
If temporary file exists in parent (main branch):
```bash
# Don't unstage - let it show as deletion
# Or create .gitignore rule and commit separately:
echo ".claude/commands/" >> .gitignore
git add .gitignore
git commit -m "chore: Ignore temporary command files"
```

### Multiple Branches Affected
```bash
# Clean current branch first
git reset --soft origin/main
git restore --staged <unwanted>
git commit && git push --force-with-lease

# Then cherry-pick to other branches
git checkout other-branch
git cherry-pick <clean-commit-hash>
```

## Usage Guidelines
- **Use soft reset**: When removing files from most recent commit(s)
- **Use interactive rebase**: When files scattered across multiple commits
- **Use .gitignore**: To prevent future accidents
- **Always verify**: Check `gh pr diff` after force push
- **Force-with-lease**: Safer than `--force`, prevents overwriting others' work

## Session Context
Applied during PR #967 cleanup after /fix-bugs workflow accidentally committed:
- `.claude/commands/fix-bugs.md` (workflow definition)
- `ISSUE_962_FIX_SUMMARY.md` (QA analysis report)
- `TEST_REPORT_*.md` (4 Playwright test reports)

Result: Clean PR with only 17 bug fix files (6 frontend, 11 backend).
