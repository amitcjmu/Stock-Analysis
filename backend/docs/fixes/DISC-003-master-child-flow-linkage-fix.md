# DISC-003: Master-Child Flow Linkage Fix

## Issue Summary
86% of discovery flows (19 out of 22) had NULL master_flow_id, breaking the flow hierarchy and preventing proper flow management through the Master Flow Orchestrator.

## Root Cause
Historical discovery flows were created before the Master Flow Orchestrator was implemented, resulting in orphaned flows without proper parent linkage.

## Fix Implementation

### 1. Migration Script Created
Created `/backend/migrate_legacy_flow.py` to:
- Identify orphaned discovery flows (master_flow_id = NULL)
- Create matching master flow records in `crewai_flow_state_extensions`
- Link discovery flows to their master flows
- Handle status mapping (e.g., 'deleted' → 'cancelled')

### 2. Code Review Findings
The current flow creation process (`FlowExecutionEngine._create_discovery_flow_record`) already properly sets master_flow_id:
```python
discovery_flow_record = DiscoveryFlow(
    flow_id=flow_id,
    master_flow_id=flow_id,  # Properly linked
    # ... other fields
)
```

### 3. Migration Results
- **Before**: 19/22 flows orphaned (86.4%)
- **After**: 0/22 flows orphaned (0%)
- **Actions**: Created 10 new master flows, linked 19 discovery flows
- **Status**: 100% of discovery flows now have proper master flow linkage

## Verification
```sql
-- Check linkage status
SELECT COUNT(*) as total_flows,
       COUNT(master_flow_id) as linked_flows,
       ROUND(100.0 * COUNT(master_flow_id) / COUNT(*), 1) as linked_percentage
FROM discovery_flows;

-- Result: 100% linked
```

## Impact
- ✅ All discovery flows now properly managed by Master Flow Orchestrator
- ✅ Flow deletion cascade now works correctly
- ✅ Flow status tracking unified across all flow types
- ✅ Enables proper flow hierarchy visualization

## Future Prevention
The current implementation ensures all new discovery flows are created with proper master_flow_id linkage through the Master Flow Orchestrator pattern. No code changes needed - the fix was purely data migration.

## Dependencies Resolved
This fix was foundational and unblocks:
- DISC-001: Asset discovery issues (Agent-1)
- DISC-002: Field mapping problems (Agent-2)
- All other discovery flow management operations
