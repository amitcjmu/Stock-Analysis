# Data Flow Analysis Report: Resource Page

**Analysis Date:** 2025-10-29
**Previous Version:** 2024-07-29 (Placeholder Analysis)
**Status:** Backend Fully Implemented, Frontend Placeholder

---

## Overview

The Resource page manages resource allocation and skill gap analysis for migration waves. It displays role-based resource assignments, calculates utilization, identifies skill gaps, and supports AI-driven suggestions with manual override.

---

## Backend Implementation (Migration 114)

### Database Tables

#### `resource_pools`

Role-based resource capacity tracking with auto-calculated utilization.

**Key Fields:**

- `pool_name` (VARCHAR): Pool identifier
- `role_name` (VARCHAR): Role name (e.g., "Cloud Architect")
- `total_capacity_hours` (NUMERIC): Total available hours
- `available_capacity_hours` (NUMERIC): Current available hours
- `allocated_capacity_hours` (NUMERIC): Currently allocated hours
- `hourly_rate` (NUMERIC): Cost per hour
- `utilization_percentage` (NUMERIC): Auto-calculated (trigger)
- `skills` (JSONB): Array of skills

**Trigger:** Auto-calculates utilization percentage on INSERT/UPDATE

#### `resource_allocations`

Resource assignments to migration waves with AI suggestions.

**Key Fields:**

- `planning_flow_id` (UUID): FK to planning_flows
- `wave_id` (UUID): FK to migration_waves
- `resource_pool_id` (UUID): FK to resource_pools
- `allocated_hours` (NUMERIC): Allocated hours
- `allocation_start_date` (TIMESTAMP): Start date
- `allocation_end_date` (TIMESTAMP): End date
- `is_ai_suggested` (BOOLEAN): AI-generated recommendation
- `ai_confidence_score` (NUMERIC): Confidence (0-100)
- `manual_override` (BOOLEAN): User modified AI suggestion
- `status` (VARCHAR): Allocation status

#### `resource_skills`

Skill requirements and gap analysis per wave.

**Key Fields:**

- `wave_id` (UUID): FK to migration_waves
- `skill_name` (VARCHAR): Required skill
- `required_hours` (NUMERIC): Hours required
- `available_hours` (NUMERIC): Hours available
- `has_gap` (BOOLEAN): Skill gap exists
- `gap_severity` (VARCHAR): Severity (`none`, `low`, `medium`, `high`, `critical`)
- `mitigation_plan` (TEXT): Plan to address gap
- `training_required` (BOOLEAN): Training needed
- `external_hire_needed` (BOOLEAN): External hire needed

---

## Service Layer

### Method: `execute_resource_allocation_phase()`

**Location:** `backend/app/services/planning_service.py` (lines 302-447)

**Agent:** `ResourceAllocationSpecialist` (via `PlanningCrew`)

**Process:**

1. Validates wave plan completed
2. Prepares resource pools (roles, hourly rates)
3. Invokes resource allocation agent
4. Agent suggests resource allocations per wave
5. Calculates skill gaps (non-blocking warnings)
6. Saves to `resource_allocation_data` JSONB + relational tables
7. Transitions to timeline generation phase

**AI Features:**

- Suggests optimal resource allocations based on wave complexity
- Provides confidence scores (0-100)
- Identifies skill gaps with severity levels
- Supports manual override without blocking progression

---

## Repository Layer

### Resource Methods

**Location:** `backend/app/repositories/planning_flow_repository.py`

| Method                             | Lines      | Purpose                                |
|------------------------------------|------------|----------------------------------------|
| **Resource Pools**                 |            |                                        |
| `create_resource_pool()`           | 835-889    | Create resource pool                   |
| `list_resource_pools()`            | 891-928    | List all pools (tenant-scoped)         |
| `get_resource_pool_by_id()`        | 930-968    | Get pool by ID                         |
| `update_resource_pool()`           | 970-1020   | Update pool                            |
| **Resource Allocations**           |            |                                        |
| `create_resource_allocation()`     | 1026-1083  | Allocate resource to wave              |
| `list_allocations_by_wave()`       | 1085-1122  | Get allocations for wave               |
| `list_allocations_by_planning_flow()` | 1124-1163 | Get allocations for planning flow   |
| `update_allocation()`              | 1165-1224  | Update allocation                      |
| **Resource Skills**                |            |                                        |
| `create_resource_skill()`          | 1230-1275  | Create skill requirement               |
| `list_skills_by_wave()`            | 1277-1312  | Get skills for wave                    |
| `list_skill_gaps_by_wave()`        | 1314-1351  | Get skill gaps for wave                |

