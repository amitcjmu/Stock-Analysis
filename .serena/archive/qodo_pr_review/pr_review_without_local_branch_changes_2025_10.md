# PR Review Without Local Branch Changes

## Problem
During PR #847 re-review, I incorrectly checked out the PR branch locally:
```bash
git checkout feature/cmdb-fields-enhancement-833  # ❌ WRONG
```

**User Feedback**: "Why did you go to this branch? This will affect other testing going on locally. Get back to the proper main branch and limit your validations and verifications to the git repository and the code in the PR branch."

## Root Cause
- Agent assumed branch checkout was necessary to inspect files
- Disrupted user's local testing environment
- Caused unnecessary git state changes

## Solution: Remote-Only PR Review Workflow

### 1. Fetch PR Metadata (No Checkout)
```bash
# Get PR details without touching local branches
gh pr view 847 --json number,title,state,commits,files,additions,deletions,headRefName,baseRefName

# Check if related PRs were merged (critical for migration conflicts)
gh pr view 848 --json state,mergedAt
# Output: {"mergedAt":"2025-10-29T20:29:12Z","state":"MERGED"}
```

### 2. Inspect Files in Remote Branches
```bash
# List files in main branch without checkout
git ls-tree -r --name-only origin/main backend/alembic/versions/ | grep "^backend/alembic/versions/[0-9]" | tail -10

# Check specific file content in remote branch
# Option A: Use GitHub raw URLs with Read tool (if available)
# Option B: Use gh pr diff command
gh pr diff 847 --patch

# Option C: Fetch remote branch and read without checkout
git fetch origin feature/cmdb-fields-enhancement-833
git show origin/feature/cmdb-fields-enhancement-833:backend/alembic/versions/112_add_cmdb_explicit_fields.py
```

### 3. Verify Migration Conflicts
```bash
# WITHOUT checkout, check what migrations exist in main
git ls-tree -r --name-only origin/main backend/alembic/versions/ | grep "[0-9][0-9][0-9]_"

# Compare with PR branch
git ls-tree -r --name-only origin/feature/cmdb-fields-enhancement-833 backend/alembic/versions/ | grep "[0-9][0-9][0-9]_"

# Show diff between main and PR branch for specific directory
git diff origin/main...origin/feature/cmdb-fields-enhancement-833 -- backend/alembic/versions/
```

### 4. Post Review
```bash
# Create review document locally
cat > /tmp/pr847_review.md << 'EOF'
# PR Review Findings
...
EOF

# Post as comment (stays on current branch)
gh pr comment 847 --body-file /tmp/pr847_review.md
```

## Key Commands Reference

### Safe PR Inspection (Never Changes Local State)
```bash
gh pr view <num> --json state,mergedAt,commits,files
gh pr diff <num> --patch
git show origin/<branch>:<file-path>
git ls-tree -r --name-only origin/<branch> <directory>
git diff origin/main...origin/<pr-branch> -- <path>
```

### AVOID These Commands During PR Review
```bash
git checkout <pr-branch>           # ❌ Changes local state
git switch <pr-branch>             # ❌ Changes local state
git pull origin <pr-branch>        # ❌ Modifies local branch
```

## Migration Conflict Detection Pattern

When reviewing PR with database migrations:

```bash
# 1. Check if related PRs merged first
gh pr view <related-pr-num> --json state,mergedAt

# 2. If merged, check what migrations are now in main
git ls-tree -r --name-only origin/main backend/alembic/versions/ | grep "[0-9][0-9][0-9]_" | tail -10

# 3. Check migrations in PR branch
gh pr view <num> --json files | jq '.files[].path' | grep alembic/versions

# 4. Identify conflicts (same migration numbers)
# Example: PR #848 merged with 112-115, PR #847 still has 112-117 → CONFLICT
```

## Usage
Apply this pattern when:
- User asks to review a PR
- User explicitly says "stay on main branch"
- Multiple PRs touching same files (migrations, API endpoints)
- User has local testing in progress

## Benefits
- ✅ No disruption to user's local environment
- ✅ Always reviews latest remote state
- ✅ Detects merge conflicts with recently merged PRs
- ✅ Can review multiple PRs in parallel without branch switches
