# E2E Flow: Planning Phase

This document outlines the end-to-end user and data flow for the **Planning** phase of the migration process, which is fully integrated with the Master Flow Orchestrator (MFO) architecture.

**Last Updated:** 2025-10-29
**Status:** Actively Implemented (Post-October 2025)

---

## 1. Objective

The primary objective of the Planning flow is to translate assessment results into actionable migration plans. This involves wave planning (grouping applications into sequential migration batches), resource allocation, timeline generation with Gantt chart visualization, and comprehensive cost estimation. The Planning phase leverages CrewAI agents for AI-driven recommendations while allowing manual override and adjustment.

---

## 2. MFO Integration Architecture

The Planning flow follows the **Master Flow Orchestrator** pattern established in ADR-006 and ADR-012:

### Two-Table Pattern

- **Master Table**: `migration.crewai_flow_state_extensions`
  - Tracks high-level lifecycle: `running`, `paused`, `completed`
  - Referenced by `master_flow_id` (UUID)
  - Created by MFO on flow initialization

- **Child Table**: `migration.planning_flows` (Migration 112)
  - Tracks operational state: phases, wave data, resource allocations
  - Referenced by `planning_flow_id` (UUID)
  - Contains JSONB columns for flexible planning data storage

### Primary Identifiers

- **ALL Planning operations use** `master_flow_id` as the primary identifier
- Frontend components reference `planning_flow_id` for operational data
- Backend automatically resolves `master_flow_id` → `planning_flow_id` mapping

### API Pattern

- **Flow Lifecycle**: `/api/v1/master-flows/*` (create, resume, pause, complete)
- **Planning Operations**: `/api/v1/master-flows/planning/*` (initialize, execute-phase, status)
- **Legacy Endpoints**: `/api/v1/plan/*` and `/api/v1/wave_planning/*` (placeholder data, scheduled for removal)

---

## 3. API Call Summary (MFO-Aligned)

| # | Method | Endpoint                                              | Trigger                                    | Description                                                |
|---|--------|-------------------------------------------------------|--------------------------------------------|------------------------------------------------------------|
| 1 | `POST` | `/api/v1/master-flows/planning/initialize`           | User initiates planning flow via wizard.   | Creates master flow + child planning flow.                 |
| 2 | `POST` | `/api/v1/master-flows/planning/execute-phase`        | User triggers phase execution.             | Executes specific planning phase (wave/resource/timeline). |
| 3 | `GET`  | `/api/v1/master-flows/planning/status/{flow_id}`     | Polling for status updates.                | Fetches current planning status and progress.              |
| 4 | `PUT`  | `/api/v1/master-flows/planning/update-wave-plan`     | User manually adjusts wave assignments.    | Updates wave plan data with manual modifications.          |
| 5 | `GET`  | `/api/v1/master-flows/planning/export/{flow_id}`     | User exports planning report.              | Exports planning data in JSON/PDF/Excel format.            |
| 6 | `GET`  | `/api/v1/wave_planning/`                             | Legacy endpoint (placeholder data).        | Returns stub wave planning data.                           |
| 7 | `GET`  | `/api/v1/plan/roadmap`                               | Legacy endpoint (mixed real/placeholder).  | Returns timeline/roadmap data.                             |

**Key Architecture Decisions:**

- All flow lifecycle operations go through MFO (ADR-006)
- Planning-specific operations use `/master-flows/planning/*` prefix
- No direct child flow ID references in public APIs
- HTTP polling strategy (NOT WebSockets) per Railway deployment constraints

---

## 4. Database Schema Overview

### Core Tables (Migration 112-114)

#### 4.1 `planning_flows` (Migration 112)

Child flow table tracking operational state.

**Key Columns:**

- `id` (UUID): Internal primary key
- `planning_flow_id` (UUID): Frontend-facing identifier (unique)
- `master_flow_id` (UUID): FK to `crewai_flow_state_extensions`
- `client_account_id` (INTEGER): Multi-tenant scoping
- `engagement_id` (INTEGER): Project-level scoping
- `current_phase` (VARCHAR): Phase name (`wave_planning`, `resource_allocation`, `timeline_generation`, `cost_estimation`, `synthesis`, `completed`)
- `phase_status` (VARCHAR): Phase status (`pending`, `in_progress`, `completed`, `failed`)
- **JSONB Columns:**
  - `planning_config`: Planning configuration (max_apps_per_wave, wave_duration_limit_days, etc.)
  - `wave_plan_data`: Wave assignments and metadata
  - `resource_allocation_data`: Resource assignments with AI suggestions
  - `timeline_data`: Gantt chart structure with phases/milestones
  - `cost_estimation_data`: Comprehensive cost breakdown
  - `agent_execution_log`: Agent task history
  - `ui_state`: Frontend display state
  - `validation_errors`: Validation issues
  - `warnings`: Non-blocking warnings
  - `selected_applications`: Array of application UUIDs

**Indexes:**

- Composite: `client_account_id + engagement_id`
- Single: `master_flow_id`, `planning_flow_id`, `current_phase + phase_status`
- GIN (JSONB): `wave_plan_data`, `resource_allocation_data`, `timeline_data`

#### 4.2 `project_timelines` (Migration 113)

Master timeline for Gantt chart visualization.

**Key Columns:**

- `id` (UUID): Primary key
- `planning_flow_id` (UUID): FK to `planning_flows`
- `timeline_name` (VARCHAR): Timeline name
- `overall_start_date` (TIMESTAMP): Timeline start
- `overall_end_date` (TIMESTAMP): Timeline end
- `timeline_status` (VARCHAR): Status (`draft`, `active`, `completed`, `archived`)

#### 4.3 `timeline_phases` (Migration 113)

Individual phases within project timeline.

