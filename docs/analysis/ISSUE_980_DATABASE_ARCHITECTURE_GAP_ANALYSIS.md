# Issue #980: Database Architecture Gap Analysis
## Intelligent Gap Detection Data Flow Disconnect

**Date:** 2025-11-09
**Analyst:** Database Architecture Review
**Severity:** HIGH - Data propagation failure affecting core feature

---

## Executive Summary

The intelligent gap detection workflow suffers from a **critical data propagation disconnect** between questionnaire responses and Asset table updates. While responses ARE being saved to the database, the data flow breaks at the gap resolution stage, preventing Asset fields from being updated and readiness scores from improving.

**Root Cause:** The `resolved_value` field in `collection_data_gaps` is NOT populated with response values, causing the asset writeback service to find no data to propagate.

---

## 1. Database Schema Analysis

### 1.1 Table Relationships (Schema Diagram)

```
┌─────────────────────────────────────┐
│ collection_questionnaire_responses  │
│ ─────────────────────────────────── │
│ • id (PK)                           │
│ • collection_flow_id (FK)           │
│ • gap_id (FK) → collection_data_gaps│
│ • asset_id (FK) → assets            │
│ • question_id                       │
│ • response_value JSONB              │ ← DATA HERE
│ • confidence_score                  │
│ • responded_at                      │
└─────────────────────────────────────┘
            ↓ (gap_id FK)
┌─────────────────────────────────────┐
│ collection_data_gaps                │
│ ─────────────────────────────────── │
│ • id (PK)                           │
│ • collection_flow_id (FK)           │
│ • asset_id (FK) → assets            │
│ • field_name (e.g., "operating_    │
│     system", "criticality")         │
│ • resolution_status                 │
│   ('pending', 'resolved')           │
│ • resolved_value TEXT               │ ← EMPTY (PROBLEM!)
│ • priority, impact_on_sixr          │
└─────────────────────────────────────┘
            ↓ (should propagate to)
┌─────────────────────────────────────┐
│ assets                              │
│ ─────────────────────────────────── │
│ • id (PK)                           │
│ • name                              │
│ • operating_system                  │ ← NULL (never updated)
│ • criticality                       │ ← NULL (never updated)
│ • application_type                  │ ← NULL (never updated)
│ • assessment_readiness_score        │ ← 0% (never recalculated)
│ • completeness_score                │ ← NULL
│ • technical_details JSONB           │
│ • custom_attributes JSONB           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ collection_gap_analysis             │
│ ─────────────────────────────────── │
│ • id (PK)                           │
│ • collection_flow_id (FK)           │
│ • completeness_percentage           │ ← NOT updated after responses
│ • fields_collected                  │ ← NOT recalculated
│ • critical_gaps JSONB               │
└─────────────────────────────────────┘
```

### 1.2 Enrichment Tables (Related but Not Part of Data Flow)

```sql
-- These tables exist for enrichment but are not involved in the current data propagation issue
migration.asset_resilience           -- RTO/RPO, SLA requirements
migration.asset_compliance_flags     -- Compliance scopes (GDPR, HIPAA, etc.)
migration.asset_vulnerabilities      -- Security vulnerabilities
```

---

## 2. Data Flow Analysis

### 2.1 Expected Data Flow

```
1. GapAnalyzer identifies missing Asset fields
   ↓
2. Adaptive questionnaire generated based on gaps
   ↓
3. User submits responses via frontend
   ↓
4. Backend saves to collection_questionnaire_responses
   ↓ [MISSING STEP]
5. SHOULD copy response_value → resolved_value in collection_data_gaps
   ↓ [MISSING STEP]
6. SHOULD propagate resolved_value → assets.{field_name}
   ↓
7. Recalculate assessment_readiness_score
   ↓
8. Update collection_gap_analysis.completeness_percentage
```

### 2.2 Actual Data Flow (With Breakpoints)