---

## Frontend Integration TODO

### Current Status

**File:** `src/pages/plan/Resource.tsx`

**Status:** Placeholder UI (no API integration)

### Implementation Steps

#### 1. Create Resource Data Hook

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/apiClient';

function useResourceAllocation(planning_flow_id: string) {
  return useQuery({
    queryKey: ['resource-allocation', planning_flow_id],
    queryFn: async () => {
      const status = await planningFlowApi.getPlanningStatus(planning_flow_id);
      return status.resource_allocation_data;
    },
    refetchInterval: 10000 // Poll every 10 seconds
  });
}
```

#### 2. Display Resource Pools

**Component:** Resource pool cards showing:

- Role name
- Total capacity vs allocated capacity
- Utilization percentage (color-coded)
- Hourly rate
- Available skills

#### 3. Display Wave Allocations

**Component:** Allocation table per wave:

- Wave number and name
- Allocated resources (role, hours, cost)
- AI confidence score (if AI-suggested)
- Manual override indicator
- Status (planned, confirmed, in_progress)

#### 4. Display Skill Gaps

**Component:** Skill gap warnings panel:

- Skill name
- Required hours vs available hours
- Gap severity (color-coded badge)
- Mitigation plan
- Training/external hire indicators

#### 5. Manual Override Feature

**Action:** Allow users to:

- Modify AI-suggested allocations
- Add/remove resources from waves
- Update allocation hours
- Mark allocations as "manual override"

---

## API Integration

### Expected Endpoints (TODO)

| Method | Endpoint                                         | Purpose                          |
|--------|--------------------------------------------------|----------------------------------|
| GET    | `/api/v1/master-flows/planning/resources/{id}`  | Get resource allocation data     |
| PUT    | `/api/v1/master-flows/planning/resources/{id}`  | Update resource allocations      |
| POST   | `/api/v1/master-flows/planning/execute-phase`   | Trigger resource allocation agent|

### Data Structure

```typescript
interface ResourceAllocationData {
  allocations: Array<{
    wave_id: string;
    wave_number: number;
    resources: Array<{
      role_name: string;
      allocated_hours: number;
      hourly_rate: number;
      estimated_cost: number;
      is_ai_suggested: boolean;
      ai_confidence_score: number;
      manual_override: boolean;
    }>;
  }>;
  skill_gaps: Array<{
    skill_name: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    impact: string;
    required_hours: number;
    available_hours: number;
    training_required: boolean;
    external_hire_needed: boolean;
  }>;
  total_cost_estimate: number;
}
```

---

## Troubleshooting

| Issue                        | Check                                        | Fix                                               |
|------------------------------|----------------------------------------------|---------------------------------------------------|
| **No resource pools**        | `resource_pools` table empty                 | Create resource pools via admin interface         |
| **Utilization incorrect**    | Check trigger calculation                    | Query: `SELECT * FROM migration.resource_pools;`  |
| **AI confidence missing**    | Agent execution log empty                    | Verify agent populates `ai_confidence_score`      |
| **Skill gaps not showing**   | `resource_skills` table empty                | Check agent skill gap analysis logic              |
| **Manual override fails**    | Check `manual_override` boolean update       | Verify PUT endpoint updates field correctly       |

---

## Implementation Priority

**High Priority:**

1. Integrate resource allocation display with backend data
2. Show AI confidence scores for transparency
3. Display skill gaps with severity indicators

**Medium Priority:**

4. Enable manual override functionality
5. Add resource pool management interface
6. Implement allocation editing

**Low Priority:**

7. Add resource utilization charts
8. Enable allocation drag-and-drop
9. Export resource plan to Excel

---

## Related Files

- **Backend Service:** `backend/app/services/planning_service.py:302-447`
- **Backend Repository:** `backend/app/repositories/planning_flow_repository.py:835-1351`
- **Frontend Page:** `src/pages/plan/Resource.tsx` (placeholder)
- **Migration:** `114_create_resource_planning_tables.py`

---

## Summary

The Resource page backend is **FULLY IMPLEMENTED** with comprehensive database schema (migration 114) and service layer logic. Frontend is **PLACEHOLDER** awaiting integration.

**Key Features:**

- Role-based resource pools (NOT individual contributors per #690)
- Auto-calculated utilization percentage
- AI-driven allocation suggestions with confidence scores
- Skill gap analysis (non-blocking warnings)
- Manual override capability
- Multi-tenant scoping throughout

**Next Steps:**

1. Create frontend data hooks
2. Build resource display components
3. Integrate with planning status endpoint
4. Add manual override UI
5. Test with agent-generated data