**Key Columns:**

- `timeline_id` (UUID): FK to `project_timelines`
- `phase_number` (INTEGER): Sequence number
- `phase_name` (VARCHAR): Phase name
- `planned_start_date` (TIMESTAMP): Planned start
- `planned_end_date` (TIMESTAMP): Planned end
- `status` (VARCHAR): Phase status
- `wave_number` (INTEGER): Associated wave number

#### 4.4 `timeline_milestones` (Migration 113)

Key milestones and deliverables.

**Key Columns:**

- `timeline_id` (UUID): FK to `project_timelines`
- `milestone_number` (INTEGER): Sequence number
- `milestone_name` (VARCHAR): Milestone name
- `target_date` (TIMESTAMP): Target completion date
- `status` (VARCHAR): Milestone status
- `description` (TEXT): Milestone description

#### 4.5 `resource_pools` (Migration 114)

Role-based resource capacity and cost tracking.

**Key Columns:**

- `pool_name` (VARCHAR): Pool identifier
- `role_name` (VARCHAR): Role name (per #690: role-based resources)
- `total_capacity_hours` (NUMERIC): Total available hours
- `available_capacity_hours` (NUMERIC): Current available hours
- `allocated_capacity_hours` (NUMERIC): Currently allocated hours
- `hourly_rate` (NUMERIC): Cost per hour
- `utilization_percentage` (NUMERIC): Auto-calculated utilization (trigger)
- `skills` (JSONB): Array of skills for this role

#### 4.6 `resource_allocations` (Migration 114)

Resource assignments to migration waves.

**Key Columns:**

- `planning_flow_id` (UUID): FK to `planning_flows`
- `wave_id` (UUID): FK to `migration_waves`
- `resource_pool_id` (UUID): FK to `resource_pools`
- `allocated_hours` (NUMERIC): Allocated hours
- `allocation_start_date` (TIMESTAMP): Allocation start
- `allocation_end_date` (TIMESTAMP): Allocation end
- `is_ai_suggested` (BOOLEAN): AI-generated recommendation
- `ai_confidence_score` (NUMERIC): Confidence level (0-100)
- `manual_override` (BOOLEAN): User modified AI suggestion
- `status` (VARCHAR): Allocation status

#### 4.7 `resource_skills` (Migration 114)

Skill requirements and gap analysis per wave.

**Key Columns:**

- `wave_id` (UUID): FK to `migration_waves`
- `skill_name` (VARCHAR): Required skill
- `required_hours` (NUMERIC): Hours required
- `available_hours` (NUMERIC): Hours available
- `has_gap` (BOOLEAN): Skill gap exists
- `gap_severity` (VARCHAR): Severity level (`none`, `low`, `medium`, `high`, `critical`)
- `mitigation_plan` (TEXT): Plan to address gap
- `training_required` (BOOLEAN): Training needed
- `external_hire_needed` (BOOLEAN): External hire needed

---

## 5. Planning Flow Phases

The Planning flow progresses through six sequential phases:

### Phase 1: Wave Planning

**Purpose**: Group applications into sequential migration waves based on dependencies, complexity, and business priorities.

**Agent**: `WavePlanningSpecialist` (via `PlanningCrew`)

**Inputs:**

- Selected applications from Assessment flow
- Assessment results (6R strategies, complexity scores)
- Planning configuration (`max_apps_per_wave`, `wave_duration_limit_days`)

**Outputs:**

- Wave assignments (which applications in which wave)
- Wave metadata (names, descriptions, dependencies)
- Saved to `planning_flows.wave_plan_data` (JSONB)

**Backend Implementation:**

- Service: `planning_service.py:196-300` (`execute_wave_planning_phase()`)
- Repository: `planning_flow_repository.py:363-387` (`save_wave_plan_data()`)
- Crew: `planning_crew.py` (`execute_wave_planning()`)

**Frontend Integration:**

- Page: `src/pages/plan/WavePlanning.tsx`
- Component: `src/components/plan/WaveDashboard.tsx`
- API: `planningFlowService.ts:151-170` (`initializePlanningFlow()`)

### Phase 2: Resource Allocation

**Purpose**: Allocate role-based resources to each wave with AI-driven recommendations and manual override capability.

**Agent**: `ResourceAllocationSpecialist` (via `PlanningCrew`)

**Inputs:**

- Wave plan data (from Phase 1)
- Resource pools with capacity and rates
- Planning configuration

**Outputs:**

- Resource allocations per wave
- Skill gap analysis (non-blocking warnings)
- AI confidence scores
- Saved to `planning_flows.resource_allocation_data` (JSONB)
- Relational data in `resource_allocations` and `resource_skills` tables

**Backend Implementation:**

- Service: `planning_service.py:302-447` (`execute_resource_allocation_phase()`)
- Repository: `planning_flow_repository.py:835-1351` (resource CRUD methods)

**Frontend Integration:**

- Page: `src/pages/plan/Resource.tsx`
- API: `planningFlowService.ts:191-213` (`executePlanningPhase()`)

### Phase 3: Timeline Generation

**Purpose**: Generate detailed migration timeline with phases, milestones, dependencies, and Gantt chart visualization.

**Agent**: `TimelinePlanningSpecialist` (via `PlanningCrew`)

**Inputs:**

- Wave plan data
- Resource allocation data
- Planning configuration

**Outputs:**

- Project timeline with overall start/end dates
- Timeline phases linked to waves
- Milestones with target dates
- Gantt chart structure
- Critical path analysis
- Saved to `planning_flows.timeline_data` (JSONB)
- Relational data in `project_timelines`, `timeline_phases`, `timeline_milestones` tables

**Backend Implementation:**

- Service: `planning_service.py:449-539` (`execute_timeline_generation_phase()`)
- Repository: `planning_flow_repository.py:471-829` (timeline CRUD methods)

**Frontend Integration:**

- Page: `src/pages/plan/Timeline.tsx`
- API Endpoint: `/api/v1/plan/roadmap` (lines 17-133 in `plan.py`)

### Phase 4: Cost Estimation

**Purpose**: Calculate comprehensive migration costs including resources, infrastructure, licenses, and contingency.

**Agent**: `CostEstimationSpecialist` (via `PlanningCrew`)

**Inputs:**

- Wave plan data
- Resource allocation data (with hourly rates)
- Timeline data (duration calculations)
- Planning configuration (contingency percentage)

**Outputs:**

- Total estimated cost
- Cost breakdown by wave, category, timeline phase
- Resource cost vs infrastructure cost
- Contingency buffer
- Saved to `planning_flows.cost_estimation_data` (JSONB)

**Backend Implementation:**

- Service: `planning_service.py:541-626` (`execute_cost_estimation_phase()`)
- Repository: `planning_flow_repository.py:441-465` (`save_cost_estimation_data()`)

**Frontend Integration:**

- Dashboard cards on `src/pages/plan/Index.tsx`
- Cost details in export reports

### Phase 5: Synthesis

**Purpose**: Consolidate all planning results into comprehensive planning report with executive summary and recommendations.

**Agent**: None (pure data aggregation)

**Inputs:**

- All completed phase data (wave plan, resources, timeline, costs)

**Outputs:**

- Executive summary with key metrics
- Optimization recommendations
- Comprehensive planning report
- Ready for export (JSON/PDF/Excel)
- Phase status → `completed`

**Backend Implementation:**

- Service: `planning_service.py:628-767` (`execute_synthesis_phase()`)
- Helpers: `planning_service.py:1182-1211` (recommendations generation)

**Frontend Integration:**

- Export functionality via `planningFlowService.ts:310-325` (`exportPlanningData()`)

### Phase 6: Completed

**Purpose**: Final state indicating planning flow completion.

**Triggers:**

- Synthesis phase completes successfully
- `planning_flows.planning_completed_at` timestamp set

**Actions:**

- Planning data available for export
- Ready for handoff to Execute phase (when implemented)

---

## 6. Frontend Architecture

### Key Pages

#### 6.1 Plan Overview (`src/pages/plan/Index.tsx`)

**Purpose**: Dashboard showing planning summary and quick actions.

**Current Status**: Placeholder data (lines 20-36: hard-coded summary cards)

**Features:**

- Summary cards: Waves Planned, Resource Utilization, Target Designs, Planning Progress
- Planning Initialization Wizard (component imported, line 10)
- Quick action links to Timeline, Resource, Target pages
- AI insights panel (placeholder insights, line 32-36)

**TODO:** Replace placeholder data with actual planning flow status polling.

#### 6.2 Wave Planning (`src/pages/plan/WavePlanning.tsx`)

**Purpose**: Main interface for creating and editing migration waves.

**Implementation Status**: ACTIVE (uses `planningFlowService.ts`)

**Features:**

- Wave dashboard component (`WaveDashboard.tsx`, line 17)
- Wave modal for create/edit (`WaveModal.tsx`, line 18)
- API integration with `getPlanningStatus()` (line 58)
- Uses query parameters: `engagement_id`, `planning_flow_id` (lines 26-27)

**Data Flow:**

1. Loads planning data via `planningFlowApi.getPlanningStatus()` (line 58)
2. Extracts waves from `status.wave_plan_data?.waves` (snake_case, line 61)
3. Displays waves in dashboard
4. Supports create/edit/save operations

#### 6.3 Timeline (`src/pages/plan/Timeline.tsx`)

**Purpose**: Detailed timeline view with Gantt chart visualization.

**Current Status**: Placeholder UI (per original 02_Timeline.md)

**TODO:** Integrate with `/api/v1/plan/roadmap` endpoint (which has real data from migration 113).

#### 6.4 Resource (`src/pages/plan/Resource.tsx`)

**Purpose**: Resource allocation and skill gap management.

**Current Status**: Placeholder UI (per original 03_Resource.md)

**TODO:** Integrate with resource allocation API endpoints.

#### 6.5 Target (`src/pages/plan/Target.tsx`)

**Purpose**: Target cloud architecture design.

**Current Status**: Placeholder UI (per original 04_Target.md)

**NOTE:** This may belong to Execute phase rather than Planning phase.

### Key Components

#### 6.6 `PlanningInitializationWizard.tsx`

**Purpose**: Multi-step wizard to initialize planning flow.

**Location**: `src/components/plan/PlanningInitializationWizard.tsx`

**Features:**

- Application selection step
- Planning configuration step (max_apps_per_wave, wave_duration_limit_days, contingency_percentage)
- Calls `planningFlowApi.initializePlanningFlow()` on submission

#### 6.7 `WaveDashboard.tsx`

**Purpose**: Display all waves in card/table view.

**Location**: `src/components/plan/WaveDashboard.tsx`

**Features:**

- Wave cards with summary info
- Create/edit/delete wave actions
- Drag-and-drop support (potential feature)

#### 6.8 `WaveModal.tsx`

**Purpose**: Modal form for creating/editing individual waves.

**Location**: `src/components/plan/WaveModal.tsx`

**Features:**

- Wave name, description, status
- Application selection for wave
- Start/end date pickers
- Dependency selection

### API Client

#### 6.9 `planningFlowService.ts`

**Location**: `src/lib/api/planningFlowService.ts`

**Purpose**: TypeScript API client for Planning Flow endpoints.

**Key Methods:**

- `initializePlanningFlow(request)` (lines 152-170)
- `executePlanningPhase(planning_flow_id, phase)` (lines 192-213)
- `getPlanningStatus(planning_flow_id)` (lines 230-241)
- `updateWavePlan(planning_flow_id, wave_plan_data)` (lines 271-290)
- `exportPlanningData(planning_flow_id, format)` (lines 310-325)

**Field Naming Convention:** ALL fields use `snake_case` (per CLAUDE.md) - NO transformation layer.

**Request Pattern:** POST/PUT use request body, GET uses query parameters (per API_REQUEST_PATTERNS.md).

---

## 7. Backend Architecture

### 7.1 Service Layer (`planning_service.py`)

**Location**: `backend/app/services/planning_service.py`

**Purpose**: Business logic orchestration for planning flow.

**Key Methods:**

| Method                               | Lines       | Purpose                                      |
|--------------------------------------|-------------|----------------------------------------------|
| `initialize_planning_flow()`         | 81-190      | Create new planning flow from assessment     |
| `execute_wave_planning_phase()`      | 196-300     | Execute wave planning agent                  |
| `execute_resource_allocation_phase()`| 302-447     | Execute resource allocation agent            |
| `execute_timeline_generation_phase()`| 449-539     | Execute timeline generation agent            |
| `execute_cost_estimation_phase()`    | 541-626     | Execute cost estimation agent                |
| `execute_synthesis_phase()`          | 628-767     | Synthesize planning report                   |
| `get_planning_status()`              | 773-857     | Get current planning flow status             |
| `update_wave_plan()`                 | 859-918     | Update wave plan with manual changes         |
| `validate_planning_config()`         | 924-1012    | Validate planning configuration              |
| `calculate_wave_capacity()`          | 1014-1105   | Calculate resource utilization and warnings  |

**Transaction Management:** Uses async context managers for atomic operations (e.g., line 146: `async with self.db.begin()`).

**Agent Integration:** Delegates to `PlanningCrew` for CrewAI agent execution (lines 261-266, 392-399, etc.).

### 7.2 Repository Layer (`planning_flow_repository.py`)

**Location**: `backend/app/repositories/planning_flow_repository.py`

**Purpose**: Data access layer with multi-tenant scoping.

**Architecture:** Extends `ContextAwareRepository[PlanningFlow]` (line 50) for automatic tenant filtering.

**Key Method Categories:**

| Category                  | Lines        | Methods                                          |
|---------------------------|--------------|--------------------------------------------------|
| PlanningFlow CRUD         | 82-324       | create, get_by_id, get_by_master_flow_id, update, delete |
| Phase Management          | 326-357      | update_phase_status                              |
| JSONB Data Updates        | 359-465      | save_wave_plan_data, save_resource_allocation_data, save_timeline_data, save_cost_estimation_data |
| Timeline CRUD             | 467-626      | create_timeline, get_timeline_by_planning_flow, update_timeline |
| Timeline Phase Operations | 628-728      | create_timeline_phase, get_phases_by_timeline    |
| Timeline Milestone Ops    | 730-829      | create_milestone, get_milestones_by_timeline     |
| Resource Pool CRUD        | 831-1020     | create_resource_pool, list_resource_pools, get_by_id, update |
| Resource Allocation CRUD  | 1022-1224    | create_allocation, list_by_wave, list_by_planning_flow, update |
| Resource Skills Ops       | 1226-1351    | create_skill, list_skills_by_wave, list_skill_gaps_by_wave |

**Tenant Scoping:** ALL queries automatically filter by `client_account_id` and `engagement_id` (initialized in constructor, lines 58-76).

### 7.3 API Endpoints

#### `/api/v1/wave_planning/*` (`wave_planning.py`)

**Location**: `backend/app/api/v1/endpoints/wave_planning.py`

**Purpose**: Wave planning API endpoints (currently hybrid real/placeholder).

**Endpoints:**

| Method | Route      | Lines   | Status       | Description                          |
|--------|------------|---------|--------------|--------------------------------------|
| GET    | `/`        | 17-61   | REAL DATA    | Get wave planning data via repository |
| PUT    | `/`        | 64-72   | PLACEHOLDER  | Update wave planning (stub)          |
| GET    | `/roadmap` | 75-149  | PLACEHOLDER  | Get roadmap with phases (hard-coded) |
| PUT    | `/roadmap` | 152-160 | PLACEHOLDER  | Update roadmap (stub)                |

**Real Data Implementation (GET `/`):**

- Initializes `PlanningFlowRepository` with tenant scoping (lines 32-37)
- Queries `planning_flows` table via `repository.get_all()` (line 40)
- Returns empty state if no planning flow exists (lines 43-49)
- Returns actual wave data from `wave_plan_data` JSONB column (line 55)

#### `/api/v1/plan/*` (`plan.py`)

**Location**: `backend/app/api/v1/endpoints/plan.py`

**Purpose**: Plan overview and timeline endpoints.

**Endpoints:**

| Method | Route         | Lines    | Status               | Description                              |
|--------|---------------|----------|----------------------|------------------------------------------|
| GET    | `/roadmap`    | 17-133   | REAL DATA (partial)  | Get migration roadmap with timeline      |
| PUT    | `/roadmap`    | 136-144  | PLACEHOLDER          | Update roadmap (stub)                    |
| GET    | `/`           | 147-181  | PLACEHOLDER          | Get plan overview (hard-coded)           |
| GET    | `/waveplanning`| 184-221 | PLACEHOLDER          | Get wave planning (hard-coded)           |
| PUT    | `/waveplanning`| 224-232 | PLACEHOLDER          | Update wave planning (stub)              |
| GET    | `/timeline`   | 235-384  | PLACEHOLDER          | Get detailed timeline (hard-coded)       |

**Real Data Implementation (GET `/roadmap`):**

- Queries `project_timelines` table directly (lines 54-67)
- Fetches timeline phases via repository (lines 81-85)
- Fetches timeline milestones via repository (lines 88-92)
- Returns structured timeline data from migration 113 tables (lines 94-133)

### 7.4 CrewAI Integration

**Crew Definition:** `PlanningCrew` (location inferred, not provided)

**Agent Specialists:**

1. **WavePlanningSpecialist**: Groups applications into waves
2. **ResourceAllocationSpecialist**: Allocates resources to waves
3. **TimelinePlanningSpecialist**: Generates project timeline
4. **CostEstimationSpecialist**: Calculates migration costs

**Execution Pattern:**

- Service layer calls crew methods (e.g., `planning_crew.execute_wave_planning()`, line 261)
- Crew orchestrates agents with tenant-scoped context
- Results returned as structured dictionaries
- Service layer persists results to JSONB columns

**Memory Configuration:** CrewAI built-in memory is DISABLED per ADR-024. Use `TenantMemoryManager` for agent learning.

---

## 8. End-to-End Flow Sequence: Complete Planning Workflow

### Scenario: User completes Assessment and initiates Planning

#### Step 1: Planning Initialization

1. **User Action:** Clicks "Start Planning" button on Plan Overview page (`Index.tsx`, line 58)
2. **Frontend:** Opens `PlanningInitializationWizard` modal (line 14 state)
3. **User Input:**
   - Selects applications to include in planning (from Assessment results)
   - Configures planning parameters:
     - Max apps per wave: 5
     - Wave duration limit: 90 days
     - Contingency percentage: 15%
4. **Frontend API Call:** `planningFlowApi.initializePlanningFlow()` (line 152)
   - **Method:** `POST`
   - **Endpoint:** `/api/v1/master-flows/planning/initialize`
   - **Body:**
     ```json
     {
       "engagement_id": 1,
       "selected_application_ids": ["uuid1", "uuid2", "uuid3"],
       "planning_config": {
         "max_apps_per_wave": 5,
         "wave_duration_limit_days": 90,
         "contingency_percentage": 15
       }
     }
     ```

#### Step 2: Backend Processing (Initialization)

5. **Backend Route:** Planning API endpoint (not yet implemented - TODO)
6. **Service Layer:** `planning_service.initialize_planning_flow()` (line 81)
   - Validates planning configuration (line 127)
   - Validates selected applications exist (line 131-137)
   - Creates `PlanningFlow` instance (lines 147-169)
     - `current_phase`: `"wave_planning"`
     - `phase_status`: `"ready"`
     - Stores `planning_config` and `selected_applications` in JSONB
7. **Database Transaction:** Creates row in `planning_flows` table (line 172)
8. **Backend Response:**
   ```json
   {
     "master_flow_id": "uuid-master",
     "planning_flow_id": "uuid-planning",
     "current_phase": "wave_planning",
     "phase_status": "ready",
     "status": "success"
   }
   ```

#### Step 3: Wave Planning Phase Execution

9. **Frontend:** Redirects to Wave Planning page (`WavePlanning.tsx`)
10. **User Action:** Clicks "Generate Waves" button
11. **Frontend API Call:** `planningFlowApi.executePlanningPhase(planning_flow_id, 'wave_planning')` (line 192)
    - **Method:** `POST`
    - **Endpoint:** `/api/v1/master-flows/planning/execute-phase`
    - **Body:**
      ```json
      {
        "planning_flow_id": "uuid-planning",
        "phase": "wave_planning",
        "manual_override": false
      }
      ```

12. **Backend Processing:**
    - Service: `execute_wave_planning_phase()` (line 196)
    - Fetches planning flow with tenant scoping (line 241)
    - Validates current phase is `"wave_planning"` (line 244-249)
    - Updates phase status to `"running"` (line 252)
    - Invokes `WavePlanningSpecialist` agent via `PlanningCrew` (lines 256-266)
      - Agent analyzes application dependencies, complexity, 6R strategies
      - Groups applications into 3-5 waves
      - Assigns wave names, descriptions, dependencies
    - Saves wave plan results to `wave_plan_data` JSONB (line 269)
    - Logs agent execution (lines 270-278)
    - Transitions to `"resource_allocation"` phase (lines 281-282)

13. **Backend Response:**
    ```json
    {
      "waves": [
        {
          "wave_number": 1,
          "wave_name": "Wave 1 - Quick Wins",
          "applications": ["uuid1", "uuid2"],
          "start_date": "2025-01-01",
          "end_date": "2025-03-31",
          "dependencies": [],
          "status": "planned"
        },
        {
          "wave_number": 2,
          "wave_name": "Wave 2 - Core Systems",
          "applications": ["uuid3"],
          "start_date": "2025-04-01",
          "end_date": "2025-06-30",
          "dependencies": [1],
          "status": "planned"
        }
      ],
      "total_waves": 2,
      "planning_metadata": {...}
    }
    ```

#### Step 4: Resource Allocation Phase

14. **Frontend:** Polls `/master-flows/planning/status/{flow_id}` (every 5 seconds)
15. **User Action:** Reviews resource allocation suggestions, clicks "Confirm Resources"
16. **Backend Processing:**
    - Service: `execute_resource_allocation_phase()` (line 302)
    - Validates wave plan exists (line 375-379)
    - Invokes `ResourceAllocationSpecialist` agent (lines 392-399)
      - Agent analyzes wave complexity and duration
      - Suggests role-based resource allocations (Cloud Architect, DevOps Engineer, QA Engineer)
      - Calculates required hours and costs
      - Identifies skill gaps
    - Saves allocation results to `resource_allocation_data` JSONB (line 405)
    - Creates rows in `resource_allocations` and `resource_skills` tables
    - Adds skill gap warnings (lines 418-424)
    - Transitions to `"timeline_generation"` phase (lines 428-429)

17. **Backend Response:**
    ```json
    {
      "allocations": [
        {
          "wave_id": "uuid-wave1",
          "wave_number": 1,
          "resources": [
            {
              "role_name": "Cloud Architect",
              "allocated_hours": 160,
              "hourly_rate": 150.0,
              "estimated_cost": 24000.0,
              "is_ai_suggested": true,
              "ai_confidence_score": 0.85
            }
          ]
        }
      ],
      "skill_gaps": [
        {
          "skill_name": "Kubernetes",
          "severity": "medium",
          "impact": "May require external training"
        }
      ],
      "total_cost_estimate": 125000.0
    }
    ```

#### Step 5: Timeline Generation Phase

18. **Frontend:** Automatically triggers timeline generation
19. **Backend Processing:**
    - Service: `execute_timeline_generation_phase()` (line 449)
    - Invokes `TimelinePlanningSpecialist` agent (lines 502-508)
      - Agent generates project timeline with start/end dates
      - Creates timeline phases for each wave
      - Defines key milestones (Planning Complete, Wave 1 Migration Start, etc.)
      - Performs critical path analysis
    - Saves timeline results to `timeline_data` JSONB (line 511)
    - Creates rows in `project_timelines`, `timeline_phases`, `timeline_milestones` tables
    - Transitions to `"cost_estimation"` phase (lines 522-523)

20. **Backend Response:**
    ```json
    {
      "timeline_id": "uuid-timeline",
      "timeline_name": "Migration Timeline - Engagement 1",
      "overall_start_date": "2025-01-01T00:00:00Z",
      "overall_end_date": "2025-06-30T23:59:59Z",
      "phases": [
        {
          "id": "uuid-phase1",
          "phase_name": "Wave 1 Planning",
          "planned_start_date": "2025-01-01T00:00:00Z",
          "planned_end_date": "2025-01-31T23:59:59Z",
          "status": "in_progress",
          "wave_number": 1
        }
      ],
      "milestones": [
        {
          "id": "uuid-milestone1",
          "milestone_name": "Wave 1 Go-Live",
          "target_date": "2025-03-31T00:00:00Z",
          "status": "pending",
          "description": "All Wave 1 applications live in production"
        }
      ],
      "roadmap_status": "active"
    }
    ```

#### Step 6: Cost Estimation Phase

21. **Frontend:** Automatically triggers cost estimation
22. **Backend Processing:**
    - Service: `execute_cost_estimation_phase()` (line 541)
    - Invokes `CostEstimationSpecialist` agent (lines 586-593)
      - Aggregates resource costs from resource_allocation_data
      - Calculates infrastructure costs (compute, storage, network)
      - Adds license and third-party service costs
      - Applies contingency buffer (15%)
      - Generates cost breakdown by wave, category, timeline phase
    - Saves cost estimation to `cost_estimation_data` JSONB (line 596)
    - Transitions to `"synthesis"` phase (lines 607-608)

23. **Backend Response:**
    ```json
    {
      "total_estimated_cost": 187500.0,
      "cost_breakdown": {
        "resource_costs": 125000.0,
        "infrastructure_costs": 37500.0,
        "license_costs": 6250.0,
        "contingency": 18750.0
      },
      "cost_by_wave": [
        {
          "wave_number": 1,
          "estimated_cost": 75000.0
        },
        {
          "wave_number": 2,
          "estimated_cost": 112500.0
        }
      ]
    }
    ```

#### Step 7: Synthesis Phase

24. **Frontend:** Automatically triggers synthesis
25. **Backend Processing:**
    - Service: `execute_synthesis_phase()` (line 628)
    - Validates all phases completed (lines 678-692)
    - Generates executive summary (lines 699-715)
    - Generates optimization recommendations (line 720)
    - Calculates key metrics (lines 721-734)
    - Marks flow completed (lines 738-742)
      - `current_phase`: `"completed"`
      - `phase_status`: `"completed"`
      - `planning_completed_at`: timestamp

26. **Backend Response:**
    ```json
    {
      "executive_summary": {
        "total_applications": 3,
        "total_waves": 2,
        "total_duration_days": 180,
        "total_cost": 187500.0,
        "resource_count": 6,
        "skill_gaps_identified": 1
      },
      "wave_plan": {...},
      "resource_allocation": {...},
      "timeline": {...},
      "cost_estimation": {...},
      "recommendations": [
        "Address 1 skill gaps through training or external hiring",
        "Consider phased approach to spread costs over multiple budget cycles"
      ],
      "key_metrics": {
        "avg_cost_per_app": 62500.0,
        "avg_duration_per_wave": 90
      },
      "generated_at": "2025-10-29T15:30:00Z"
    }
    ```

#### Step 8: Export Planning Report

27. **User Action:** Clicks "Export Planning Report" button
28. **Frontend API Call:** `planningFlowApi.exportPlanningData(planning_flow_id, 'pdf')` (line 310)
29. **Backend Processing:**
    - Fetches completed planning flow
    - Generates PDF report with all planning data
    - Returns PDF file or download URL
30. **Frontend:** Initiates PDF download

---

## 9. Troubleshooting Breakpoints

| Breakpoint                                  | Diagnostic Check                                                                                     | Platform-Specific Fix                                                                                                                      |
|---------------------------------------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **Planning initialization fails (422)**     | Check request body structure. Must use `snake_case` field names.                                     | Verify `InitializePlanningFlowRequest` interface matches backend Pydantic model. Check network tab for actual payload sent.              |
| **Planning initialization fails (403)**     | Check multi-tenant headers: `x-client-account-id`, `x-engagement-id`.                                | Ensure `get_current_context()` middleware is enabled. Verify headers in browser DevTools Network tab.                                    |
| **Wave planning phase stuck**               | Check agent execution log in `planning_flows.agent_execution_log` JSONB.                             | Query: `SELECT agent_execution_log FROM migration.planning_flows WHERE planning_flow_id = 'uuid';` Look for agent errors.                |
| **Wave plan data empty**                    | Check `planning_flows.wave_plan_data` JSONB column.                                                  | Query: `SELECT wave_plan_data FROM migration.planning_flows WHERE planning_flow_id = 'uuid';` May indicate agent failure.                |
| **Resource allocation fails (validation)**  | Check if wave plan exists. Cannot allocate resources without completed wave plan.                    | Ensure `current_phase` is `"resource_allocation"` and `wave_plan_data` is not empty.                                                      |
| **Timeline generation fails**               | Check if resource allocation completed. Timeline depends on resource data.                           | Ensure `current_phase` is `"timeline_generation"` and `resource_allocation_data` is not empty.                                            |
| **Timeline phases not visible**             | Check `project_timelines`, `timeline_phases`, `timeline_milestones` tables.                          | Query: `SELECT * FROM migration.project_timelines WHERE planning_flow_id = 'uuid';` Verify foreign key relationships.                    |
| **Cost estimation incorrect**               | Check resource allocation hourly rates. Verify contingency percentage applied.                       | Query: `SELECT cost_estimation_data FROM migration.planning_flows WHERE planning_flow_id = 'uuid';` Verify calculation logic.            |
| **Synthesis phase fails**                   | Check if ALL previous phases completed. Synthesis requires all data.                                 | Query: `SELECT current_phase, wave_plan_data, resource_allocation_data, timeline_data, cost_estimation_data FROM migration.planning_flows WHERE planning_flow_id = 'uuid';` |
| **Export fails (404)**                      | Check if planning flow completed. Export only available after synthesis.                             | Ensure `current_phase` is `"completed"` and `planning_completed_at` timestamp is set.                                                    |
| **Polling shows stale data**                | Check frontend polling interval. May need to increase/decrease frequency.                            | Default is 5 seconds for `running` status. Check `WavePlanning.tsx` or dashboard for polling logic.                                      |
| **Master flow not found (404)**             | Check `crewai_flow_state_extensions` table. Master flow may have been deleted.                       | Query: `SELECT * FROM migration.crewai_flow_state_extensions WHERE flow_id = 'master-flow-uuid';` Verify FK constraint.                  |
| **Child flow not found (404)**              | Check `planning_flows` table with tenant scoping.                                                    | Query: `SELECT * FROM migration.planning_flows WHERE planning_flow_id = 'uuid' AND client_account_id = 1 AND engagement_id = 1;`         |
| **Skill gap warnings not displayed**        | Check `resource_allocation_data.skill_gaps` array and `warnings` JSONB column.                       | Query: `SELECT warnings, resource_allocation_data->'skill_gaps' FROM migration.planning_flows WHERE planning_flow_id = 'uuid';`          |
| **Utilization percentage incorrect**        | Check `resource_pools.utilization_percentage`. Auto-calculated via trigger.                          | Query: `SELECT role_name, total_capacity_hours, allocated_capacity_hours, utilization_percentage FROM migration.resource_pools WHERE client_account_id = 1;` |
| **Planning config not applied**             | Check `planning_flows.planning_config` JSONB column.                                                 | Query: `SELECT planning_config FROM migration.planning_flows WHERE planning_flow_id = 'uuid';` Verify values match user input.           |

---

## 10. Directory Structure

The documentation for the Planning flow is organized as follows:

- **`00_Planning_Flow_Summary.md`**: This file (comprehensive overview).
- **`01_Overview.md`**: Plan overview page and initialization wizard.
- **`02_Timeline.md`**: Timeline generation and Gantt chart visualization.
- **`03_Resource.md`**: Resource allocation and skill gap management.
- **`04_Target.md`**: Target cloud architecture design (may belong to Execute phase).

---

## 11. Key Architectural Patterns

### 11.1 Two-Table Pattern (ADR-012)

- **Master Flow** (`crewai_flow_state_extensions`): High-level lifecycle (`running`, `paused`, `completed`)
- **Child Flow** (`planning_flows`): Operational state (phases, wave data, resource allocations)
- **Relationship**: One-to-one via `master_flow_id` foreign key
- **Benefits**: Separation of concerns, UI can query child for operational decisions, MFO queries master for lifecycle

### 11.2 JSONB Storage Strategy

- **Purpose**: Flexible schema for planning data that evolves over time
- **Indexed**: GIN indexes on `wave_plan_data`, `resource_allocation_data`, `timeline_data` for fast queries
- **Hybrid Approach**: Complex relational data (timelines, resource pools) also stored in normalized tables for querying
- **Tradeoff**: JSONB for agent output (schema flexibility), relational tables for UI queries (performance)

### 11.3 Multi-Tenant Scoping

- **Mandatory Fields**: `client_account_id` (organization) + `engagement_id` (project)
- **Repository Pattern**: `ContextAwareRepository` automatically filters ALL queries by tenant
- **Security**: Prevents data leakage across organizations
- **Performance**: Composite indexes on `(client_account_id, engagement_id)` for fast filtering

### 11.4 Phase Progression

- **Sequential**: Phases must complete in order (wave → resource → timeline → cost → synthesis)
- **Validation**: Each phase validates prerequisites before execution
- **Non-Blocking Warnings**: Skill gaps and capacity warnings don't block progression
- **Manual Override**: Users can modify AI suggestions at any phase

### 11.5 Agent Integration

- **Crew Pattern**: `PlanningCrew` orchestrates multiple specialist agents
- **Memory Disabled**: CrewAI built-in memory disabled per ADR-024 (use `TenantMemoryManager` instead)
- **Tenant Context**: Agents receive `client_account_id` and `engagement_id` for tenant-scoped learning
- **Result Persistence**: Agent outputs saved to JSONB columns + relational tables

---

## 12. Gap Analysis and TODOs

### 12.1 Missing MFO Endpoints

**Problem:** Planning flow endpoints are defined in `planningFlowService.ts` but not implemented in backend.

**Expected Endpoints (Not Found):**

- `POST /api/v1/master-flows/planning/initialize`
- `POST /api/v1/master-flows/planning/execute-phase`
- `GET /api/v1/master-flows/planning/status/{flow_id}`
- `PUT /api/v1/master-flows/planning/update-wave-plan`
- `GET /api/v1/master-flows/planning/export/{flow_id}`

**TODO:** Create `backend/app/api/v1/endpoints/planning_flow.py` with these endpoints, integrate with `planning_service.py`.

### 12.2 Frontend Placeholder Data

**Affected Files:**

- `src/pages/plan/Index.tsx` (lines 20-36: hard-coded summary cards)
- `src/pages/plan/Timeline.tsx` (entire file - no API integration)
- `src/pages/plan/Resource.tsx` (entire file - no API integration)
- `src/pages/plan/Target.tsx` (entire file - no API integration)

**TODO:** Replace placeholder data with actual API polling to planning flow status endpoint.

### 12.3 Export Functionality

**Problem:** Export endpoint defined in API client (`exportPlanningData()`) but no backend implementation found.

**TODO:** Implement export service that:

- Queries completed planning flow
- Generates PDF report using template engine (e.g., `reportlab`, `weasyprint`)
- Generates Excel export using `openpyxl`
- Returns JSON export (already available via status endpoint)

### 12.4 PlanningCrew Implementation

**Problem:** `PlanningCrew` class imported in `planning_service.py` (line 34) but implementation not provided.

**TODO:** Create `backend/app/services/crewai_flows/crews/planning_crew.py` with:

- `execute_wave_planning()` method
- `execute_resource_allocation()` method
- `execute_timeline_generation()` method
- `execute_cost_estimation()` method
- Agent definitions for each specialist

### 12.5 Migration Waves Table

**Problem:** `resource_allocations` and `resource_skills` tables reference `wave_id` FK to `migration.migration_waves` table, but this table is not defined in migrations 112-114.

**TODO:** Check if `migration_waves` table exists from earlier migration. If not, create migration to define it with:

- `wave_number` (INTEGER)
- `wave_name` (VARCHAR)
- `planning_flow_id` (UUID FK)
- `client_account_id` (INTEGER)
- `engagement_id` (INTEGER)

### 12.6 Timeline Phase 113

**Problem:** Documentation references migration 113 (`create_timeline_tables.py`) but file was not provided in analysis.

**TODO:** Verify migration 113 exists in `backend/alembic/versions/` with tables:

- `project_timelines`
- `timeline_phases`
- `timeline_milestones`

### 12.7 Target Architecture Placement

**Problem:** `04_Target.md` discusses target cloud architecture design, but this may belong to Execute phase rather than Planning phase.

**Decision Needed:** Should target architecture be:

- **Option A:** Part of Planning (design before execution)
- **Option B:** Part of Execute (design during migration)
- **Option C:** Separate Architecture phase

---

## 13. Related Documentation

- **ADR-006:** Master Flow Orchestrator (`/docs/adr/006-master-flow-orchestrator.md`)
- **ADR-012:** Flow Status Management Separation (`/docs/adr/012-flow-status-management-separation.md`)
- **ADR-024:** TenantMemoryManager Architecture (`/docs/adr/024-tenant-memory-manager-architecture.md`)
- **API Request Patterns:** `/docs/guidelines/API_REQUEST_PATTERNS.md`
- **Architectural Review Guidelines:** `/docs/guidelines/ARCHITECTURAL_REVIEW_GUIDELINES.md`
- **Collection Flow Summary:** `/docs/e2e-flows/02_Collection/00_Collection_Flow_Summary.md` (reference template)
- **Coding Agent Guide:** `/docs/analysis/Notes/coding-agent-guide.md`

---

## 14. Summary

The Planning flow is a **comprehensive, AI-driven workflow** that transforms assessment results into actionable migration plans. It leverages the **Master Flow Orchestrator** architecture for lifecycle management, uses **CrewAI agents** for intelligent recommendations, and stores data in a **hybrid JSONB + relational schema** for flexibility and performance.

**Current Implementation Status (October 2025):**

- Database schema: COMPLETE (migrations 112, 113, 114)
- Repository layer: COMPLETE (1351 lines, comprehensive)
- Service layer: COMPLETE (1212 lines, all phases implemented)
- Backend API: PARTIAL (some endpoints placeholder, MFO endpoints missing)
- Frontend API client: COMPLETE (346 lines, full type safety)
- Frontend UI: PARTIAL (wizard + wave dashboard complete, other pages placeholder)
- Agent integration: PENDING (PlanningCrew implementation not provided)

**Next Steps:**

1. Implement missing MFO endpoints (`/api/v1/master-flows/planning/*`)
2. Create `PlanningCrew` class with agent specialists
3. Replace frontend placeholder data with actual API polling
4. Implement export functionality (PDF/Excel)
5. Verify migration 113 exists and is complete
6. Create/verify `migration_waves` table
7. Decide on target architecture placement (Planning vs Execute vs separate phase)

**Documentation Quality:** This document follows the comprehensive style of Collection flow documentation (`00_Collection_Flow_Summary.md`) with detailed API tables, file path references with line numbers, end-to-end flow sequences, and troubleshooting breakpoints.
