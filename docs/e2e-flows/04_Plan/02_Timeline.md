# Data Flow Analysis Report: Timeline Page

**Analysis Date:** 2025-10-29
**Previous Version:** 2024-07-29 (Placeholder Analysis)
**Status:** Real Backend Data Available, Frontend Integration Pending

---

## Overview

The Timeline page provides a detailed Gantt chart view of the migration timeline, including phases, milestones, dependencies, and critical path analysis. This page visualizes the output from the Timeline Generation phase (Phase 3) of the Planning flow.

---

## Current Implementation Status

### Frontend: `src/pages/plan/Timeline.tsx`

**Status:** Placeholder UI (as of original analysis)

**TODO:** Integrate with actual backend endpoints

### Backend: Real Data Available

#### Endpoint: `GET /api/v1/plan/roadmap`

**File:** `backend/app/api/v1/endpoints/plan.py` (lines 17-133)

**Implementation:** REAL DATA from migrations 112-113

**Response Structure:**

```json
{
  "timeline_id": "uuid",
  "timeline_name": "Migration Timeline - Engagement 1",
  "overall_start_date": "2025-01-01T00:00:00Z",
  "overall_end_date": "2025-06-30T23:59:59Z",
  "phases": [
    {
      "id": "uuid",
      "phase_name": "Wave 1 Planning",
      "planned_start_date": "2025-01-01",
      "planned_end_date": "2025-01-31",
      "status": "in_progress",
      "wave_number": 1
    }
  ],
  "milestones": [
    {
      "id": "uuid",
      "milestone_name": "Wave 1 Go-Live",
      "target_date": "2025-03-31",
      "status": "pending",
      "description": "All Wave 1 applications live in production"
    }
  ],
  "roadmap_status": "active"
}
```

### Database Tables (Migration 113)

#### `project_timelines`

- `id` (UUID): Primary key
- `planning_flow_id` (UUID): FK to planning_flows
- `timeline_name` (VARCHAR): Timeline name
- `overall_start_date` (TIMESTAMP): Timeline start
- `overall_end_date` (TIMESTAMP): Timeline end
- `timeline_status` (VARCHAR): Status

#### `timeline_phases`

- `timeline_id` (UUID): FK to project_timelines
- `phase_number` (INTEGER): Sequence number
- `phase_name` (VARCHAR): Phase name
- `planned_start_date` (TIMESTAMP): Planned start
- `planned_end_date` (TIMESTAMP): Planned end
- `status` (VARCHAR): Phase status
- `wave_number` (INTEGER): Associated wave

#### `timeline_milestones`

- `timeline_id` (UUID): FK to project_timelines
- `milestone_number` (INTEGER): Sequence number
- `milestone_name` (VARCHAR): Milestone name
- `target_date` (TIMESTAMP): Target date
- `status` (VARCHAR): Milestone status
- `description` (TEXT): Description

---

## Service Layer Integration

### Method: `execute_timeline_generation_phase()`

**Location:** `backend/app/services/planning_service.py` (lines 449-539)

**Agent:** `TimelinePlanningSpecialist` (via `PlanningCrew`)

**Process:**

1. Validates resource allocation completed
2. Invokes timeline generation agent
3. Creates records in `project_timelines`, `timeline_phases`, `timeline_milestones`
4. Saves timeline data to `planning_flows.timeline_data` JSONB
5. Transitions to cost estimation phase

---

## Repository Layer

### Timeline Methods

**Location:** `backend/app/repositories/planning_flow_repository.py`

| Method                           | Lines    | Purpose                           |
|----------------------------------|----------|-----------------------------------|
| `create_timeline()`              | 471-521  | Create project timeline           |
| `get_timeline_by_planning_flow()`| 523-567  | Get timeline for planning flow    |
| `update_timeline()`              | 569-626  | Update timeline                   |
| `create_timeline_phase()`        | 632-685  | Create timeline phase             |
| `get_phases_by_timeline()`       | 687-728  | Get all phases for timeline       |
| `create_milestone()`             | 734-783  | Create timeline milestone         |
| `get_milestones_by_timeline()`   | 786-829  | Get all milestones for timeline   |

---

## Frontend Integration TODO

### 1. Update `Timeline.tsx` Component

**Replace placeholder hook** with:

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/apiClient';

function useTimeline() {
  return useQuery({
    queryKey: ['timeline'],
    queryFn: async () => {
      const response = await apiClient.get('/plan/roadmap');
      return response;
    },
    refetchInterval: 15000 // Poll every 15 seconds
  });
}
```

### 2. Add Gantt Chart Library

**Recommended:** `react-gantt-chart` or `dhtmlx-gantt`

**Install:**

```bash
npm install react-gantt-chart
```

### 3. Transform Data for Gantt Display

**Map phases to Gantt tasks:**

```typescript
const ganttTasks = timeline.phases.map(phase => ({
  id: phase.id,
  name: phase.phase_name,
  start: new Date(phase.planned_start_date),
  end: new Date(phase.planned_end_date),
  progress: getProgressFromStatus(phase.status),
  dependencies: getDependencies(phase)
}));
```

---

## Troubleshooting

| Issue                          | Check                                                  | Fix                                                      |
|--------------------------------|--------------------------------------------------------|----------------------------------------------------------|
| **Timeline empty**             | No timeline created for planning flow                  | Ensure timeline generation phase completed              |
| **Phases missing**             | `timeline_phases` table empty                          | Check agent execution log for errors                     |
| **Dates incorrect**            | Agent calculation error                                | Review `planning_config.wave_duration_limit_days`        |
| **Critical path wrong**        | Dependencies not calculated                            | Implement critical path algorithm in agent               |

---

## Implementation Priority

**High Priority:**

1. Integrate `/plan/roadmap` endpoint with frontend
2. Add Gantt chart visualization
3. Display milestones on timeline

**Medium Priority:**

4. Add critical path highlighting
5. Enable phase editing
6. Export timeline to PDF/image

**Low Priority:**

7. Add resource allocation overlay
8. Enable milestone drag-and-drop

---

## Related Files

- **Backend Endpoint:** `backend/app/api/v1/endpoints/plan.py:17-133`
- **Service:** `backend/app/services/planning_service.py:449-539`
- **Repository:** `backend/app/repositories/planning_flow_repository.py:471-829`
- **Frontend:** `src/pages/plan/Timeline.tsx` (placeholder)
- **Migrations:** `113_create_timeline_tables.py`

---

## Summary

The Timeline page backend is **FULLY IMPLEMENTED** with real data from migration 113 tables. Frontend integration is **PENDING**. Priority is to replace placeholder UI with actual API polling and Gantt chart visualization.

**Key Changes from July 2024:**

- Backend now uses real database queries (not placeholder)
- Timeline data stored in normalized tables + JSONB
- Agent-driven timeline generation implemented
- Multi-tenant scoping enforced
- MFO integration complete
