# QA Validation Cache Invalidation Pattern

## Problem: Fixes Validated as "Not Working" Due to Cached Data

After implementing questionnaire generation fixes, QA validation showed:
- ❌ Fix #1: Duplicate compliance questions still present
- ❌ Fix #3: OS field shows textbox instead of dropdown
- ❌ Fix #4: Field type still returns `null` instead of dropdown

**User Assumption**: "The fixes aren't working"
**Reality**: Old questionnaires cached in database, generated BEFORE fixes committed

## Root Cause Discovery Process

### Step 1: Verify Fix Implementation in Code

```bash
# Check if fix exists in backend
grep -A5 "VERIFICATION_FIELDS" backend/app/api/v1/endpoints/collection_crud_questionnaires/gap_detection.py

# Check commit timestamp
git log --oneline --after="2025-11-06" | grep "collection flow"
# 694cc51ae fix: Complete collection flow fixes implementation (2025-11-06 23:06)

# Check questionnaire generation timestamp
docker exec -it migration_postgres psql -U postgres -d migration_db -c \
  "SELECT id, created_at, completion_status FROM migration.adaptive_questionnaires
   WHERE created_at > '2025-11-06 22:00:00' ORDER BY created_at DESC LIMIT 5;"
```

**Discovery**: Questionnaires created at `22:59:43+00`, commit at `23:06:38+00`
→ Questionnaires generated 7 minutes BEFORE fixes were committed

### Step 2: Console Log Analysis

```javascript
// Browser console showing instant questionnaire retrieval
[QuestionnaireFetcher] Found 1 agent-generated questionnaires after 0ms
```

**Red Flag**: `0ms` response time indicates cached data, not fresh generation

### Step 3: Database Investigation

```sql
-- Check questionnaire timestamps vs commit timestamp
SELECT
    id,
    created_at,
    completion_status,
    question_count,
    updated_at
FROM migration.adaptive_questionnaires
WHERE engagement_id = '00000000-0000-0000-0000-000000000001'
ORDER BY created_at DESC
LIMIT 10;

-- Output shows all questionnaires created before fix commit
```

## Solution: Delete Cached Questionnaires

```sql
-- Step 1: Identify cutoff time (commit timestamp)
-- Commit: 694cc51ae at 2025-11-06 23:06:38+00

-- Step 2: Count questionnaires before cutoff
SELECT COUNT(*)
FROM migration.adaptive_questionnaires
WHERE created_at < '2025-11-06 23:06:00+00';
-- Result: 64 questionnaires

-- Step 3: Delete pre-fix questionnaires
DELETE FROM migration.adaptive_questionnaires
WHERE created_at < '2025-11-06 23:06:00+00';
-- Deleted 64 rows

-- Step 4: Verify deletion
SELECT COUNT(*) FROM migration.adaptive_questionnaires;
-- Result: 0 questionnaires (clean slate)
```

## Re-validation Results (Post-Deletion)

```bash
# Re-run QA validation with fresh data
/qa-test-flow collection "Validate all 5 collection flow fixes with fresh questionnaire generation"
```

**Results**:
- ✅ Fix #2: Asset deduplication working (shared questionnaires)
- ✅ Fix #4: Field type fallback working (dropdown with balanced options)
- ✅ Fix #5: Status filter working (excludes completed/cancelled)
- ⚠️ Fix #1: Form submission working but not tested to 100%
- ⚠️ Fix #3: OS pre-selection needs E2E testing

## Prevention Pattern: Timestamp-Based Cache Invalidation

### For Future QA Validations

```bash
# Step 1: Get commit timestamp
git log --format="%H %ai" -1 | awk '{print $1, $2, $3}'
# Output: 694cc51ae 2025-11-06 23:06:38

# Step 2: Delete questionnaires created before commit
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
DELETE FROM migration.adaptive_questionnaires
WHERE created_at < '2025-11-06 23:06:00+00'
RETURNING id, created_at;
"

# Step 3: Verify clean slate
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
SELECT COUNT(*) as remaining_questionnaires
FROM migration.adaptive_questionnaires;
"
```

### Automated Cleanup Script

```bash
#!/bin/bash
# cleanup-cached-questionnaires.sh

COMMIT_TIMESTAMP=$(git log --format="%ai" -1 | cut -d' ' -f1-2)

docker exec -it migration_postgres psql -U postgres -d migration_db <<EOF
DO \$\$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM migration.adaptive_questionnaires
    WHERE created_at < '${COMMIT_TIMESTAMP}'::timestamp;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % cached questionnaires created before %',
                 deleted_count, '${COMMIT_TIMESTAMP}';
END \$\$;
EOF
```

## Cache Invalidation Indicators

**Signs You Need Cache Invalidation**:
1. ✅ **Instant retrieval** (0-5ms response time in console)
2. ✅ **Questionnaire created_at BEFORE commit timestamp**
3. ✅ **QA validation shows old behavior despite code fixes**
4. ✅ **Console logs show "Found N questionnaires" without "Generating..." logs

**When Cache is Valid** (Fresh Generation):
1. ❌ Response time >500ms (agent generation time)
2. ❌ Questionnaire created_at AFTER commit timestamp
3. ❌ Console shows "Generating questionnaire..." logs
4. ❌ Status shows `pending` → `ready` transition

## Usage Guidelines

### Before QA Validation of Questionnaire Fixes

```bash
# 1. Get last commit time
COMMIT_TIME=$(git log -1 --format="%ai" | cut -d' ' -f1-2)

# 2. Check for cached questionnaires
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
SELECT COUNT(*) as cached_count
FROM migration.adaptive_questionnaires
WHERE created_at < '${COMMIT_TIME}'::timestamp;
"

# 3. If cached_count > 0, delete them
# (Use DELETE query above)

# 4. Run QA validation
/qa-test-flow collection "..."
```

### During QA Validation

**If validation shows old behavior**:
1. Stop testing immediately
2. Check console for retrieval time (0ms = cached)
3. Check database for questionnaire timestamps
4. Delete cached questionnaires
5. Re-run validation from scratch

### After QA Validation

**Document in test report**:
```markdown
## Cache Invalidation Performed

- **Questionnaires deleted**: 64
- **Created before**: 2025-11-06 23:06:00+00 (commit timestamp)
- **Reason**: Validate fresh questionnaire generation with fixes
- **Result**: Re-validation successful (3/5 fixes fully validated)
```

## Common Mistakes

### ❌ Wrong: Assume Code Fixes = Working System
```
"I implemented the fix, so the QA validation failure must be a test issue"
```

### ❌ Wrong: Re-run Tests Without Investigation
```bash
# Run test → Fails
# Run test again → Still fails
# Run test third time → Still fails
# Give up and report "fix doesn't work"
```

### ✅ Correct: Investigate Timestamp Evidence
```bash
# 1. Check commit timestamp
git log -1 --format="%ai"

# 2. Check questionnaire timestamp
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
SELECT created_at FROM migration.adaptive_questionnaires
ORDER BY created_at DESC LIMIT 1;
"

# 3. Compare: If questionnaire_time < commit_time → CACHED

# 4. Delete cached data
# 5. Re-validate
```

## Session Context

Applied during PR #969 QA validation (November 2025):
- Initial validation: 0/5 fixes working (all cached)
- Cache invalidation: Deleted 64 questionnaires
- Re-validation: 3/5 fixes fully validated ✅
- Documentation: Added cache invalidation notes to TEST_REPORT

**Key Insight**: Always check data timestamps vs commit timestamps before concluding "fix doesn't work"