```
1. GapAnalyzer identifies gaps ✅
   ↓
2. Questionnaire generated ✅
   ↓
3. User submits responses ✅
   ↓
4. Saved to collection_questionnaire_responses ✅
   response_value = {"value": "Linux"} ✅
   ↓
5. resolve_data_gaps() marks gap as resolved ✅
   resolution_status = 'resolved' ✅
   resolved_value = '' ❌ (EMPTY!)
   ↓
6. apply_asset_writeback() query finds resolved gaps ✅
   BUT resolved_value is EMPTY ❌
   field_updates = {} (empty dict) ❌
   ↓
7. No Asset fields updated ❌
   operating_system = NULL (unchanged) ❌
   ↓
8. assessment_readiness_score = 0.4 (unchanged) ❌
```

---

## 3. Database Query Results

### 3.1 Questionnaire Responses (Data IS Being Saved)

```sql
SELECT
    id,
    asset_id,
    question_id,
    response_value::text,
    created_at
FROM migration.collection_questionnaire_responses
ORDER BY created_at DESC
LIMIT 5;
```

**Result:**
```
id                                  | asset_id | question_id               | response_value                    | created_at
------------------------------------+----------+---------------------------+-----------------------------------+---------------------------
43f53055-9b76-4da9-a3c6-88b6a01af2d9| NULL     | business_logic_complexity | {"value": "moderate"}             | 2025-11-09 18:21:06.517321
78238098-79a3-4856-a49f-9d36af14186e| NULL     | dependencies              | {"value": ["low"]}                | 2025-11-09 18:21:06.517319
bc45283e-dd97-4f83-a1fa-7056ff46bdaf| NULL     | architecture_pattern      | {"value": "microservices"}        | 2025-11-09 18:21:06.517316
736e4218-7201-4f1b-bff7-580b183f156f| NULL     | technology_stack          | {"value": ["python"]}             | 2025-11-09 18:21:06.517314
9dbb9468-1a3c-464d-b3e5-d1fd81f37e39| NULL     | business_owner            | {"value": ["executive_c_level"]}  | 2025-11-09 18:21:06.517312
```

**Finding:** Responses contain actual data in `response_value` JSONB field ✅

### 3.2 Data Gaps (Marked Resolved but No Value)

```sql
SELECT
    id,
    asset_id,
    field_name,
    resolution_status,
    LENGTH(COALESCE(resolved_value, '')) AS resolved_value_len,
    created_at
FROM migration.collection_data_gaps
WHERE resolution_status = 'resolved'
ORDER BY updated_at DESC
LIMIT 5;
```

**Result:**
```
id                                  | asset_id                             | field_name                | resolution_status | resolved_value_len | created_at
------------------------------------+--------------------------------------+---------------------------+-------------------+--------------------+---------------------------
7d53e42a-7ca0-4711-93a3-dffb8baa1ea5| 778f9a98-1ed9-4acd-8804-bdcec659ac00 | technology_stack          | resolved          | 0                  | 2025-11-09 14:08:22.440225
9d6f1e22-1c2d-4d58-8805-a456ce619d53| 778f9a98-1ed9-4acd-8804-bdcec659ac00 | architecture_pattern      | resolved          | 0                  | 2025-11-09 14:08:22.433827
8c67d062-175e-4c5c-80b8-23187d9943d6| c0691645-5e81-4530-98af-55f906c49ddd | technology_stack          | resolved          | 0                  | 2025-11-01 02:34:00.556036
```

**CRITICAL FINDING:**
- `resolution_status = 'resolved'` ✅
- `resolved_value_len = 0` ❌ **(EMPTY!)**
- Data never copied from `response_value` → `resolved_value`

### 3.3 Asset Fields (Remain NULL)

```sql
SELECT
    id,
    name,
    operating_system,
    criticality,
    application_type,
    assessment_readiness_score,
    completeness_score
FROM migration.assets
WHERE id = '778f9a98-1ed9-4acd-8804-bdcec659ac00';
```

