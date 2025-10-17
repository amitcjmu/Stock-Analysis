# Feature-Flagged Unmapped Asset Handling

**Status**: ✅ Implemented (Phase 1.2 - October 16, 2025)
**Issue**: Prevents "DevTestVM01" (server) from showing as individual "application"
**Implementation**: Progressive strictness with feature flags

---

## Overview

This feature implements progressive strictness for handling unmapped assets in assessment flows. It addresses the issue where unmapped assets (e.g., "DevTestVM01" server) were incorrectly displayed as individual "applications" instead of being grouped under canonical applications.

### Problem

- **Root Cause**: 83% of production assets unmapped (119/144)
- **Impact**: Assessment flows accept unmapped assets, breaking canonical application grouping
- **User Experience**: Individual assets like "DevTestVM01" appear as separate applications

### Solution

Feature-flagged validation with three modes:
1. **Banner** (default): Warn + proceed
2. **Block**: Reject if exceeds threshold
3. **Strict**: Always reject unmapped assets

---

## Configuration

### Environment Variables

```bash
# Mode selection (default: banner)
UNMAPPED_ASSET_HANDLING=banner    # Show warning, allow proceeding
UNMAPPED_ASSET_HANDLING=block     # Reject if exceeds threshold
UNMAPPED_ASSET_HANDLING=strict    # Always reject any unmapped

# Threshold for block mode (default: 0.5 = 50%)
UNMAPPED_ASSET_THRESHOLD=0.5      # 50% threshold
UNMAPPED_ASSET_THRESHOLD=0.3      # 30% threshold (stricter)
```

### Configuration in `backend/app/core/config.py`

```python
# Unmapped Asset Handling Configuration (Phase 1.2 - October 2025)
UNMAPPED_ASSET_HANDLING: str = Field(
    default="banner",
    env="UNMAPPED_ASSET_HANDLING",
    description=(
        "How to handle unmapped assets in assessment flows. "
        "Options: 'banner' (warn + proceed), 'block' (reject if >threshold), 'strict' (always reject)"
    ),
)
UNMAPPED_ASSET_THRESHOLD: float = Field(
    default=0.5,
    ge=0.0,
    le=1.0,
    env="UNMAPPED_ASSET_THRESHOLD",
    description="Maximum percentage of unmapped assets allowed (0.0-1.0, default 0.5 = 50%)",
)
```

---

## Behavior by Mode

### Mode 1: Banner (Default)

**Purpose**: Development and testing, gradual rollout

**Behavior**:
- ✅ Allow flow creation even with unmapped assets
- ⚠️ Log warning with tenant-scoped metrics
- 📊 Track unmapped percentage for monitoring
- 🎨 Frontend shows AssetResolutionBanner

**Use Case**:
- Local development
- New tenants onboarding
- Gradual migration to canonical grouping

**Example Log Output**:
```
[INFO] Assessment flow unmapped asset metrics: total=5, unmapped=4, percentage=80.0%, client_account_id=11111111-1111-1111-1111-111111111111, engagement_id=22222222-2222-2222-2222-222222222222
[WARNING] Assessment flow has 4 unmapped assets. Asset Resolution banner will be shown in UI.
```

**API Response**:
- Status: `200 OK`
- Flow created successfully
- Warning logged server-side

---

### Mode 2: Block with Threshold

**Purpose**: Staging environments, progressive enforcement

**Behavior**:
- ✅ Allow if unmapped percentage ≤ threshold
- ❌ Reject if unmapped percentage > threshold
- 📊 Log tenant-scoped metrics
- 🚫 Return 400 error with clear guidance

**Use Case**:
- Staging environments
- Phased rollout (start with 50%, tighten to 30%, then 10%)
- Tenants with partial canonical mapping

**Example Log Output (Within Threshold)**:
```
[INFO] Assessment flow unmapped asset metrics: total=5, unmapped=1, percentage=20.0%, client_account_id=..., engagement_id=...
[WARNING] Assessment flow has 1 unmapped assets (20.0%) but within threshold (50.0%). Proceeding with banner.
```

**Example Error Response (Exceeds Threshold)**:
```json
{
  "status": "failed",
  "error_code": "UNMAPPED_ASSETS_EXCEED_THRESHOLD",
  "message": "Assessment initialization blocked: 80.0% unmapped assets exceeds threshold of 50.0%. Unmapped assets (4): DevTestVM01, DevTestVM02, DevTestVM03, DevTestVM04. Please complete canonical application mapping to proceed.",
  "details": {
    "total_assets": 5,
    "unmapped_count": 4,
    "unmapped_percentage": 0.8,
    "threshold": 0.5,
    "unmapped_assets": ["DevTestVM01", "DevTestVM02", "DevTestVM03", "DevTestVM04"]
  }
}
```

