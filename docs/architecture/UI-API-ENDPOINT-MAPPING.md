# UI API Endpoint Mapping & Data Sources

**Document Purpose**: Map all UI components to their API endpoints and data sources to prevent duplicate fixes across multiple endpoints.

**Last Updated**: 2025-10-16  
**Related**: ADR-027 (Universal FlowTypeConfig Pattern), Bug #557, #560, #578, #579

## Overview

The UI consumes multiple API endpoints that serve similar flow data but with different implementations. This document maps each UI component to its data source to ensure consistent fixes across all endpoints.

## Discovery Flow UI Components & API Endpoints

### 1. Discovery Overview Page (`/discovery/overview`)

**UI Component**: `src/pages/discovery/EnhancedDiscoveryDashboard/components/FlowsOverview.tsx`

**Primary API Endpoint**: 
```
GET /api/v1/unified-discovery/flows/active
```

**Data Used**:
- `flow_id` - Flow identifier
- `flow_name` - Display name
- `status` - Flow status (running, completed, failed, etc.)
- `current_phase` - Current phase name
- `progress` - Progress percentage (0-100)
- `phases` - Object with phase completion flags
- `created_at` / `updated_at` - Timestamps

**Backend Implementation**:
- **File**: `backend/app/services/discovery/flow_status/operations.py`
- **Function**: `get_active_flows()`
- **Data Source**: `CrewAIFlowStateExtensions` (master flows) + `DiscoveryFlow` (child flows)
- **Status**: ✅ **FIXED** - Now returns correct 5-phase structure and status

**Issues Fixed**:
- ✅ Bug #560: Progress bar showing 0% → Fixed to show actual progress
- ✅ Bug #578: Success criteria showing 0/6 → Fixed to show 5/5 (ADR-027)
- ✅ Current phase showing "initialization" → Fixed to show actual phase
- ✅ Status showing "running" for completed flows → Fixed to show "completed"

---

### 2. Monitor Flow Popup (Flow Status Modal)

**UI Component**: Triggered from "Monitor" button in FlowsOverview

**Primary API Endpoint**:
```
POST /api/v1/flow-processing/continue/{flow_id}
```

**Data Used**:
- `checklist_status` - Array of phase status objects
- `current_phase` - Current phase name
- `routing_context` - Navigation information
- `user_guidance` - User instructions

**Backend Implementation**:
- **File**: `backend/app/api/v1/endpoints/flow_processing/commands.py`
- **Function**: `continue_flow()`
- **Data Source**: `FlowHandler.get_flow_status()` → `DiscoveryFlow` table
- **Status**: ✅ **FIXED** - Now returns correct 5-phase checklist

**Issues Fixed**:
- ✅ Bug #557: Monitor popup showing only 1 phase → Fixed to show all 5 phases
- ✅ Data validation showing 0% → Fixed to show actual completion status
- ✅ Empty checklist_status → Fixed to populate from database flags

---

### 3. Individual Flow Status Page

**UI Component**: Individual flow detail pages (e.g., `/discovery/field-mapping`)

**Primary API Endpoint**:
```
GET /api/v1/unified-discovery/flows/{flow_id}/status
```

**Data Used**:
- `flow_id` - Flow identifier
- `status` - Flow status
- `current_phase` - Current phase name
- `progress_percentage` - Progress (0-100)
- `phases` - Object with phase completion flags

**Backend Implementation**:
- **File**: `backend/app/api/v1/endpoints/unified_discovery/flow_status_handlers.py`
- **Function**: `get_flow_status()`
- **Data Source**: `DiscoveryFlow` table directly
- **Status**: ✅ **FIXED** - Updated to 5-phase structure

**Issues Fixed**:
- ✅ Progress calculation → Fixed to use phase completion flags
- ✅ Phase structure → Updated to ADR-027 5-phase model

---

### 4. Master Flow Status (Background Processing)

**UI Component**: Used by various hooks and background processes

**Primary API Endpoint**:
```
GET /api/v1/master-flows/active?flow_type=discovery
```

