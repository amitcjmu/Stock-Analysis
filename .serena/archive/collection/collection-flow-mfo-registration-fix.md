# Collection Flow MFO Registration - Bridge Pattern Fix

## Problem: Direct Model Instantiation Bypasses MFO

**Issue**: Collection flows created from discovery weren't registered in Master Flow Orchestrator

**Root Cause**: `discovery_collection_bridge.py` created flows using direct SQLAlchemy model instantiation instead of repository pattern

## Architecture: ADR-006 MFO Pattern

**Requirement**: ALL flows MUST register with `crewai_flow_state_extensions` table via repository

**Anti-Pattern** (❌):
```python
# Direct model instantiation - bypasses MFO registration
collection_flow = CollectionFlow(
    flow_name=flow_name,
    automation_tier=tier,
    # ... fields ...
)
self.db.add(collection_flow)
await self.db.commit()
# ❌ No MFO entry created
```

**Correct Pattern** (✅):
```python
# Use repository - ensures MFO registration
from app.repositories.collection_flow_repository import CollectionFlowRepository

collection_repo = CollectionFlowRepository(
    db=self.db,
    client_account_id=self.context.client_account_id,
    engagement_id=self.context.engagement_id,
)

collection_flow = await collection_repo.create(
    flow_name=flow_name,
    automation_tier=tier,
    # ... other params ...
)
# ✅ Automatically registers with MFO
```

## Solution Applied

**File**: `backend/app/services/integration/discovery_collection_bridge.py:125-174`

**Before**:
```python
async def create_collection_flow(
    self,
    discovery_flow_id: UUID,
    applications: List[Dict[str, Any]],
    automation_tier: str,
    start_phase: str = "gap_analysis",
) -> CollectionFlow:
    """Create Collection flow with Discovery context."""

    # ❌ Direct instantiation
    collection_flow = CollectionFlow(
        client_account_id=self.context.client_account_id,
        engagement_id=self.context.engagement_id,
        flow_name=f"Collection from Discovery - {len(applications)} apps",
        # ... fields ...
    )

    self.db.add(collection_flow)
    await self.db.commit()
    await self.db.refresh(collection_flow)

    return collection_flow
```

**After**:
```python
async def create_collection_flow(
    self,
    discovery_flow_id: UUID,
    applications: List[Dict[str, Any]],
    automation_tier: str,
    start_phase: str = "gap_analysis",
) -> CollectionFlow:
    """
    Create Collection flow with Discovery context.
    Uses CollectionFlowRepository to ensure MFO registration (ADR-006).
    """
    from app.repositories.collection_flow_repository import CollectionFlowRepository
    from uuid import uuid4

    flow_id = uuid4()

    # ✅ Use repository pattern to ensure MFO registration
    collection_repo = CollectionFlowRepository(
        db=self.db,
        client_account_id=self.context.client_account_id,
        engagement_id=self.context.engagement_id,
    )

    # Create flow with MFO registration
    collection_flow = await collection_repo.create(
        flow_name=f"Collection from Discovery - {len(applications)} apps",
        automation_tier=automation_tier,
        flow_metadata={
            "discovery_flow_id": str(discovery_flow_id),
            "created_from": "discovery_bridge",
            "application_count": len(applications),
        },
        collection_config={
            "discovery_flow_id": str(discovery_flow_id),
            "application_count": len(applications),
            "start_phase": start_phase,
            "applications": applications,
        },
        flow_id=flow_id,
        user_id=self.context.user_id,
        discovery_flow_id=discovery_flow_id,
        current_phase=start_phase,
    )

    logger.info(
        f"✅ Collection flow {collection_flow.id} registered with MFO "
        f"(master_flow_id: {collection_flow.flow_id})"
    )

    return collection_flow
```

## Bridge Service Pattern

When creating flows in bridge/integration services:
1. **NEVER** use direct model instantiation
2. **ALWAYS** import and use the flow-specific repository
3. **VERIFY** MFO registration in logs: `✅ Collection flow {id} registered with MFO`

## Files Using Bridge Pattern

Check these for proper MFO registration:
- `backend/app/services/integration/discovery_collection_bridge.py` - Discovery → Collection
- `backend/app/services/collection_transition_service.py` - Collection → Assessment
- Any future flow transition services

## Verification

After creating a flow via bridge service:
```sql
-- Check MFO registration
SELECT flow_id, flow_type, flow_status
FROM migration.crewai_flow_state_extensions
WHERE flow_type = 'collection'
ORDER BY created_at DESC LIMIT 1;

-- Should return the newly created flow
```

## Usage

When implementing new flow transitions:
1. Import target flow repository
2. Call `repository.create()` with all required fields
3. Log MFO registration confirmation
4. Verify both child flow table AND MFO table have entries