**Result:**
```
id                                  | name             | operating_system | criticality | application_type | assessment_readiness_score | completeness_score
------------------------------------+------------------+------------------+-------------+------------------+----------------------------+-------------------
778f9a98-1ed9-4acd-8804-bdcec659ac00| Analytics Engine | NULL             | Low         | NULL             | 0.39999999999999997        | NULL
```

**Finding:** Asset fields remain NULL despite resolved gaps ❌

---

## 4. Code Analysis - The Missing Link

### 4.1 Questionnaire Submission Flow

**File:** `/backend/app/api/v1/endpoints/collection_crud_update_commands/questionnaire_submission.py`

```python
# Line 220: Marks gaps as "resolved" but does NOT copy response_value
gaps_resolved = await resolve_data_gaps(gap_index, form_responses, db)

# Line 267: Calls asset writeback (but no data to write back)
await apply_asset_writeback(gaps_resolved, flow, context, current_user, db)
```

### 4.2 Gap Resolution Function (THE PROBLEM)

**File:** `/backend/app/api/v1/endpoints/collection_crud_helpers.py:243-308`

```python
async def resolve_data_gaps(
    gap_index: Dict[str, Any],
    form_responses: Dict[str, Any],
    db: AsyncSession,
) -> int:
    """Mark gaps as resolved for fields that received responses."""
    gaps_resolved = 0

    for field_name, value in form_responses.items():
        if value is None or value == "":
            continue

        gap = gap_index.get(field_name)  # Find gap by field name

        if gap:
            # ❌ CRITICAL BUG: Only updates status, NOT resolved_value
            gap.resolution_status = "resolved"
            gap.resolved_at = datetime.utcnow()
            gap.resolved_by = "manual_submission"
            gaps_resolved += 1

            # ❌ MISSING: gap.resolved_value = value  # Should copy response value here!
```

**What's Missing:**
```python
# Line 296 should be:
gap.resolution_status = "resolved"
gap.resolved_at = datetime.utcnow()
gap.resolved_by = "manual_submission"
gap.resolved_value = json.dumps(value) if isinstance(value, dict) else str(value)  # ← MISSING!
gaps_resolved += 1
```

### 4.3 Asset Writeback Function (No Data to Write)

**File:** `/backend/app/services/flow_configs/collection_handlers/asset_handlers.py:117-179`

```python
async def apply_resolved_gaps_to_assets(...):
    # Query for resolved gaps
    resolved_rows = await db.execute(
        text(
            "SELECT DISTINCT "
            "COALESCE(g.field_name, r.question_id) AS field_name, "
            "r.response_value, "  # ← Queries response_value from responses table
            "r.asset_id, "
            "(g.metadata->>'asset_id') AS asset_id_hint, "
            "(g.metadata->>'application_name') AS app_name_hint "
            "FROM migration.collection_questionnaire_responses r "
            "LEFT JOIN migration.collection_data_gaps g ON g.id = r.gap_id "
            "WHERE r.collection_flow_id = :flow_id "
            "AND (g.resolution_status = 'resolved' OR r.gap_id IS NULL)"
            "AND r.response_value IS NOT NULL"
        ),
        {"flow_id": collection_flow_id},
    )

    # ✅ WORKAROUND: Reads directly from responses table (bypassing gaps)
    # This means it SHOULD work, but there's a mismatch in field name mapping
```

**Helper Function:**

**File:** `/backend/app/services/flow_configs/collection_handlers/base.py`

```python
def build_field_updates_from_rows(resolved_rows):
    """Extract field updates from response rows."""
    field_updates = {}

    for row in resolved_rows:
        field_name = row.field_name
        response_value = row.response_value  # JSONB from responses table

        if response_value and isinstance(response_value, dict):
            value = response_value.get('value')  # Extract {"value": "Linux"} → "Linux"
            field_updates[field_name] = value

    return field_updates
```

---

## 5. The Actual Problem - Field Name Mismatch

### 5.1 Field Name Mapping Issue

