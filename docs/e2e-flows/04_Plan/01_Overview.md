# Data Flow Analysis Report: Plan Overview Page

This document provides a complete, end-to-end data flow analysis for the `Plan Overview` page of the AI Modernize Migration Platform.

**Analysis Date:** 2025-11-10
**Previous Version:** 2025-10-29 (Partial Implementation)
**Status:** Backend COMPLETE, Frontend Integration Pending

---

## 1. Frontend: Components and API Calls

The Plan Overview page serves as the central dashboard for the migration planning phase, providing summary metrics, quick action links, and AI-driven insights. It also hosts the Planning Initialization Wizard for starting new planning flows.

### Key Components & Hooks

#### Page Component

- **Location:** `src/pages/plan/Index.tsx`
- **Key Imports:**
  - `PlanningInitializationWizard` (line 10) - Multi-step wizard for starting planning
  - Context and routing components
  - Icon components from `lucide-react`

#### Core UI Elements

1. **Planning Initialization Wizard** (lines 13-14, 56-62)
   - Modal component controlled by `isWizardOpen` state
   - Triggered by "Start Planning" button
   - Full implementation in `src/components/plan/PlanningInitializationWizard.tsx`

2. **Summary Cards** (lines 19-24, 72-88)
   - **Current Status:** Hard-coded placeholder data
   - Displays:
     - Waves Planned: 3 waves
     - Resource Utilization: 75%
     - Target Designs: 2 designs
     - Planning Progress: 60%

3. **AI Assistant Panel** (lines 32-36, 91-104)
   - **Current Status:** Hard-coded insights
   - Example insights:
     - "Migration Goals Assistant recommends light modernization for Wave 1"
     - "AI suggests 2-week buffer for critical applications in Wave 2"
     - "Resource optimization shows 15% efficiency gain possible"

4. **Quick Actions** (lines 26-30, 107-123)
   - Navigation links to:
     - `/plan/timeline` - Migration Timeline
     - `/plan/resource` - Resource Allocation
     - `/plan/target` - Target Architecture

### Current API Integration

**Status (November 2025):** MFO endpoints IMPLEMENTED, frontend integration PENDING

**Available API Endpoints:**

| # | Method | Endpoint                                           | Status      | Description                                      |
|---|--------|---------------------------------------------------|-------------|--------------------------------------------------|
| 1 | `POST` | `/api/v1/master-flows/planning/initialize`        | ✅ ACTIVE   | Creates master + child planning flow             |
| 2 | `GET`  | `/api/v1/master-flows/planning/status/{flow_id}`  | ✅ ACTIVE   | Fetches complete planning flow state             |
| 3 | `POST` | `/api/v1/master-flows/planning/execute-phase`     | ⚠️ PARTIAL  | Triggers phase execution (agent wiring pending)  |
| 4 | `PUT`  | `/api/v1/master-flows/planning/update`            | ✅ ACTIVE   | Updates planning flow data                       |
| 5 | `GET`  | `/api/v1/master-flows/planning/export/{flow_id}`  | ✅ ACTIVE   | Exports planning data (report generation pending)|

**Frontend Integration TODO:**
- Replace hard-coded dashboard data in `Index.tsx` (lines 19-36)
- Call `/status/{flow_id}` endpoint for real-time polling
- Extract AI insights from `agent_execution_log` JSONB field

---

## 2. Backend, CrewAI, ORM, and Database Trace

### Current Backend Implementation

#### Existing Endpoints (Placeholder Data)

**File:** `backend/app/api/v1/endpoints/plan.py`

##### `GET /api/v1/plan/` (lines 147-181)

Returns hard-coded plan overview metrics.

```python
overview_data = {
    "summary": {
        "totalApps": 83,
        "plannedApps": 45,
        "totalWaves": 3,
        "completedPhases": 2,
        "upcomingMilestones": 4,
    },
    "nextMilestone": {
        "name": "Wave 1 Migration Start",
        "date": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
        "description": "Begin migration activities for Wave 1 applications",
    },
    "recentActivity": [...]
}
```

**Status:** Placeholder - does NOT query database.

#### Expected Backend Implementation (TODO)

##### Service Layer

**File:** `backend/app/services/planning_service.py`

**New Method Required:**

