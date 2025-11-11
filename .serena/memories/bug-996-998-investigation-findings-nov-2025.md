# Bug #996-#998 Investigation Findings (November 2025)

## Executive Summary

Investigation of questionnaire generation failures revealed **3 critical bugs** beyond the originally reported issues. While GPT-5's serialization fixes (#996a, #996b) are deployed, the questionnaire generation is still failing due to **background task errors** and **data persistence issues**.

## Critical Findings

### 🐛 Bug #1: Gap Data Persistence & Duplication (NEW - User Reported)

**Symptom**: Selecting Consul asset shows 22 gaps initially, but re-selecting the same asset shows only 4 gaps.

**Root Cause**:
- Database contains **158 duplicate gap records** for single Consul asset (`1f9e22f8-7d91-4c9b-bb25-b725e9913985`)
- Gaps are **flow-scoped** (linked to `collection_flow_id`) instead of **asset-scoped**
- Each new flow creates duplicate gap records (22 gaps × 7 flows = 154+ records)
- Gap analysis queries filter by `collection_flow_id`, showing different counts per flow

**Database Evidence**:
```sql
-- 158 total gaps for one asset
SELECT COUNT(*) FROM migration.collection_data_gaps
WHERE asset_id = '1f9e22f8-7d91-4c9b-bb25-b725e9913985';
-- Result: 158

-- Distributed across flows
SELECT collection_flow_id, COUNT(*)
FROM migration.collection_data_gaps
WHERE asset_id = '1f9e22f8-7d91-4c9b-bb25-b725e9913985'
GROUP BY collection_flow_id;
-- Shows 22 gaps per flow
```

**Impact**:
- Data duplication and storage waste
- Inconsistent gap counts confuse users
- Violates ADR-034 asset-centric data scoping principle

**Fix Required**: Make gap analysis **asset-scoped** not **flow-scoped**

---

### 🐛 Bug #2: Questionnaire Generation Silent Failure (CRITICAL)

**Symptom**: 14 flows stuck in `questionnaire_generation` phase at 0% progress, showing fallback form.

**Root Cause**:
- **Only 3 questionnaires exist** in database (all with `completion_status = 'failed'`)
- **14 flows have NO questionnaire records** despite being in questionnaire_generation phase
- Background tasks (`_background_generate`) are failing silently
- No error status updates to flows when background tasks fail
- Frontend shows 2-question fallback form instead of 22-question intelligent form

**Database Evidence**:
```sql
-- Only 3 questionnaires, all failed
SELECT COUNT(*), completion_status
FROM migration.adaptive_questionnaires
GROUP BY completion_status;
-- Result: 3 total, 0 ready, 0 pending, 3 failed

-- Flow 2d016a8b has NO questionnaire
SELECT aq.*
FROM migration.collection_flows cf
LEFT JOIN migration.adaptive_questionnaires aq ON aq.collection_flow_id = cf.id
WHERE cf.flow_id = '2d016a8b-15b2-421d-bc58-6196b967bf2f';
-- Result: NULL (no questionnaire linked)
```

**Frontend Evidence** (Playwright observation):
- URL: `http://localhost:8081/collection/adaptive-forms?flowId=2d016a8b-15b2-421d-bc58-6196b967bf2f`
- Error notification: "Questionnaire generation failed - please try again"
- Fallback form with only 2 questions: "Application Name" and "Application Type"
- Console log: `Questionnaire completion status: failed`

**Impact**:
- Complete breakdown of intelligent questionnaire generation
- Users stuck with basic 2-question fallback form
- 14 flows abandoned in running state (data integrity issue)
- No way for users to retry or recover

**Fix Required**:
1. Investigate why background tasks fail (check exception logs)
2. Add error handling to update flow status when tasks fail
3. Implement retry mechanism for failed questionnaires
4. Surface errors to users instead of silent failures

---

### 🐛 Bug #3: Flow-Questionnaire Linkage Integrity (CRITICAL)

**Symptom**: Flows exist without questionnaires, breaking referential integrity.

**Root Cause**:
- ADR-034 specifies **asset-centric questionnaires** with unique constraint on `(engagement_id, asset_id)`
- But creation code in `commands.py:82-165` tries to link questionnaires to `collection_flow_id`
- Race conditions during INSERT cause unique constraint violations (lines 144-165 handle this)
- Some questionnaires created but never committed to database
- No rollback/cleanup when questionnaire creation fails

**Code Location**:
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py:29-220`
- Lines 82-98: Get-or-create logic checks for existing questionnaire by `(engagement_id, asset_id)`
- Lines 127-165: Race condition handling with unique constraint violations

**Impact**:
- Orphaned flows with no questionnaires
- Violated foreign key relationships
- Data inconsistency between flows and questionnaires

**Fix Required**:
- Ensure transactional integrity between flow creation and questionnaire creation
- Add cleanup logic to mark flows as `failed` if questionnaire creation fails
- Consider decoupling questionnaire creation from flow progression

---

## Fixes Already Deployed ✅

### Bug #996a: Boolean Evaluation in data_extraction.py
**Status**: ✅ DEPLOYED and VERIFIED in container

**Location**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/data_extraction.py:197-203`

**Fix Applied**:
```python
# BEFORE (BUGGY)
data_to_process = questionnaires_data or sections_data or _extract_from_agent_output(agent_result)

# AFTER (FIXED)
data_to_process = (
    questionnaires_data if questionnaires_data else
    sections_data if sections_data else
    _extract_from_agent_output(agent_result)
)
```