The asset writeback service queries:
```sql
COALESCE(g.field_name, r.question_id) AS field_name
```

But:
- `collection_data_gaps.field_name` = "operating_system" (Asset column name)
- `collection_questionnaire_responses.question_id` = "operating_system_version" (Questionnaire field ID)

**Mapping Whitelist** (asset_handlers.py:185-196):
```python
whitelist = {
    "environment": "environment",
    "business_criticality": "business_criticality",
    "business_owner": "business_owner",
    "operating_system_version": "operating_system",  # Maps question_id → Asset column
    "cpu_cores": "cpu_cores",
    # ...
}
```

**Problem:** When `gap_id IS NULL` (response not linked to gap), uses `question_id` from responses, but field name normalization may fail if:
1. Question ID doesn't match whitelist key
2. Composite field IDs (e.g., `{asset_id}__{field_name}`) aren't handled
3. Custom attributes prefix (e.g., `custom_attributes.architecture_pattern`) not stripped

---

## 6. Missing Database Components

### 6.1 No Triggers

```sql
-- Query: Check for triggers on relevant tables
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_schema = 'migration'
AND event_object_table IN (
    'collection_questionnaire_responses',
    'collection_data_gaps',
    'assets'
);
```

**Result:**
```
trigger_name                       | event_manipulation | event_object_table
-----------------------------------+--------------------+-------------------
update_collection_data_gaps_updated_at | UPDATE          | collection_data_gaps
```

**Finding:** Only a timestamp trigger exists. **No data propagation triggers.**

### 6.2 No Stored Procedures

```sql
-- Query: Check for stored procedures
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'migration'
AND (
    routine_name LIKE '%gap%'
    OR routine_name LIKE '%response%'
    OR routine_name LIKE '%asset%'
);
```

**Result:** `0 rows` - **No stored procedures exist.**

### 6.3 No ETL Jobs

No scheduled jobs or background workers to:
- Copy `response_value` → `resolved_value`
- Propagate `resolved_value` → Asset columns
- Recalculate `completeness_percentage`
- Update `assessment_readiness_score`

---

## 7. Root Cause Summary

The data flow disconnect occurs at **TWO critical points:**

### 7.1 Primary Issue: `resolved_value` Not Populated

**Location:** `collection_crud_helpers.py:resolve_data_gaps()` (Line 296)

```python
# Current code (BROKEN):
gap.resolution_status = "resolved"
gap.resolved_at = datetime.utcnow()
gap.resolved_by = "manual_submission"
# ❌ MISSING: gap.resolved_value = ...

# Should be:
gap.resolution_status = "resolved"
gap.resolved_at = datetime.utcnow()
gap.resolved_by = "manual_submission"
gap.resolved_value = json.dumps(value) if isinstance(value, dict) else str(value)  # ✅ FIX
```

### 7.2 Secondary Issue: Field Name Mapping

**Location:** `asset_handlers.py:apply_resolved_gaps_to_assets()`

The SQL query:
```sql
COALESCE(g.field_name, r.question_id) AS field_name
```

Works ONLY if:
1. Gap is properly linked (`gap_id` IS NOT NULL)
2. Question ID matches whitelist keys exactly
3. No composite field IDs or custom prefixes

**Workaround in code:** Uses `response_value` directly from responses table (bypassing gaps), but field name normalization still fragile.

---

## 8. Recommended Database Architecture Fix

### 8.1 Immediate Fix (Code-Level)

**File:** `backend/app/api/v1/endpoints/collection_crud_helpers.py`