```python
async def get_planning_summary(
    self,
    engagement_id: int,
    client_account_id: int
) -> Dict[str, Any]:
    """
    Generate planning summary dashboard metrics.

    Aggregates data from:
    - planning_flows table (wave counts, phase completion)
    - resource_allocations table (utilization %)
    - project_timelines table (upcoming milestones)
    - Assets table (total applications)

    Returns:
        Dict with summary metrics for dashboard
    """
```

##### Repository Layer

**File:** `backend/app/repositories/planning_flow_repository.py`

**Methods to Use:**

- `get_all()` (lines 38-75) - Get all planning flows for engagement
- `list_resource_pools()` (lines 891-928) - Get resource pools for utilization calc
- `get_timeline_by_planning_flow()` (lines 523-567) - Get timeline for milestones

##### ORM Models

**File:** `backend/app/models/planning.py`

**Tables to Query:**

1. **`PlanningFlow`** (lines 44-147)
   - Fields: `current_phase`, `phase_status`, `wave_plan_data`, `planning_completed_at`
   - Purpose: Count waves, determine completion status

2. **`ResourcePool`** (Migration 114)
   - Fields: `utilization_percentage`, `allocated_capacity_hours`, `total_capacity_hours`
   - Purpose: Calculate average resource utilization

3. **`ProjectTimeline`** (Migration 113)
   - Related: `TimelineMilestone` (for upcoming milestones)
   - Purpose: Find next milestone dates

##### Database Queries

**Wave Count Query:**

```sql
SELECT
    JSONB_ARRAY_LENGTH(wave_plan_data->'waves') AS total_waves,
    current_phase,
    phase_status
FROM migration.planning_flows
WHERE client_account_id = $1
  AND engagement_id = $2
ORDER BY created_at DESC
LIMIT 1;
```

**Resource Utilization Query:**

```sql
SELECT
    AVG(utilization_percentage) AS avg_utilization
FROM migration.resource_pools
WHERE client_account_id = $1
  AND engagement_id = $2
  AND is_active = true;
```

**Upcoming Milestones Query:**

```sql
SELECT
    m.milestone_name,
    m.target_date,
    m.description,
    m.status
FROM migration.timeline_milestones m
JOIN migration.project_timelines t ON m.timeline_id = t.id
WHERE t.client_account_id = $1
  AND t.engagement_id = $2
  AND m.target_date > NOW()
ORDER BY m.target_date ASC
LIMIT 5;
```

---

## 3. Planning Initialization Wizard Flow

### User Journey

1. **User clicks "Start Planning" button** (line 58)
2. **Wizard opens** (`PlanningInitializationWizard` component)
3. **Step 1:** Select applications (from Assessment results)
4. **Step 2:** Configure planning parameters:
   - Max apps per wave
   - Wave duration limit (days)
   - Contingency percentage
5. **Step 3:** Review and submit
6. **API Call:** `planningFlowApi.initializePlanningFlow()`

### Backend Processing (From Service Layer)

**Service:** `planning_service.py:81-190` (`initialize_planning_flow()`)

**Steps:**

1. Validate planning configuration (line 127)
2. Validate selected applications exist (lines 131-137)
3. Create `PlanningFlow` record (lines 147-169)
   - Initial phase: `"wave_planning"`
   - Status: `"ready"`
   - Store config and selected apps in JSONB
4. Commit to database (line 172)
5. Return `planning_flow_id` and `master_flow_id`

### Frontend Response Handling

After successful initialization:

1. **Redirect** to Wave Planning page (`/plan/wave-planning?planning_flow_id={id}`)
2. **Polling begins** for planning status updates
3. **User can trigger** wave planning execution

---

## 4. End-to-End Flow Sequence: Loading the Plan Dashboard

### Current Implementation (Placeholder)

1. **User Navigates:** User loads Plan Overview page
2. **Component Mounts:** `PlanIndex` component renders
3. **Static Data Rendered:** Hard-coded summary cards and AI insights display
4. **No API Calls:** All data is client-side only

### Target Implementation (TODO)

1. **User Navigates:** User loads Plan Overview page
2. **Frontend Hook:** `useQuery` hook for `planning-summary` triggers
3. **API Call:** `GET /api/v1/master-flows/planning/summary`
   - Headers: `x-client-account-id: 1`, `x-engagement-id: 1`