**Data Used**:
- `flow_id` - Master flow identifier
- `flow_status` - Master flow status
- `flow_type` - Flow type (discovery, assessment, etc.)

**Backend Implementation**:
- **File**: `backend/app/api/v1/endpoints/master_flows.py`
- **Function**: `get_active_master_flows()`
- **Data Source**: `CrewAIFlowStateExtensions` table
- **Status**: ⚠️ **POTENTIAL ISSUE** - May need similar fixes

---

## Data Flow Architecture

### Master Flow vs Child Flow Pattern (ADR-012)

```
Master Flow (CrewAIFlowStateExtensions)
├── High-level lifecycle: initialized, running, completed, failed
├── Cross-flow coordination
└── References child flows

Child Flow (DiscoveryFlow)
├── Operational state: current_phase, progress_percentage
├── Phase completion flags
└── Business logic data
```

### API Endpoint Data Sources

| Endpoint | Primary Source | Secondary Source | Purpose |
|----------|---------------|------------------|---------|
| `/flows/active` | Master Flow | Child Flow | Overview listing |
| `/flows/{id}/status` | Child Flow | - | Individual flow details |
| `/flow-processing/continue/{id}` | Child Flow | - | Monitor popup |
| `/master-flows/active` | Master Flow | - | Background processing |

## Common Issues & Fixes Applied

### 1. Phase Structure Inconsistency

**Problem**: Different endpoints used different phase structures (6-phase vs 5-phase)

**ADR-027 Solution**: Standardized to 5-phase Discovery v3.0.0
- `data_import` → `data_validation` → `field_mapping` → `data_cleansing` → `asset_inventory`

**Files Fixed**:
- ✅ `backend/app/services/discovery/flow_status/operations.py` (2 code paths)
- ✅ `backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py`
- ✅ `backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py`
- ✅ `backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py`
- ✅ `backend/app/services/agents/agent_service_layer/handlers/flow_handler_helpers.py`
- ✅ `src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts`

### 2. Status Calculation Issues

**Problem**: Master flows don't have operational fields like `current_phase`

**Solution**: Calculate from child flow data or phase completion flags

**Logic Applied**:
```python
# For current_phase
if discovery_flow:
    current_phase = discovery_flow.current_phase
else:
    # Find first incomplete phase
    for phase in ["data_import", "data_validation", "field_mapping", "data_cleansing", "asset_inventory"]:
        if not phases_dict.get(phase, False):
            current_phase = phase
            break
    if current_phase is None:
        current_phase = "completed"

# For status
if discovery_flow:
    flow_status = discovery_flow.status
else:
    # Set to completed if all phases done
    if all_phases_completed:
        flow_status = "completed"
```

### 3. Progress Calculation Issues

**Problem**: Progress calculated differently across endpoints

**Solution**: Standardized calculation using phase completion flags

**Formula Applied**:
```python
completed_phases = sum([
    phases_dict["data_import"],
    phases_dict["data_validation"], 
    phases_dict["field_mapping"],
    phases_dict["data_cleansing"],
    phases_dict["asset_inventory"]
])
progress = (completed_phases / 5) * 100  # ADR-027: 5 phases total
```

## Frontend Data Transformation

### Dashboard Service (`dashboardService.ts`)

**File**: `src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts`

**Transformation**:
```typescript
// API Response → UI Data
{
  flow_id: string,
  status: string,
  current_phase: string,
  progress: number,
  phases: { [phase: string]: boolean }
} 
→ 
{
  flow_id: string,
  status: string,
  current_phase: string,
  progress: number,
  success_criteria_met: number,  // Calculated from phases
  total_success_criteria: 5      // ADR-027: Fixed to 5
}
```

**Key Calculation**:
```typescript
success_criteria_met: Object.values(flow.phases || {}).filter(Boolean).length,
total_success_criteria: 5, // Per ADR-027: Discovery v3.0.0 has 5 phases
```

## Testing & Validation

### API Response Validation