```python
async def resolve_data_gaps(
    gap_index: Dict[str, Any],
    form_responses: Dict[str, Any],
    db: AsyncSession,
) -> int:
    """Mark gaps as resolved for fields that received responses."""
    gaps_resolved = 0

    for field_name, value in form_responses.items():
        if value is None or value == "":
            continue

        gap = gap_index.get(field_name)

        if gap:
            gap.resolution_status = "resolved"
            gap.resolved_at = datetime.utcnow()
            gap.resolved_by = "manual_submission"

            # ✅ FIX: Populate resolved_value with response data
            if isinstance(value, dict):
                # Extract "value" key from {"value": "Linux"} format
                gap.resolved_value = json.dumps(value.get("value", value))
            elif isinstance(value, list):
                gap.resolved_value = json.dumps(value)
            else:
                gap.resolved_value = str(value)

            gaps_resolved += 1

            logger.info(
                f"Resolved gap {gap.id} ({gap.field_name}) with value: {gap.resolved_value}"
            )
```

### 8.2 Enhanced Fix (Database-Level Trigger)

**Migration:** `093_add_gap_resolution_trigger.py`

```python
"""Add trigger to copy response_value to resolved_value when gap is resolved"""

def upgrade():
    op.execute("""
        -- Function to sync response value to gap resolved_value
        CREATE OR REPLACE FUNCTION migration.sync_response_to_gap()
        RETURNS TRIGGER AS $$
        BEGIN
            -- When a questionnaire response is inserted and linked to a gap
            IF NEW.gap_id IS NOT NULL AND NEW.response_value IS NOT NULL THEN
                UPDATE migration.collection_data_gaps
                SET
                    resolved_value = NEW.response_value::text,
                    resolution_status = 'resolved',
                    resolved_at = NOW(),
                    resolved_by = COALESCE(NEW.responded_by::text, 'auto_sync')
                WHERE id = NEW.gap_id
                AND resolution_status = 'pending';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Trigger on questionnaire responses
        CREATE TRIGGER trg_sync_response_to_gap
        AFTER INSERT OR UPDATE ON migration.collection_questionnaire_responses
        FOR EACH ROW
        EXECUTE FUNCTION migration.sync_response_to_gap();
    """)

def downgrade():
    op.execute("""
        DROP TRIGGER IF EXISTS trg_sync_response_to_gap ON migration.collection_questionnaire_responses;
        DROP FUNCTION IF EXISTS migration.sync_response_to_gap();
    """)
```

### 8.3 Comprehensive Fix (Stored Procedure for Asset Updates)

**Migration:** `094_add_asset_update_procedure.py`

```python
"""Add stored procedure to propagate resolved gaps to Asset fields"""

def upgrade():
    op.execute("""
        -- Function to propagate resolved gaps to assets
        CREATE OR REPLACE FUNCTION migration.propagate_gaps_to_assets(
            p_collection_flow_id UUID
        )
        RETURNS TABLE(assets_updated INT, fields_updated INT) AS $$
        DECLARE
            v_assets_updated INT := 0;
            v_fields_updated INT := 0;
        BEGIN
            -- Update assets from resolved gaps
            WITH resolved_data AS (
                SELECT
                    g.asset_id,
                    g.field_name,
                    g.resolved_value,
                    r.response_value
                FROM migration.collection_data_gaps g
                LEFT JOIN migration.collection_questionnaire_responses r ON r.gap_id = g.id
                WHERE g.collection_flow_id = p_collection_flow_id
                AND g.resolution_status = 'resolved'
                AND (g.resolved_value IS NOT NULL OR r.response_value IS NOT NULL)
            )
            UPDATE migration.assets a
            SET
                operating_system = COALESCE(
                    (SELECT resolved_value FROM resolved_data WHERE asset_id = a.id AND field_name = 'operating_system'),
                    a.operating_system
                ),
                business_criticality = COALESCE(
                    (SELECT resolved_value FROM resolved_data WHERE asset_id = a.id AND field_name = 'business_criticality'),
                    a.business_criticality
                ),
                application_type = COALESCE(
                    (SELECT resolved_value FROM resolved_data WHERE asset_id = a.id AND field_name = 'application_type'),
                    a.application_type
                ),
                -- Add more field mappings here
                updated_at = NOW()
            WHERE a.id IN (SELECT DISTINCT asset_id FROM resolved_data WHERE asset_id IS NOT NULL);

            GET DIAGNOSTICS v_assets_updated = ROW_COUNT;
            v_fields_updated := (SELECT COUNT(*) FROM resolved_data);

            RETURN QUERY SELECT v_assets_updated, v_fields_updated;
        END;
        $$ LANGUAGE plpgsql;
    """)

def downgrade():
    op.execute("""
        DROP FUNCTION IF EXISTS migration.propagate_gaps_to_assets(UUID);
    """)
```