4. **Backend Route:** FastAPI router → `get_planning_summary()` service method
5. **Service Logic:**
   - Query latest planning flow for engagement
   - Calculate wave count from `wave_plan_data` JSONB
   - Calculate resource utilization from `resource_pools` table
   - Query upcoming milestones from `timeline_milestones` table
   - Query recent agent execution log from `planning_flows.agent_execution_log`
6. **ORM Query:** Repository layer executes multi-table queries with tenant scoping
7. **DB Execution:** PostgreSQL returns aggregated metrics
8. **Backend Response:**
   ```json
   {
     "summary": {
       "total_apps": 83,
       "planned_apps": 45,
       "total_waves": 3,
       "completed_phases": 2,
       "upcoming_milestones": 4,
       "resource_utilization_percentage": 75.5
     },
     "next_milestone": {
       "name": "Wave 1 Migration Start",
       "date": "2025-02-01T00:00:00Z",
       "description": "Begin migration activities for Wave 1 applications",
       "status": "pending"
     },
     "recent_activity": [
       {
         "date": "2025-10-29T14:30:00Z",
         "activity": "Wave planning completed",
         "description": "Generated 3 migration waves with AI optimization",
         "phase": "wave_planning"
       }
     ],
     "ai_insights": [
       "AI suggests 2-week buffer for critical applications in Wave 2",
       "Resource optimization shows 15% efficiency gain possible",
       "Consider parallel wave execution for independent application groups"
     ]
   }
   ```
9. **UI Render:** Component updates with real data:
   - Summary cards show actual metrics
   - AI insights from agent execution log
   - Recent activity from database
   - Next milestone with real date

---

## 5. Troubleshooting Breakpoints

| Breakpoint                           | Diagnostic Check                                                                                    | Platform-Specific Fix                                                                                                                      |
|--------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **Dashboard Shows Placeholder Data** | This is the current state. Real data integration is pending.                                        | Implement `usePlanningDashboard` hook that calls `/api/v1/master-flows/planning/summary` endpoint. Replace hard-coded data in lines 19-36. |
| **API Call Fails (404)**             | If implemented API returns 404, the backend route has not been created yet.                         | Create `get_planning_summary()` endpoint in `backend/app/api/v1/endpoints/planning_flow.py`. Wire to `planning_service.py` method.       |
| **API Call Fails (403)**             | Multi-tenant headers missing or invalid.                                                            | Verify `x-client-account-id` and `x-engagement-id` headers in request. Check `get_current_context()` middleware is enabled.              |
| **Summary Metrics Incorrect**        | Aggregation query in service layer is incorrect.                                                    | Debug SQL queries in repository layer. Check JSONB path queries (e.g., `wave_plan_data->'waves'`) are correct.                           |
| **No Planning Flow Data**            | User hasn't initiated planning yet.                                                                 | Show "Start Planning" wizard. Query should return empty state gracefully (not error).                                                     |
| **Wizard Initialization Fails**      | Check request body structure and tenant headers.                                                    | Verify `InitializePlanningFlowRequest` payload in browser DevTools. Check backend validation errors in response.                         |
| **Resource Utilization Shows 0%**    | No resource pools created or all pools have 0 total capacity.                                       | Query: `SELECT * FROM migration.resource_pools WHERE client_account_id = 1 AND engagement_id = 1;` Verify pools exist with capacity > 0. |
| **Upcoming Milestones Empty**        | No project timeline created or all milestones in past.                                              | Query: `SELECT * FROM migration.project_timelines WHERE client_account_id = 1 AND engagement_id = 1;` Verify timeline generation completed. |
| **AI Insights Not Updating**         | Agent execution log not being populated during phase execution.                                     | Check `planning_flows.agent_execution_log` JSONB column. Verify service layer appends to log during agent execution (e.g., line 270-278). |

---

## 6. Implementation TODO List

### High Priority

1. **Create `/api/v1/master-flows/planning/summary` endpoint**
   - File: `backend/app/api/v1/endpoints/planning_flow.py`
   - Method: `get_planning_summary()`
   - Returns: Dashboard metrics as JSON

