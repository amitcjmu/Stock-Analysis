# Qodo Bot Security: Three-Tier Logging Pattern
Date: 2025-11-19
Context: PR #1070 - Qodo Bot Security Review

## Problem
Qodo Bot identified sensitive information exposure in logs:
1. Exception messages with SQL, tokens, paths in ERROR logs
2. Field names (schema details) in INFO logs
3. Asset names and identifiers in production logs
4. Auth flow details in frontend console

## Solution: Three-Tier Logging Strategy

### Tier 1: DEBUG Level (Development Only)
**Purpose**: Full diagnostic details for debugging
**Audience**: Developers in development environment
**Content**: Everything - exceptions, field names, asset names, SQL

### Tier 2: ERROR/INFO Level (Production Safe)
**Purpose**: Generic status and errors without sensitive data
**Audience**: Production monitoring, log aggregation
**Content**: Exception types, counts, generic status

### Tier 3: Database Storage (Audit Trail)
**Purpose**: User-facing error messages
**Audience**: End users, support team
**Content**: Generic error types only

## Backend Implementation Pattern

### Exception Handling (Tier 1 + Tier 2 + Tier 3)

**Location**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands/background_task.py:173-194`

```python
except Exception as e:
    # CC Security: Tier 1 - DEBUG level (full details)
    logger.debug(f"Background generation failed for flow {flow_id}: {e}", exc_info=True)
    logger.debug(f"Exception type: {type(e).__name__}")
    logger.debug(f"Exception details: {str(e)}")

    # CC Security: Tier 2 - ERROR level (generic only)
    logger.error(
        f"Background generation failed for flow {flow_id} "
        f"(exception type: {type(e).__name__})"
    )

    # CC Security: Tier 3 - Database (exception type only)
    error_msg = f"Questionnaire generation failed: {type(e).__name__}"
    async with AsyncSessionLocal() as db:
        await update_questionnaire_status(
            questionnaire_id, "failed", error_message=error_msg, db=db
        )
```

**Benefits**:
- Development: Full stack traces available for debugging
- Production: No SQL, tokens, or paths in logs
- Users: Clear generic errors without technical exposure

### Field Name Logging (Tier 1 Only)

**Location**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/section_helpers.py:120-125`

```python
# CC Security: Log field names at DEBUG level only (not INFO)
# Per Qodo Bot review: Field names are internal schema details
logger.debug(
    f"Section {section_id}: {len(filtered)}/{len(gaps)} gaps filtered "
    f"({', '.join(filtered) if filtered else 'none'})"
)
```

**Why**: Field names expose database schema structure
- ✅ DEBUG: Developers need field names for debugging
- ❌ INFO: Production logs should not reveal schema

### Asset Name Logging (Tier 2: Counts Only)

**Location**: `backend/app/api/v1/endpoints/collection_gap_analysis/analysis_endpoints/background_workers.py:49-54`

```python
# CC Security: Log count only at INFO (not asset details)
# Per Qodo Bot review: Asset names and field names should not be in INFO-level logs
logger.info(
    f"🔍 Cleaning up heuristic gaps for {len(analyzed_assets)} analyzed assets "
    f"(AI gaps authoritative, preserving {len(critical_attributes)} critical attributes)"
)
```

**Why**: Asset names may contain customer identifiable information
- ✅ INFO: Counts and aggregates (5 assets, 12 gaps)
- ❌ INFO: Asset names ("Customer XYZ Database")

## Frontend Implementation Pattern

### Conditional Logging (Development Only)

**Location**: `src/components/collection/DataGapDiscovery.tsx:266-282`

```typescript
// CC Security: Conditional logging (development only)
// Per Qodo Bot review: Console logs around auth flows can expose session behavior
if (import.meta.env.DEV) {
  console.log('🔄 Refreshing auth token before manual AI gap analysis...');
}

try {
  const { refreshAccessToken } = await import('@/lib/tokenRefresh');
  const newToken = await refreshAccessToken();

  if (newToken && import.meta.env.DEV) {
    console.log('✅ Token refreshed successfully before manual analysis');
  }
} catch (refreshError) {
  if (import.meta.env.DEV) {
    console.warn('⚠️ Token refresh failed, proceeding anyway:', refreshError);
  }
}
```

**Benefits**:
- Development builds: Full console logging for debugging
- Production builds: Silent (no auth flow exposure)
- Security: Production users never see session behavior

## When to Use Each Tier

### Use DEBUG for:
- Exception stack traces and messages
- Field names, column names, schema details
- Asset names, asset IDs, UUIDs
- SQL queries and parameters
- Token refresh details
- Detailed API request/response bodies

### Use INFO/ERROR for:
- Counts and aggregates (5 assets, 12 questions)
- Generic status ("questionnaire generated")
- Flow states ("phase completed")
- Exception types only ("ValueError")
- Performance metrics (duration, counts)

### Use Database Storage for:
- Generic user-facing errors
- Exception types only
- High-level status ("failed", "completed")
- NO stack traces or technical details

## Qodo Bot Security Principles

### Principle 1: Least Privilege (Logging)
Sensitive details (exception messages, field names, asset names) → DEBUG level only

### Principle 2: Defense in Depth
- Database: Generic errors
- Production logs: No schema details
- Development logs: Full diagnostics

### Principle 3: Fail Secure
Auth token refresh failures logged only in development

### Principle 4: Transparency
- CC Security comments explain each tier
- Qodo Bot review referenced in comments
- Documentation provides audit trail

## Pre-commit Hook Integration

These patterns are enforced by Qodo Bot review but should be followed proactively:

```python
# ❌ BAD - Exposes SQL in production
logger.error(f"Database error: {str(e)}")

# ✅ GOOD - Three-tier pattern
logger.debug(f"Database error: {str(e)}", exc_info=True)  # Tier 1
logger.error(f"Database error (type: {type(e).__name__})")  # Tier 2
error_msg = f"Operation failed: {type(e).__name__}"  # Tier 3 (DB)
```

## Verification Commands

```bash
# Check production logs for sensitive data exposure
docker logs migration_backend 2>&1 | grep -i "select\|insert\|update\|delete\|token\|password"
# Should return EMPTY (no SQL or credentials in logs)

# Check for field name exposure at INFO level
docker logs migration_backend 2>&1 | grep "INFO.*business_criticality\|data_classification"
# Should return EMPTY (field names only in DEBUG)

# Verify frontend production build
npm run build && grep -r "console\\.log" .next/
# Should show minimal console logs (wrapped in DEV checks)
```

## Related Memories
- `security_best_practices` - General security patterns
- `qodo_bot_pr_review_handling` - Qodo Bot integration
- `pr_review_patterns_collection_assessment_2025_01` - PR review workflows

## Documentation Reference
Full security review response: `/docs/security/QODO_BOT_REVIEW_RESPONSE.md`