---

## 9. Verification SQL Scripts

### 9.1 Check Data Propagation Status

```sql
-- Verify responses exist
SELECT
    COUNT(*) AS total_responses,
    COUNT(DISTINCT asset_id) AS unique_assets,
    COUNT(DISTINCT collection_flow_id) AS unique_flows
FROM migration.collection_questionnaire_responses
WHERE created_at > NOW() - INTERVAL '7 days';

-- Verify gaps are marked resolved but have no value
SELECT
    COUNT(*) AS total_resolved_gaps,
    COUNT(CASE WHEN resolved_value IS NULL OR resolved_value = '' THEN 1 END) AS empty_resolved_values,
    COUNT(CASE WHEN resolved_value IS NOT NULL AND resolved_value != '' THEN 1 END) AS populated_resolved_values
FROM migration.collection_data_gaps
WHERE resolution_status = 'resolved';

-- Check Asset fields that should be updated
SELECT
    a.id,
    a.name,
    a.operating_system,
    a.business_criticality,
    a.application_type,
    a.assessment_readiness_score,
    COUNT(g.id) AS total_gaps,
    COUNT(CASE WHEN g.resolution_status = 'resolved' THEN 1 END) AS resolved_gaps
FROM migration.assets a
LEFT JOIN migration.collection_data_gaps g ON g.asset_id = a.id
WHERE a.engagement_id = '<your-engagement-id>'
GROUP BY a.id, a.name, a.operating_system, a.business_criticality, a.application_type, a.assessment_readiness_score
HAVING COUNT(CASE WHEN g.resolution_status = 'resolved' THEN 1 END) > 0
AND a.operating_system IS NULL;  -- Should be updated but isn't
```

### 9.2 Manual Data Repair Script

```sql
-- TEMPORARY FIX: Manually populate resolved_value from responses
UPDATE migration.collection_data_gaps g
SET
    resolved_value = r.response_value::text,
    updated_at = NOW()
FROM migration.collection_questionnaire_responses r
WHERE r.gap_id = g.id
AND g.resolution_status = 'resolved'
AND (g.resolved_value IS NULL OR g.resolved_value = '')
AND r.response_value IS NOT NULL;

-- Verify update
SELECT
    COUNT(*) AS gaps_updated
FROM migration.collection_data_gaps
WHERE resolution_status = 'resolved'
AND resolved_value IS NOT NULL
AND resolved_value != '';
```

---

## 10. Action Items

### 10.1 Immediate (Code Fix)

1. **Update `resolve_data_gaps()` function** to populate `gap.resolved_value`
   - File: `backend/app/api/v1/endpoints/collection_crud_helpers.py:296`
   - Add: `gap.resolved_value = json.dumps(value.get("value", value)) if isinstance(value, dict) else str(value)`
   - Test: Submit questionnaire response and verify `resolved_value` is populated

2. **Verify field name mapping** in `asset_handlers.py`
   - Ensure whitelist includes all questionnaire field IDs
   - Handle composite field IDs (`{asset_id}__{field_name}`)
   - Strip `custom_attributes.` prefix

3. **Add logging** to trace data propagation
   - Log when `resolved_value` is set
   - Log when Asset fields are updated
   - Log readiness score changes

### 10.2 Short-Term (Database Enhancement)

4. **Create database trigger** (`093_add_gap_resolution_trigger.py`)
   - Auto-populate `resolved_value` when response is inserted
   - Ensures data consistency even if application code fails