2. **Implement `get_planning_summary()` in `planning_service.py`**
   - Aggregate data from multiple tables
   - Calculate wave count, resource utilization, milestone dates
   - Extract AI insights from agent execution log

3. **Create frontend hook `usePlanningDashboard()`**
   - Location: `src/hooks/usePlanningDashboard.ts`
   - Uses React Query for data fetching
   - Polls every 15 seconds for updates

4. **Update `Index.tsx` to use real data**
   - Replace hard-coded `summaryCards` (line 19-24)
   - Replace hard-coded `aiInsights` (line 32-36)
   - Replace hard-coded `quickActions` with dynamic generation

### Medium Priority

5. **Add AI insights generation to agent execution**
   - Update `planning_service.py` to extract insights from agent outputs
   - Store insights in `agent_execution_log` with structured format

6. **Implement recent activity tracking**
   - Track phase transitions in `agent_execution_log`
   - Display last 5 activities in dashboard

7. **Add export functionality**
   - "Export Planning Report" button
   - Calls `planningFlowApi.exportPlanningData()`

### Low Priority

8. **Add polling status indicator**
   - Show "Data refreshing..." badge when polling

9. **Add manual refresh button**
   - Trigger immediate data refresh

10. **Add planning flow selection dropdown**
    - If multiple planning flows exist for engagement

---

## 7. Data Structures

### Planning Summary Response

```typescript
interface PlanningDashboardSummary {
  summary: {
    total_apps: number;
    planned_apps: number;
    total_waves: number;
    completed_phases: number;
    upcoming_milestones: number;
    resource_utilization_percentage: number;
  };
  next_milestone: {
    name: string;
    date: string; // ISO 8601
    description: string;
    status: 'pending' | 'in_progress' | 'completed';
  } | null;
  recent_activity: Array<{
    date: string; // ISO 8601
    activity: string;
    description: string;
    phase: string;
  }>;
  ai_insights: string[];
}
```

### Planning Initialization Request

```typescript
interface InitializePlanningFlowRequest {
  engagement_id: number;
  selected_application_ids: string[]; // UUID strings
  planning_config?: {
    max_apps_per_wave?: number; // Default: 5
    wave_duration_limit_days?: number; // Default: 90
    contingency_percentage?: number; // Default: 15
  };
}
```

---

## 8. Related Files

### Frontend

- **Page:** `src/pages/plan/Index.tsx`
- **Wizard:** `src/components/plan/PlanningInitializationWizard.tsx`
- **API Client:** `src/lib/api/planningFlowService.ts` (lines 152-170: `initializePlanningFlow()`)

### Backend

- **Service:** `backend/app/services/planning_service.py`
  - Lines 81-190: `initialize_planning_flow()`
  - Lines 773-857: `get_planning_status()` (can be adapted for summary)
- **Repository:** `backend/app/repositories/planning_flow_repository.py`
  - Lines 79-324: PlanningFlow CRUD operations
  - Lines 891-928: Resource pool queries
  - Lines 687-728: Timeline phase queries
- **Models:** `backend/app/models/planning.py`
  - Lines 44-147: `PlanningFlow` model

### Database

- **Migrations:**
  - `112_create_planning_flows_table.py` - Planning flows table
  - `113_create_timeline_tables.py` - Timeline tables
  - `114_create_resource_planning_tables.py` - Resource tables

---

## 9. Summary

The Plan Overview page serves as the **central hub** for the Planning phase, providing users with:

1. **Summary Metrics:** High-level view of planning progress
2. **AI Insights:** Recommendations from CrewAI agents
3. **Quick Actions:** Navigation to detailed planning pages
4. **Initialization:** Entry point for starting new planning flows

**Current Status (October 2025):**

- **Wizard:** IMPLEMENTED and functional
- **Dashboard:** Placeholder data, API integration PENDING
- **Backend:** Service layer complete, endpoints PENDING
- **Database:** Schema complete and production-ready

**Next Steps:**

1. Implement missing MFO endpoints
2. Create planning summary service method
3. Build frontend data hook
4. Replace placeholder data with API calls
5. Add real-time polling for status updates

This document aligns with the comprehensive style established in `00_Planning_Flow_Summary.md` and provides clear guidance for completing the dashboard implementation.
