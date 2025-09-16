# Persistent Agent Migration for Discovery Flow Data Cleansing

## Problem Solved
Migrated from inefficient crew-based data cleansing to persistent multi-tenant agents, fixing asset creation failures due to missing cleansed data and implementing proper 422 HTTP error handling.

## Key Technical Changes

### 1. DataCleansingExecutor Rewrite
**Problem**: Legacy crew instantiation causing performance issues and API confusion
**Solution**: Use TenantScopedAgentPool with persistent agents

```python
# NEW: Persistent agent approach
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

cleansing_agent = await TenantScopedAgentPool.get_agent(
    context=request_context,
    agent_type="data_cleansing",
    service_registry=service_registry
)
cleaned_data = await cleansing_agent.process(raw_import_records)
```

### 2. API Error Handling for Missing Cleansed Data
**Problem**: Asset inventory phase executed with raw data, creating generic asset names
**Solution**: Return 422 HTTP status when cleansed data required

```python
# In flow execution service
if result.get("error_code") == "CLEANSING_REQUIRED":
    return {
        "success": False,
        "error_code": "CLEANSING_REQUIRED",
        "message": result.get("message"),
        "http_status": 422,
        "requires_cleansing": True
    }

# In API endpoint
if result.get("error_code") == "CLEANSING_REQUIRED":
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "CLEANSING_REQUIRED",
            "message": result.get("message"),
            "counts": result.get("counts", {})
        }
    )
```

### 3. Session Management Pattern
**Problem**: Transaction boundary confusion between executor and storage manager
**Solution**: Conditional commit based on session ownership

```python
# In DataCleansingExecutor
if hasattr(self, 'db_session') and self.db_session:
    db = self.db_session
    should_commit = False  # Parent manages transaction
else:
    db = AsyncSessionLocal()
    should_commit = True   # We own the transaction

# After storage operations
if should_commit:
    await db.commit()
```

### 4. Agent Configuration Standardization
**Problem**: Inconsistent agent_type naming (`asset_inventory_agent` vs `asset_inventory`)
**Solution**: Use consistent snake_case without suffix

```python
# BEFORE: Mixed naming
agent_type="asset_inventory_agent"

# AFTER: Standardized
agent_type="asset_inventory"
```

## Legacy Code Removal

### Complete DataCleansingCrew Elimination
**Files Removed**:
- `backend/app/services/crewai_flows/crews/data_cleansing_crew.py`
- `backend/app/services/crewai_flows/handlers/crew_execution/data_cleansing.py`

**Import Cleanup**:
- Removed from `__init__.py` exports
- Updated initialization_handler.py crew references
- Cleaned up factory registrations

## Critical Error Patterns Fixed

### 1. ID Mapping in Cleansed Data
**Problem**: Records missing `id` field, only had `raw_import_record_id`
```python
# Fix ID mapping before storage
for record in cleaned_data:
    if 'raw_import_record_id' in record and 'id' not in record:
        record['id'] = record['raw_import_record_id']
```

### 2. Proper Storage Manager Usage
**Storage manager uses flush(), executor handles commit**:
```python
# StorageManager - flushes but doesn't commit
await self.db.flush()
return records_updated

# Executor - commits when appropriate
await storage_manager.update_raw_records_with_cleansed_data(...)
if should_commit:
    await db.commit()
```

## Usage Guidelines

**When to Apply**:
- Migrating from crew-based to persistent agent patterns
- Implementing proper HTTP error codes for missing dependencies
- Managing database transactions across service boundaries

**Key Benefits**:
- Better performance (eliminates crew instantiation overhead)
- Proper tenant isolation via agent pools
- Clear error handling for missing data dependencies
- Clean transaction boundary management

**Architecture Compliance**:
- Follows ADR-015 (Persistent Multi-Tenant Agent Architecture)
- Maintains seven-layer enterprise architecture
- Preserves multi-tenant data isolation