**API Response**:
- Status: `400 Bad Request` (if exceeds threshold)
- Status: `200 OK` (if within threshold, warning logged)

---

### Mode 3: Strict

**Purpose**: Production, high-maturity tenants

**Behavior**:
- ❌ Always reject if ANY unmapped assets detected
- 📊 Log tenant-scoped metrics
- 🚫 Return 400 error immediately
- 🔒 Enforce 100% canonical mapping

**Use Case**:
- Production environments with mature data
- High-compliance tenants
- Post-migration cleanup phase

**Example Error Response**:
```json
{
  "status": "failed",
  "error_code": "UNMAPPED_ASSETS_STRICT_MODE",
  "message": "Assessment initialization blocked: 1 unmapped assets detected. Unmapped assets: DevTestVM01. Strict mode requires all assets mapped to canonical applications. Use Asset Resolution workflow in collection flow.",
  "details": {
    "total_assets": 10,
    "unmapped_count": 1,
    "unmapped_percentage": 0.1,
    "unmapped_assets": ["DevTestVM01"],
    "remediation": "Use Asset Resolution workflow in collection flow"
  }
}
```

**API Response**:
- Status: `400 Bad Request`
- No flow created

---

## Implementation Details

### File: `backend/app/core/config.py` (Lines 269-284)

Added configuration settings for feature flags.

### File: `backend/app/repositories/assessment_flow_repository/commands/flow_commands.py` (Lines 122-177)

**Key Changes**:
1. Calculate unmapped percentage
2. Collect unmapped asset names for error messages
3. Log tenant-scoped metrics (total, unmapped, percentage, tenant IDs)
4. Implement feature-flagged validation logic
5. Provide clear error messages with remediation guidance

**Code Flow**:
```python
# Step 6: Feature-flagged unmapped asset handling
unmapped_count = sum(1 for group in application_groups if group.canonical_application_id is None)
unmapped_percentage = unmapped_count / len(application_groups) if application_groups else 0

# Log tenant-scoped metrics
logger.info(f"Assessment flow unmapped asset metrics: total={len(application_groups)}, unmapped={unmapped_count}, percentage={unmapped_percentage:.1%}, client_account_id={client_account_id}, engagement_id={engagement_id}")

# Feature-flagged handling
if settings.UNMAPPED_ASSET_HANDLING == "strict":
    # Always reject
    raise ValueError(...)
elif settings.UNMAPPED_ASSET_HANDLING == "block":
    if unmapped_percentage > settings.UNMAPPED_ASSET_THRESHOLD:
        # Reject if exceeds threshold
        raise ValueError(...)
    else:
        # Within threshold - allow with warning
        logger.warning(...)
else:  # "banner" mode
    # Allow with warning
    logger.warning(...)
```

---

## Testing

### Unit Tests

**Test File**: `backend/test_unmapped_asset_handling.py`

**Test Coverage**:
- ✅ Banner mode configuration
- ✅ Block mode configuration with threshold
- ✅ Strict mode configuration
- ✅ Validation logic calculations
- ✅ Unmapped percentage accuracy

**Run Tests**:
```bash
docker exec migration_backend python test_unmapped_asset_handling.py
```

**Expected Output**:
```
============================================================
Phase 1.2 - Unmapped Asset Handling Feature Flag Tests
============================================================
✅ Banner Mode: PASSED
✅ Block Mode: PASSED
✅ Strict Mode: PASSED
✅ Validation Logic: PASSED
Test Results: 4 passed, 0 failed
```

### Integration Tests

**Test File**: `backend/test_unmapped_integration.py`

**Test Scenarios**:
1. Banner mode with 80% unmapped → Allow
2. Block mode with 80% unmapped (exceeds 50%) → Reject
3. Block mode with 20% unmapped (within 50%) → Allow
4. Strict mode with 10% unmapped → Reject

**Run Tests**:
```bash
docker exec migration_backend python test_unmapped_integration.py
```

**Expected Output**:
```
======================================================================
Phase 1.2 - Unmapped Asset Handling Integration Tests
======================================================================
✅ Banner mode test PASSED - Flow allowed to proceed
✅ Block mode test PASSED - Flow rejected as expected
✅ Block mode test PASSED - Flow allowed within threshold
✅ Strict mode test PASSED - Flow rejected even with 10% unmapped
Integration Test Results: 4 passed, 0 failed
```

---

## Production Deployment

### Recommended Rollout Strategy

#### Stage 1: Development (Week 1)
```bash
UNMAPPED_ASSET_HANDLING=banner
```
- Allow all flows
- Monitor unmapped percentage metrics
- Identify high-unmapped tenants

