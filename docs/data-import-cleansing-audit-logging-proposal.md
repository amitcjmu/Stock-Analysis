# CSV Data Cleansing Audit Logging - Implementation Proposal

## Summary

**Review Comment #3**: Backend Audit Trail Still Missing - Need to log CSV data cleansing events.

**User Requirement**: Keep it simple - just log "this field was cleansed of commas as part of data import" as a marker to go back and see what was done.

---

## Investigation Results

### ✅ Existing Audit Trail Infrastructure

1. **Audit Log Models**:
   - `AccessAuditLog` model exists in `backend/app/models/rbac/audit_models.py`
   - Has fields: `action_type`, `resource_type`, `resource_id`, `client_account_id`, `engagement_id`, `result`, `reason`, `details` (JSON), `ip_address`, `user_agent`

2. **Audit Logging Services**:
   - `AuditLoggingService` in `backend/app/services/collection_flow/audit_logging/logger.py` - Used for data export audit logs
   - `FlowAuditLogger` in `backend/app/services/flow_orchestration/audit_logger.py` - For flow operations

3. **Current Pattern**:
   - Audit logging happens **server-side** when operations occur
   - Example: `log_raw_data_export_audit()` in `backend/app/api/v1/endpoints/data_cleansing/audit_utils.py`
   - Logs are written from backend endpoints using audit services

### ❌ No Client-Side Initiated Audit Endpoint

- No simple POST endpoint like `/api/v1/audit/log` for client-side audit logging
- All audit logging is currently server-side when operations happen
- Existing `/api/v1/admin/audit-log` is GET-only (admin reading logs)

---

## Proposed Simple Implementation (Phase 1)

### Approach: Server-Side Logging When Import Received

Since the CSV data cleansing happens at the **frontend**, but the import happens at the **backend**, we can:

1. **Add `cleansing_stats` to `StoreImportRequest` schema** (already has structure ready)
2. **Log audit entry in backend** when `cleansing_stats` is present and rows were cleansed
3. **Use existing `AccessAuditLog` model** for simple, structured logging

### Implementation Details

#### Step 1: Update Schema (Simple)
```python
# backend/app/schemas/data_import_schemas.py

class CleansingStats(BaseModel):
    """Stats about CSV data cleansing performed"""
    total_rows: int
    rows_cleansed: int
    rows_skipped: int

class StoreImportRequest(BaseModel):
    # ... existing fields ...
    cleansing_stats: Optional[CleansingStats] = None  # Add this
```

#### Step 2: Add Audit Logging in Import Handler
```python
# backend/app/services/data_import/import_storage_handler.py

async def handle_import(...):
    # ... existing import logic ...
    
    # Simple audit logging for data cleansing
    if store_request.cleansing_stats and store_request.cleansing_stats.rows_cleansed > 0:
        await self._log_cleansing_audit(store_request.cleansing_stats, context, data_import.id)
    
    # ... continue import ...
```

#### Step 3: Simple Audit Log Helper
```python
async def _log_cleansing_audit(self, cleansing_stats, context, data_import_id):
    """Simple audit log for CSV data cleansing"""
    from app.models.rbac.audit_models import AccessAuditLog
    
    await self.db.add(AccessAuditLog(
        user_id=context.user_id,
        action_type="data_import_cleansing",
        resource_type="data_import",
        resource_id=str(data_import_id),
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        result="success",
        reason=f"CSV data cleansing: {cleansing_stats.rows_cleansed} row(s) had unquoted commas replaced with spaces for column alignment during data import",
        details={
            "total_rows": cleansing_stats.total_rows,
            "rows_cleansed": cleansing_stats.rows_cleansed,
            "rows_skipped": cleansing_stats.rows_skipped,
            "cleansing_type": "comma_replacement",
            "cleansing_reason": "column_alignment"
        },
        ip_address=context.ip_address,
        user_agent=context.user_agent
    ))
    await self.db.commit()
```

#### Step 4: Update Frontend to Send Cleansing Stats
```typescript
// src/pages/discovery/CMDBImport/hooks/useFileUpload.ts

// Already have cleansing_stats from parseCsvFile
const parseResult = await parseCsvFile(file);
const cleansing_stats = parseResult.cleansing_stats;

// Send to backend in store_import request
const response = await apiCall(`/data-import/store-import`, {
    // ... existing fields ...
    cleansing_stats: cleansing_stats ? {
        total_rows: cleansing_stats.total_rows,
        rows_cleansed: cleansing_stats.rows_cleansed,
        rows_skipped: cleansing_stats.rows_skipped
    } : undefined
});
```

---

## Benefits

✅ **Simple**: Minimal code changes, uses existing infrastructure
✅ **Non-invasive**: Doesn't break existing flows
✅ **Queryable**: Audit logs stored in `access_audit_log` table, can query by:
   - `action_type = 'data_import_cleansing'`
   - `resource_type = 'data_import'`
   - `client_account_id` / `engagement_id`
✅ **Complete context**: Includes user, IP, timestamp, details

---

## What Gets Logged

When CSV cleansing occurs, an audit log entry is created with:
- **Action**: `data_import_cleansing`
- **Reason**: "CSV data cleansing: X row(s) had unquoted commas replaced with spaces for column alignment during data import"
- **Details** (JSON):
  - `total_rows`: Total rows in CSV
  - `rows_cleansed`: Number of rows that were cleansed
  - `rows_skipped`: Number of rows skipped
  - `cleansing_type`: "comma_replacement"
  - `cleansing_reason`: "column_alignment"

---

## Example Query to Review Logs

```sql
SELECT 
    created_at,
    user_id,
    resource_id as data_import_id,
    reason,
    details->>'rows_cleansed' as rows_cleansed,
    details->>'total_rows' as total_rows
FROM migration.access_audit_log
WHERE action_type = 'data_import_cleansing'
  AND client_account_id = '<client_id>'
ORDER BY created_at DESC;
```

---

## Next Steps

1. **Approve this approach** - Simple server-side logging using existing infrastructure
2. **Implementation** - Add schema field, logging logic, and frontend update
3. **Testing** - Verify audit logs are created correctly
4. **Optional Phase 2** - If needed later, could add query endpoint for audit logs

---

## Files to Modify

1. `backend/app/schemas/data_import_schemas.py` - Add `CleansingStats` and field to `StoreImportRequest`
2. `backend/app/services/data_import/import_storage_handler.py` - Add audit logging call
3. `src/pages/discovery/CMDBImport/hooks/useFileUpload.ts` - Send `cleansing_stats` to backend

**Total estimated LOC**: ~50 lines

