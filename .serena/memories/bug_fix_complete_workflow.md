# Complete Bug Fix Workflow

## Critical Steps (DO NOT SKIP ANY)

### 1. Issue Discovery & Triage
```bash
gh issue list --label bug --state open --json number,title,body,comments
```
- Check for "Fixed", "Resolved", "WIP" in comments
- Prioritize by labels (P0, P1, critical, high)
- Limit to 5 issues per batch

### 2. Create Working Branch
```bash
git checkout -b fix/bug-batch-$(date +%Y%m%d)
```

### 3. Multi-Agent Fix Process
For each bug:
1. **QA Agent** - Reproduce & analyze
2. **SRE Agent** - Implement fix
3. **DevSecOps** - Validate & lint
4. **QA Validation** - Verify fix (unlimited iterations)

### 4. Handle PR Reviews Completely
**IMPORTANT**: Address ALL review feedback in the SAME PR:
- Must-fix items
- High-priority items
- Don't defer to follow-up PRs

Example fixes from this session:
```python
# Breaking change compatibility
api_router.include_router(
    data_cleansing_router,
    prefix="/data-cleansing",  # Temporary compatibility
    tags=["Legacy (Deprecated)"]
)

# TypeScript type safety
export interface DataCleansingStats {
  total_records: number;
  // ... full interface, no 'any'
}

# Pluggable patterns
class PatternProvider(ABC):
    @abstractmethod
    async def get_patterns(self) -> Dict[str, List[str]]:
        pass
```

### 5. Commit & PR
```bash
git add -A
git commit -m "fix: Resolve multiple bug issues

Issues addressed in this batch:
- #120: Data Cleansing has zero records
- #119: Incorrect data mapping
..."

gh pr create --title "fix: Bug batch fixes" --body "..."
```

### 6. UPDATE GITHUB ISSUES (CRITICAL - OFTEN MISSED!)
**This step is frequently forgotten but essential for communication:**

```bash
# For each fixed issue
gh issue comment $ISSUE_NUM --body "## ✅ Issue Fixed

### Resolution Summary
[What was fixed]

### Root Cause
[Why it broke]

### Changes Made
[What you changed]

### Validation
- Bug reproduced locally: Yes
- Fix applied and tested: Yes
- Regression tests: Passed

### Pull Request
Fixed in PR: #122 (merged to main)"

# Close issues after merge
for issue in 120 119 109 105 104; do
  gh issue close $issue --comment "Closing as fixed in PR #122"
done
```

### 7. Cleanup
```bash
git checkout main
git pull origin main
git branch -d fix/bug-batch-20250118
git remote prune origin
```

## Key Lessons
1. **Never skip GitHub issue updates** - Shows work was done
2. **Fix all review feedback in same PR** - Avoids PR sprawl
3. **Test with proper agent coordination** - QA validates each fix
4. **Document breaking changes** - Add compatibility routes
5. **Type safety over convenience** - Remove all 'any' types

## Common Mistakes to Avoid
- ❌ Forgetting to comment on GitHub issues
- ❌ Deferring review feedback to "follow-up PR"
- ❌ Using `--no-verify` without running pre-commit at least once
- ❌ Not providing backward compatibility for breaking changes
- ❌ Leaving TypeScript 'any' types in code