#### Stage 2: Staging (Week 2)
```bash
UNMAPPED_ASSET_HANDLING=block
UNMAPPED_ASSET_THRESHOLD=0.5  # Start lenient
```
- Block flows with >50% unmapped
- Validate error messages
- Test bulk mapping workflow

#### Stage 3: Production Gradual Tightening (Weeks 3-6)
```bash
# Week 3
UNMAPPED_ASSET_THRESHOLD=0.5

# Week 4 (after monitoring)
UNMAPPED_ASSET_THRESHOLD=0.3

# Week 5 (after cleanup)
UNMAPPED_ASSET_THRESHOLD=0.1

# Week 6 (high-maturity tenants only)
UNMAPPED_ASSET_HANDLING=strict
```

### Per-Tenant Configuration

For multi-tenant deployments, use environment-specific overrides:

```python
# Example: Tenant-specific settings (future enhancement)
TENANT_OVERRIDES = {
    "high_maturity_tenant_id": {
        "UNMAPPED_ASSET_HANDLING": "strict"
    },
    "new_tenant_id": {
        "UNMAPPED_ASSET_HANDLING": "banner"
    }
}
```

---

## Monitoring & Observability

### Metrics to Track

1. **Unmapped Asset Percentage** (by tenant)
   - Query logs for: `"Assessment flow unmapped asset metrics"`
   - Extract: `percentage=X%`

2. **Assessment Initialization Failures** (by mode)
   - Count `ValueError` exceptions with "Assessment initialization blocked"
   - Group by: `strict`, `block`, `banner`

3. **Bulk Mapping Usage**
   - Track POST requests to `/api/v1/canonical-applications/bulk-map-assets`
   - Measure: success rate, assets per operation

### Log Queries

**Find high-unmapped tenants**:
```bash
docker logs migration_backend | grep "unmapped asset metrics" | grep "percentage=.*[5-9][0-9]\..*%" | tail -20
```

**Count rejections by mode**:
```bash
docker logs migration_backend | grep "Assessment initialization blocked" | grep -oP "(strict|block|banner)" | sort | uniq -c
```

### Alerts

**Recommended Alerts**:
- ⚠️ Unmapped percentage > 50% for any tenant (warning)
- 🔴 Assessment initialization blocked in strict mode (critical)
- 📊 Block mode rejection rate > 10% (review threshold)

---

## Error Messages

### Strict Mode

```
Assessment initialization blocked: 1 unmapped assets detected.
Unmapped assets: DevTestVM01.
Strict mode requires all assets mapped to canonical applications.
Use Asset Resolution workflow in collection flow.
```

### Block Mode (Exceeds Threshold)

```
Assessment initialization blocked: 80.0% unmapped assets exceeds threshold of 50.0%.
Unmapped assets (4): DevTestVM01, DevTestVM02, DevTestVM03, DevTestVM04.
Please complete canonical application mapping to proceed.
```

### Banner Mode (Warning)

```
Assessment flow has 4 unmapped assets.
Asset Resolution banner will be shown in UI.
```

---

## Success Criteria

- ✅ Feature flags configurable via environment variables
- ✅ Tenant-scoped metrics logged for monitoring
- ✅ "banner" mode allows proceeding (default)
- ✅ "block" mode rejects if exceeds threshold
- ✅ "strict" mode always rejects unmapped assets
- ✅ Clear error messages with remediation guidance
- ✅ Unit tests pass (4/4)
- ✅ Integration tests pass (4/4)

---

## References

- **Remediation Plan**: `/docs/planning/Assessment/ASSESSMENT_CANONICAL_GROUPING_REMEDIATION_PLAN.md` (Lines 387-540)
- **Implementation**:
  - `backend/app/core/config.py` (Lines 269-284)
  - `backend/app/repositories/assessment_flow_repository/commands/flow_commands.py` (Lines 122-177)
- **Tests**:
  - `backend/test_unmapped_asset_handling.py`
  - `backend/test_unmapped_integration.py`

---

## Future Enhancements

### Phase 2: Bulk Asset Mapping UI (Task 2.2)
- Add "Map X Unmapped Assets" button
- Bulk mapping dialog with canonical app selector
- In-line result confirmation

### Phase 3: Auto-Enrichment (Task 3.1)
- Feature-flagged auto-enrichment on flow initialization
- Background task processing
- Per-flow "in_progress" lock

### Phase 4: Tenant-Specific Overrides
- Database-backed tenant configuration
- Override global feature flags per tenant
- Admin UI for configuration management

---

**Last Updated**: October 16, 2025
**Version**: 1.0
**Status**: ✅ Production Ready