**Verification**: `docker exec migration_backend grep -A 5 "data_to_process =" ...` confirmed fix present.

---

### Bug #996b: JSON Truncation from LLM Output (GPT-5 Fix)
**Status**: ✅ DEPLOYED and VERIFIED in container

**Location**: `backend/app/services/persistent_agents/config/agent_wrapper.py:140-172`

**Fix Applied by GPT-5**: Hardened `_ensure_agent_output_dict` function to:
1. Parse `raw_text` strings containing JSON
2. Replace `agent_output["raw_text"]` with parsed dictionary
3. Eliminate multiple JSON ↔ string conversions causing truncation

**Code**:
```python
def _ensure_agent_output_dict(normalized: Any) -> Any:
    if isinstance(normalized, dict):
        agent_output_value = normalized.get("agent_output")
        # ... parsing logic ...
        elif (
            isinstance(agent_output_value, dict)
            and "raw_text" in agent_output_value
            and isinstance(agent_output_value["raw_text"], str)
        ):
            parsed_agent_output = _parse_string_output(agent_output_value["raw_text"])
            if isinstance(parsed_agent_output, dict):
                normalized["agent_output"] = parsed_agent_output  # ✅ Replaces raw_text
```

**Verification**: `docker exec migration_backend python -c "import inspect; ..."` confirmed fix present.

**Impact**: Eliminates 16,233-character JSON truncation issue identified in logs.

---

## Investigation Methodology

### Tools Used
1. **Playwright MCP Server**: Browser automation to observe user-facing behavior
2. **PostgreSQL Database Queries**: Validate data persistence and integrity
3. **Docker Backend Logs**: Trace background task execution
4. **Serena Memory Search**: Review architectural decisions (ADR-034)

### Key Investigation Steps
1. Logged into application at `http://localhost:8081`
2. Navigated to Collection → Adaptive Forms
3. Observed 14 incomplete flows stuck in `questionnaire_generation` phase
4. Selected flow `2d016a8b-15b2-421d-bc58-6196b967bf2f` and clicked "Continue Flow"
5. Observed fallback form with error: "Questionnaire generation failed"
6. Queried database to confirm NO questionnaire record exists for this flow
7. Analyzed gap data duplication across flows for Consul asset

### Key Observations
- **Frontend**: Shows fallback 2-question form with error notification
- **Database**: Only 3 questionnaires (all failed), 14 flows with no questionnaires
- **Logs**: No recent completion messages for questionnaire generation
- **Gap Data**: 158 duplicate records for single asset across 7+ flows

---

## Next Steps (For Fresh Session)

### Immediate Actions
1. **Check Backend Logs for Actual Error**:
   ```bash
   docker logs migration_backend --since 30m 2>&1 | grep -A 20 "Background generation failed"
   ```
   Look for exception stack traces from `_background_generate` function

2. **Verify Serialization Fix is Working**:
   - Check if `_ensure_agent_output_dict` successfully parses `raw_text`
   - Confirm no JSON truncation at 16,233 characters

3. **Database Cleanup**:
   ```sql
   -- Mark abandoned flows as failed
   UPDATE migration.collection_flows
   SET status = 'failed', current_phase = 'failed'
   WHERE current_phase = 'questionnaire_generation'
   AND id NOT IN (SELECT DISTINCT collection_flow_id FROM migration.adaptive_questionnaires);
   ```

### Architectural Fixes Required

#### Fix #1: Make Gap Analysis Asset-Scoped
**File**: `backend/app/services/collection/gap_analysis/gap_persistence.py`

**Change**:
- Remove or deprecate `collection_flow_id` from gap records
- Query gaps by `(engagement_id, asset_id)` instead of `collection_flow_id`
- Implement gap deduplication logic similar to ADR-034 questionnaires

#### Fix #2: Surface Background Task Errors
**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py:334-465`

**Change** in `_background_generate`:
```python
except Exception as e:
    # BEFORE: Only logs error
    logger.error(f"Background generation failed: {e}")

    # AFTER: Update flow status
    await db.execute(
        update(CollectionFlow)
        .where(CollectionFlow.flow_id == UUID(flow_id))
        .values(status='failed', error_message=str(e))
    )
```

#### Fix #3: Add Retry Mechanism
**Frontend**: Add "Retry Generation" button when questionnaire status is `failed`

**Backend**: Add endpoint `/api/v1/collection/flows/{flow_id}/retry-questionnaire`

---

## Files Modified During Investigation

None - investigation only, no code changes made.

---

## Related Documentation
- **ADR-034**: Asset-centric questionnaire deduplication (`docs/adr/034-asset-centric-questionnaire-deduplication.md`)
- **Bug Fix Commit by GPT-5**: Hardened AgentWrapper normalization (mentioned in user message)

---

## Test Flows for Validation
- Flow `2d016a8b-15b2-421d-bc58-6196b967bf2f` - No questionnaire, shows fallback form
- Flow `851b213a-579c-4000-a1c7-46cac6eb77e8` - Has questionnaire `c395a104-da1f-4a85-8a40-7ff37e1efbfc`
- Asset `1f9e22f8-7d91-4c9b-bb25-b725e9913985` (Consul) - 158 duplicate gap records

---

## Playwright Test Spec
Created: `tests/e2e/questionnaire-upsert-fix-980.spec.ts`

**Purpose**: Validate questionnaire persistence and form submission loop fix

**Not yet executed** - awaiting fixes to complete before running E2E test.