5. **Create stored procedure** (`094_add_asset_update_procedure.py`)
   - Centralize asset update logic in database
   - Allow manual invocation for data repairs

### 10.3 Long-Term (Architecture Improvement)

6. **Add database constraints**
   - NOT NULL constraint on `resolved_value` when `resolution_status = 'resolved'`
   - CHECK constraint: `(resolution_status = 'resolved' AND resolved_value IS NOT NULL) OR resolution_status != 'resolved'`

7. **Create materialized view** for gap analysis
   - Pre-compute completeness scores
   - Refresh after questionnaire submissions
   - Improve dashboard performance

8. **Add audit trail**
   - Track when Asset fields are updated
   - Store old/new values for rollback capability
   - Link updates to questionnaire responses

---

## 11. Conclusion

The intelligent gap detection system has a **complete data propagation architecture** in place, but the critical link between `response_value` and `resolved_value` is missing. This is a **simple code fix** that will restore the entire data flow.

**Impact of Fix:**
- ✅ Asset fields will be updated with collected data
- ✅ Readiness scores will improve after questionnaire submission
- ✅ Gap analysis will show correct completeness percentages
- ✅ Users will see immediate feedback on data collection progress

**Estimated Effort:**
- Code fix: 2 hours (including testing)
- Database trigger: 4 hours (migration + testing)
- Stored procedure: 6 hours (comprehensive field mapping)
- Data repair: 1 hour (run manual SQL script)

**Total:** 13 hours to full resolution

---

## Appendix: Database Schema DDL

### A.1 collection_questionnaire_responses

```sql
CREATE TABLE migration.collection_questionnaire_responses (
    id UUID PRIMARY KEY,
    collection_flow_id UUID NOT NULL REFERENCES migration.collection_flows(id) ON DELETE CASCADE,
    gap_id UUID REFERENCES migration.collection_data_gaps(id) ON DELETE SET NULL,
    asset_id UUID REFERENCES migration.assets(id) ON DELETE CASCADE,
    questionnaire_type VARCHAR(50) NOT NULL,
    question_category VARCHAR(50) NOT NULL,
    question_id VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    response_type VARCHAR(50) NOT NULL,
    response_value JSONB,  -- ACTUAL DATA HERE
    confidence_score DOUBLE PRECISION,
    validation_status VARCHAR(20) DEFAULT 'pending',
    responded_by UUID REFERENCES migration.users(id),
    responded_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### A.2 collection_data_gaps

```sql
CREATE TABLE migration.collection_data_gaps (
    id UUID PRIMARY KEY,
    collection_flow_id UUID NOT NULL REFERENCES migration.collection_flows(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL,
    gap_type VARCHAR(100) NOT NULL,
    gap_category VARCHAR(50) NOT NULL,
    field_name VARCHAR(255) NOT NULL,  -- Asset column name
    description TEXT,
    impact_on_sixr VARCHAR(20) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    suggested_resolution TEXT,
    resolution_status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'resolved'
    resolved_value TEXT,  -- SHOULD CONTAIN RESPONSE DATA (currently empty!)
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(50),
    confidence_score DOUBLE PRECISION,
    ai_suggestions JSONB,
    resolution_method VARCHAR(50),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gaps_dedup UNIQUE (collection_flow_id, field_name, gap_type, asset_id)
);
```

### A.3 assets (abbreviated)

```sql
CREATE TABLE migration.assets (
    id UUID PRIMARY KEY,
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    operating_system VARCHAR(100),  -- Should be updated from gaps
    business_criticality VARCHAR(20),  -- Should be updated from gaps
    application_type VARCHAR(20),  -- Should be updated from gaps
    assessment_readiness_score DOUBLE PRECISION,  -- Should be recalculated
    completeness_score DOUBLE PRECISION,  -- Should be recalculated
    technical_details JSONB,  -- Enrichment from responses
    custom_attributes JSONB,  -- Enrichment from responses
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

---

**End of Analysis**
