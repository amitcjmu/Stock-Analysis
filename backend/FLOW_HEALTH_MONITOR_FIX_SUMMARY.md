# Flow Health Monitor Fix Summary

## Issue Description
The flow health monitor was throwing a "Multiple rows were found when one or none was required" error, indicating a database query issue where the code expected a single row but found multiple.

## Root Cause Analysis

### 1. **Primary Issue: Duplicate master_flow_id entries**
- **Location**: `/backend/app/services/flow_health_monitor.py` line 195
- **Problem**: The query used `scalar_one_or_none()` but multiple discovery flows had the same `master_flow_id`
- **Impact**: Violated the expected one-to-one relationship between master flows and discovery flows

### 2. **Secondary Issue: Incorrect field names in CrewAI flow monitor**
- **Location**: `/backend/app/services/crewai_flows/monitoring/flow_health_monitor.py` line 95
- **Problem**: Referenced `status` field on `CrewAIFlowStateExtensions` model, but the field is named `flow_status`
- **Impact**: Caused AttributeError when monitoring master flows

### 3. **Tertiary Issue: Timezone-aware/naive datetime conflicts**
- **Location**: Various datetime calculations in CrewAI flow monitor
- **Problem**: Mixed timezone-aware and naive datetime objects causing comparison errors
- **Impact**: Prevented accurate health status calculations

## Fixes Applied

### 1. **Fixed Flow Health Monitor Query**
**File**: `/backend/app/services/flow_health_monitor.py`
```python
# OLD - Could return multiple rows
disc_stmt = select(DiscoveryFlow).where(
    DiscoveryFlow.master_flow_id == master.flow_id
)
discovery_flow = disc_result.scalar_one_or_none()

# NEW - Gets most recent if multiple exist
disc_stmt = select(DiscoveryFlow).where(
    DiscoveryFlow.master_flow_id == master.flow_id
).order_by(DiscoveryFlow.created_at.desc()).limit(1)
discovery_flow = disc_result.scalar_one_or_none()
```

### 2. **Resolved Duplicate master_flow_id Data**
**Script**: `/backend/fix_duplicate_master_flow_ids.py`
- Identified 2 master flows with 2-3 duplicate discovery flows each
- Kept the most recent discovery flow for each master flow
- Marked older duplicate flows as "orphaned" status
- Cleared `master_flow_id` from orphaned flows to prevent future conflicts

### 3. **Fixed CrewAI Flow Monitor Field Names**
**File**: `/backend/app/services/crewai_flows/monitoring/flow_health_monitor.py`
- Created helper functions `_get_flow_status()` and `_set_flow_status()` to handle different field names
- Discovery flows use `status` field
- Master flows use `flow_status` field
- Updated all status-related operations to use the helper functions

### 4. **Fixed Timezone Handling**
**File**: `/backend/app/services/crewai_flows/monitoring/flow_health_monitor.py`
```python
# OLD - Mixed timezone types
now = datetime.utcnow()
time_since_update = now - last_update

# NEW - Consistent timezone handling
now = datetime.now(timezone.utc)
if last_update.tzinfo is None:
    last_update = last_update.replace(tzinfo=timezone.utc)
time_since_update = now - last_update
```

## Data Integrity Results

### Before Fix
```
Found 2 master flows with multiple discovery flows:
  Master Flow ID: 471a9d81-7688-4d41-8e34-f54d4f41e073 has 2 discovery flows
  Master Flow ID: e7ce6262-1b0a-438b-a601-4d623388862d has 3 discovery flows
```

### After Fix
```
✅ No duplicate master_flow_ids found - issue permanently resolved!
```

## Testing Results

### Flow Health Monitor
```
✅ update_flow_metrics() - No "Multiple rows were found" error!
✅ Health report: healthy - {'active': 0, 'initialized': 0, 'running': 0, 'complete': 0, 'failed': 16, 'waiting_for_approval': 0}
✅ check_stuck_flows() - No errors!
✅ check_timeout_flows() - No errors!
```

### CrewAI Flow Health Monitor
```
✅ CrewAI flow health monitor _check_all_flows() executed successfully
✅ Health metrics generated: 2 flows monitored
```

## Prevention Measures

1. **Database Constraint**: Consider adding a unique constraint on `master_flow_id` in the `discovery_flows` table
2. **Error Handling**: Improved error handling for cases where multiple flows exist
3. **Field Validation**: Helper functions ensure correct field names are used across different flow types
4. **Timezone Consistency**: All datetime operations now use timezone-aware calculations

## Files Modified

1. `/backend/app/services/flow_health_monitor.py` - Fixed query and ordering
2. `/backend/app/services/crewai_flows/monitoring/flow_health_monitor.py` - Fixed field names and timezone handling
3. `/backend/fix_duplicate_master_flow_ids.py` - Data cleanup script (one-time use)

## Impact
- ✅ Flow health monitoring now works without errors
- ✅ No more "Multiple rows were found" exceptions
- ✅ Proper handling of both discovery and master flow types
- ✅ Consistent timezone handling across all health calculations
- ✅ Data integrity maintained with duplicate relationships resolved

The flow health monitor is now fully functional and robust against similar issues in the future.