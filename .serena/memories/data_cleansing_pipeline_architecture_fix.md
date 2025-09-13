# Data Cleansing Pipeline Architecture Fix

## Date: 2025-09-13

## Insight 1: Persistent Agent vs Crew-Based Pattern
**Problem**: Data cleansing using crew-based patterns with JSON parsing causing failures
**Solution**: Use TenantScopedAgentPool with classmethod API
**Code**:
```python
# WRONG - Crew-based pattern
from app.services.agentic_intelligence.agentic_asset_enrichment import enrich_assets
enriched = await enrich_assets_with_agentic_intelligence(...)

# CORRECT - Persistent agent pattern
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from app.core.context import RequestContext

request_context = RequestContext(
    client_account_id=self.state.client_account_id,
    engagement_id=self.state.engagement_id,
    flow_id=self.state.flow_id
)

agent = await TenantScopedAgentPool.get_agent(
    context=request_context,
    agent_type="data_cleansing",
    service_registry=service_registry
)
cleaned_data = await agent.process(raw_records)
```
**Usage**: Always use persistent agents for multi-tenant data processing

## Insight 2: Cleansed Data Storage Pattern
**Problem**: raw_import_records.cleansed_data not populated due to ID mapping issue
**Solution**: Map raw_import_record_id to id before storage
**Code**:
```python
# Fix ID mapping before storage
for record in cleaned_data:
    if 'raw_import_record_id' in record and 'id' not in record:
        record['id'] = record['raw_import_record_id']

# Await the update (no fire-and-forget)
await storage_manager.update_raw_records_with_cleansed_data(
    data_import_id=data_import_id,
    cleansed_data=cleaned_data,
    validation_results=validation_results
)
await db.commit()
```
**Usage**: Always fix ID mapping when updating raw_import_records

## Insight 3: No Raw Data Fallback Policy
**Problem**: Asset creation using raw data bypasses data quality checks
**Solution**: Require cleansed_data, return 422 if missing
**Code**:
```python
# Query ONLY cleansed data
result = await self.db_session.execute(
    select(RawImportRecord).where(
        RawImportRecord.data_import_id == data_import_id,
        RawImportRecord.cleansed_data.isnot(None),  # REQUIRE
        RawImportRecord.client_account_id == self.context.client_account_id,
        RawImportRecord.engagement_id == self.context.engagement_id
    )
)
records = result.scalars().all()

if len(records) == 0:
    return {
        "status": "error",
        "error_code": "CLEANSING_REQUIRED",
        "message": "No cleansed data available. Run data cleansing first.",
        "counts": {"raw": raw_count, "cleansed": 0}
    }
```
**Usage**: Never fallback to raw data in asset creation pipeline

## Insight 4: Multi-Tenant Query Scoping
**Problem**: Queries missing tenant isolation filters
**Solution**: Always include client_account_id and engagement_id
**Code**:
```python
# EVERY query must have tenant scoping
.where(
    Model.data_import_id == data_import_id,
    Model.client_account_id == context.client_account_id,  # REQUIRED
    Model.engagement_id == context.engagement_id  # REQUIRED
)
```
**Usage**: Add to every database query without exception

## Insight 5: Session Management Pattern
**Problem**: Creating unnecessary database sessions
**Solution**: Reuse existing session when available
**Code**:
```python
# Check for existing session first
if hasattr(self, 'db_session') and self.db_session:
    session = self.db_session
    should_commit = False  # Don't commit external session
else:
    from app.core.database import AsyncSessionLocal
    session = AsyncSessionLocal()
    should_commit = True  # Commit our own session

try:
    # ... do work ...
    if should_commit:
        await session.commit()
finally:
    if should_commit and session:
        await session.close()
```
**Usage**: Always check for existing session before creating new one