**Check Commands**:
```bash
# Overview page data
curl -s "http://localhost:8000/api/v1/unified-discovery/flows/active" \
  -H "x-client-account-id: 11111111-1111-1111-1111-111111111111" \
  -H "x-engagement-id: 22222222-2222-2222-2222-222222222222" | jq

# Monitor popup data  
curl -s "http://localhost:8000/api/v1/flow-processing/continue/{flow_id}" \
  -H "x-client-account-id: 11111111-1111-1111-1111-111111111111" \
  -H "x-engagement-id: 22222222-2222-2222-2222-222222222222" \
  -H "Content-Type: application/json" -d '{}' | jq

# Individual flow status
curl -s "http://localhost:8000/api/v1/unified-discovery/flows/{flow_id}/status" \
  -H "x-client-account-id: 11111111-1111-1111-1111-111111111111" \
  -H "x-engagement-id: 22222222-2222-2222-2222-222222222222" | jq
```

### Expected Response Format

**Overview Page** (`/flows/active`):
```json
{
  "success": true,
  "flows": [
    {
      "flow_id": "uuid",
      "flow_name": "Discovery Import ...",
      "status": "completed",           // ✅ Fixed: was "running"
      "current_phase": "asset_inventory", // ✅ Fixed: was null
      "progress": 100.0,               // ✅ Fixed: was 0%
      "phases": {                      // ✅ Fixed: 5 phases, not 6
        "data_import": true,
        "data_validation": true,
        "field_mapping": true,
        "data_cleansing": true,
        "asset_inventory": true
      }
    }
  ]
}
```

**Monitor Popup** (`/flow-processing/continue/{id}`):
```json
{
  "success": true,
  "checklist_status": [               // ✅ Fixed: was empty array
    {
      "phase_id": "data_import",
      "phase_name": "Data Import",
      "status": "completed",
      "completion_percentage": 100.0
    },
    {
      "phase_id": "data_validation",  // ✅ Fixed: was missing
      "phase_name": "Data Validation", 
      "status": "completed",
      "completion_percentage": 100.0
    }
    // ... all 5 phases
  ]
}
```

## Future Prevention

### 1. Centralized Phase Configuration

**ADR-027 Implementation**: Use `FlowTypeConfig` as single source of truth

**Backend**: All endpoints should use `FlowTypeConfig.get_discovery_flow_config()`
**Frontend**: Use `useFlowPhases` hook instead of hardcoded constants

### 2. Consistent Data Layer

**Recommendation**: Create a unified flow status service that all endpoints use

```python
class UnifiedFlowStatusService:
    def get_flow_status(self, flow_id: str) -> FlowStatusResponse:
        # Single implementation used by all endpoints
        pass
    
    def get_active_flows(self, context: RequestContext) -> List[FlowStatusResponse]:
        # Single implementation used by all endpoints  
        pass
```

### 3. API Response Standardization

**Recommendation**: All flow-related endpoints should return the same data structure

```typescript
interface StandardFlowResponse {
  flow_id: string;
  status: 'initialized' | 'running' | 'completed' | 'failed' | 'paused';
  current_phase: string;
  progress: number;
  phases: { [phase: string]: boolean };
  metadata: FlowMetadata;
}
```

## Related Documentation

- **ADR-012**: Flow Status Management Separation
- **ADR-027**: Universal FlowTypeConfig Pattern  
- **Bug #557**: Monitor Flow Popup Phase Display
- **Bug #560**: Overview Progress Bar
- **Bug #578**: Success Criteria Count
- **Bug #579**: Data Import Flag Persistence

## Maintenance Notes

**When adding new flow types**:
1. Update `FlowTypeConfig` definitions
2. Update all endpoint implementations to use the config
3. Update frontend `useFlowPhases` hook
4. Test all UI components that display flow data

**When modifying phase structure**:
1. Update `FlowTypeConfig` first
2. Update all backend endpoints that calculate phases
3. Update frontend phase calculations
4. Run full UI test suite

**When fixing flow status issues**:
1. Check this document for all affected endpoints
2. Apply fixes to ALL endpoints, not just the reported one
3. Test all UI components that consume the data
4. Update this document if new endpoints are discovered
