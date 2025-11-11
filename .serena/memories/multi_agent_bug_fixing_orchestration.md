# Multi-Agent Bug Fixing Orchestration Patterns

## Problem
Coordinating parallel QA analysis across multiple bugs, managing batch approval workflows, and handling git operations for clean PR creation with code review feedback integration.

## Solution Architecture

### 1. Parallel QA Agent Execution (7x Speedup)
```typescript
// Launch all QA agents concurrently instead of sequentially
const qaPromises = actionableBugs.map(bug =>
  Task({
    subagent_type: "qa-playwright-tester",
    prompt: `Analyze GitHub issue #${bug.number}: ${bug.title}...`
  })
);

const results = await Promise.all(qaPromises);
// Result: 7 bugs analyzed in ~1.5 hours instead of ~7 hours
```

**Key Pattern**: Use parallel Task invocations for independent analysis work. Sequential only for implementation after approval.

### 2. Git Clean PR Creation After Unwanted Files
```bash
# Problem: Temporary files committed (.claude/commands/*.md, TEST_REPORT_*.md)

# WRONG: Using git rm --cached (shows deletions in PR)
git rm --cached .claude/commands/fix-bugs.md
git commit --amend

# CORRECT: Soft reset to parent, exclude files, clean commit
git reset --soft bf89a488a  # Parent commit
git restore --staged .claude/commands/fix-bugs.md ISSUE_*.md TEST_*.md
git commit -m "fix: Bug batch fixes - clean version"
git push --force-with-lease
```

**Usage**: When temporary/gitignored files accidentally added to PR.

### 3. Database Migration JSONB Safety Pattern
```python
# Problem: JSONB filtering can produce NULL instead of empty object

# WRONG: Direct filtering
SET phase_results = (
    SELECT jsonb_object_agg(key, value)
    FROM jsonb_each(phase_results)
    WHERE NOT (value::text LIKE '%Test error%')
)
# Result: NULL when all keys filtered

# CORRECT: Use COALESCE for empty object fallback
SET phase_results = COALESCE(
    (
        SELECT jsonb_object_agg(key, value)
        FROM jsonb_each(phase_results)
        WHERE NOT (value::text LIKE '%Test error%')
    ),
    '{}'::jsonb
)
```

**Rule**: Always COALESCE JSONB aggregations that might filter all keys.

### 4. Conditional Query Parameter Preservation (Security)
```typescript
// Problem: Unconditional param preservation leaks context between sections

// WRONG: Always preserve all query params
const pathWithParams = `${item.path}${location.search}`;

// CORRECT: Only preserve within same section
const getNavigationPath = () => {
  const currentSection = location.pathname.split('/')[1];
  const targetSection = item.path.split('/')[1];

  // Prevent flow_id leakage: /decommission → /assessment
  if (currentSection === targetSection && location.search) {
    return `${item.path}${location.search}`;
  }

  return item.path;
};
```

**Usage**: Navigation components in multi-tenant, flow-based systems. Prevents cross-section context leakage.

### 5. Batch Approval Workflow Pattern
```bash
# User provides space-separated approvals
approve 928 929 961 963 more-info 964

# Parse into categories
APPROVED=(928 929 961 963)
NEEDS_INFO=(964)

# Sequential implementation only after approval
for issue in ${APPROVED[@]}; do
  # SRE agent implements
  # DevSecOps validates
  # QA verifies
  # Only proceed if all pass
done
```

**Key Insight**: Never implement without explicit approval. Detailed analysis for "more-info" requests before proceeding.

### 6. Pre-commit Hook Failure Recovery
```bash
# First commit fails: unused imports in migration
# backend/alembic/versions/127_*.py:11:1: F401 'sqlalchemy as sa' imported but unused

# Fix: Remove unused imports before retry
# Removed: import sqlalchemy as sa
# Removed: from sqlalchemy.dialects import postgresql

git add backend/alembic/versions/127_cleanup_assessment_test_data.py
git commit -m "fix: Remove unused imports"
# Now passes all checks
```

**Pattern**: Read flake8/mypy errors carefully, fix exact violations, don't disable checks.

### 7. Code Review Feedback Integration
```markdown
# Qodobot/Coderabbit provides structured feedback:
- Security: JSONB NULL handling
- Security: Query param leakage
- Documentation: Missing issue in PR description

# Response workflow:
1. Fix each item in separate commit
2. Push with clear commit message referencing feedback
3. Update PR description to document fixes
4. Don't argue - fix or explain why not applicable
```

## Metrics from Session
- **Bugs Fixed**: 6 (964, 963, 962, 961, 929, 928)
- **Files Changed**: 17 (6 frontend, 11 backend)
- **Pre-commit Iterations**: 2 (unused imports on first)
- **Force Push Count**: 3 (cleaning unwanted files + code review fixes)
- **QA Parallel Speedup**: 7x (1.5h vs 7h sequential)

## Common Mistakes Avoided
1. ❌ Sequential QA analysis (slow)
2. ❌ Using `git rm --cached` for gitignored files (shows deletions)
3. ❌ Unconditional query param preservation (security leak)
4. ❌ Missing COALESCE in JSONB aggregations (NULL instead of `{}`)
5. ❌ Implementing fixes before user approval (wasted work if rejected)

## When to Apply
- Multi-bug orchestration workflows
- Batch PR creation with review feedback
- JSONB filtering in PostgreSQL migrations
- React Router navigation in multi-tenant apps
- Any parallel agent coordination tasks
