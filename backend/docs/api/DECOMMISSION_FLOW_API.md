# Decommission Flow API Documentation

**Version**: 1.0
**Base Path**: `/api/v1/decommission-flow`
**Authentication**: Required (Bearer token + X-Engagement-ID header)

## Overview

The Decommission Flow API provides a comprehensive system for safely decommissioning legacy systems after cloud migration. It follows the Master Flow Orchestrator (MFO) pattern per ADR-006, using a two-table architecture for atomic state management.

**Key Features:**
- Safe system retirement with dependency analysis
- Data preservation and archival management
- Cost savings tracking and compliance monitoring
- Multi-phase execution with pause/resume capability
- Support for pre-migration (6R="Retire") and post-migration systems

## Architecture

### Two-Table Pattern (ADR-006)
1. **Master Flow** (`crewai_flow_state_extensions`): Lifecycle management (running/paused/completed)
2. **Child Flow** (`decommission_flows`): Operational state, phase progress, metrics

### Flow Phases (ADR-027)
| Phase | Description | Key Activities |
|-------|-------------|----------------|
| `decommission_planning` | Analysis and planning | Dependency analysis, risk assessment, cost estimation |
| `data_migration` | Data preservation | Data retention policies, archival jobs, backup verification |
| `system_shutdown` | System retirement | Pre-shutdown validation, shutdown execution, post-validation |

## API Endpoints

### 1. Initialize Decommission Flow

Create a new decommission flow for selected systems.

**Endpoint**: `POST /initialize`

**Request Headers:**
```http
Authorization: Bearer <token>
X-Engagement-ID: <engagement-uuid>
Content-Type: application/json
```

**Request Body:**
```json
{
  "selected_system_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "flow_name": "Q1 2025 Legacy System Retirement",
  "decommission_strategy": {
    "priority": "cost_savings",
    "execution_mode": "phased",
    "rollback_enabled": true,
    "stakeholder_approvals": ["IT Manager", "Security Officer"]
  }
}
```

**Request Schema:**
```typescript
{
  selected_system_ids: string[];     // 1-100 UUIDs (REQUIRED)
  flow_name?: string;                // Optional flow name (max 255 chars)
  decommission_strategy?: {
    priority: "cost_savings" | "risk_reduction" | "compliance";
    execution_mode: "immediate" | "scheduled" | "phased";
    rollback_enabled: boolean;
    stakeholder_approvals?: string[];
  }
}
```

**Response (200 OK):**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initialized",
  "current_phase": "decommission_planning",
  "next_phase": "data_migration",
  "selected_systems": [
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "7c9e6679-7425-40de-944b-e07fc1f90ae7"
  ],
  "message": "Decommission flow initialized for 2 systems"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid system IDs or validation errors
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Engagement not found
- `500 Internal Server Error`: Flow creation failed

---

### 2. Get Flow Status

Retrieve current status and progress of a decommission flow.

**Endpoint**: `GET /{flow_id}/status`

**Request Headers:**
```http
Authorization: Bearer <token>
X-Engagement-ID: <engagement-uuid>
```

**Response (200 OK):**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "master_flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "decommission_planning",
  "current_phase": "decommission_planning",
  "system_count": 2,
  "phase_progress": {
    "decommission_planning": "in_progress",
    "data_migration": "pending",
    "system_shutdown": "pending"
  },
  "metrics": {
    "systems_decommissioned": 0,
    "estimated_savings": 120000.00,
    "compliance_score": 85.5
  },
  "runtime_state": {
    "current_agent": "dependency_analyzer",
    "pending_approvals": [],
    "warnings": []
  },
  "created_at": "2025-01-05T10:30:00Z",
  "updated_at": "2025-01-05T11:45:00Z",
  "decommission_complete": false
}
```

**Response Schema:**
```typescript
{
  flow_id: string;
  master_flow_id: string;
  status: string;                    // Current operational status
  current_phase: string;             // Current phase name
  system_count: number;              // Number of systems
  phase_progress: {
    decommission_planning: "pending" | "in_progress" | "completed" | "failed";
    data_migration: "pending" | "in_progress" | "completed" | "failed";
    system_shutdown: "pending" | "in_progress" | "completed" | "failed";
  };
  metrics: {
    systems_decommissioned: number;
    estimated_savings: number;
    compliance_score: number;
  };
  runtime_state: Record<string, any>;
  created_at: string;                // ISO 8601 timestamp
  updated_at: string;                // ISO 8601 timestamp
  decommission_complete: boolean;
}
```

**Error Responses:**
- `404 Not Found`: Flow not found
- `401 Unauthorized`: Missing or invalid authentication
- `500 Internal Server Error`: Status retrieval failed

---

### 3. Resume Flow

Resume a paused decommission flow from a specific phase.

**Endpoint**: `POST /{flow_id}/resume`

**Request Headers:**
```http
Authorization: Bearer <token>
X-Engagement-ID: <engagement-uuid>
Content-Type: application/json
```

**Request Body:**
```json
{
  "phase": "data_migration",
  "user_input": {
    "approved_by": "admin@example.com",
    "approval_notes": "Proceed with data archival"
  }
}
```

**Request Schema:**
```typescript
{
  phase?: "decommission_planning" | "data_migration" | "system_shutdown";
  user_input?: Record<string, any>;
}
```

**Response (200 OK):**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "current_phase": "data_migration",
  "next_phase": "system_shutdown",
  "selected_systems": [
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "message": "Decommission flow resumed from data_migration"
}
```

**Error Responses:**
- `400 Bad Request`: Flow already completed or invalid phase
- `404 Not Found`: Flow not found
- `401 Unauthorized`: Missing or invalid authentication
- `500 Internal Server Error`: Resume operation failed

---

### 4. Pause Flow

Pause a running decommission flow.

**Endpoint**: `POST /{flow_id}/pause`

**Request Headers:**
```http
Authorization: Bearer <token>
X-Engagement-ID: <engagement-uuid>
```

**Response (200 OK):**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "paused",
  "current_phase": "data_migration",
  "message": "Decommission flow paused at data_migration"
}
```

**Error Responses:**
- `404 Not Found`: Flow not found
- `401 Unauthorized`: Missing or invalid authentication
- `500 Internal Server Error`: Pause operation failed

---

### 5. Cancel Flow

Cancel a decommission flow (marks as failed/deleted).

**Endpoint**: `POST /{flow_id}/cancel`

**Request Headers:**
```http
Authorization: Bearer <token>
X-Engagement-ID: <engagement-uuid>
```

**Response (200 OK):**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "message": "Decommission flow cancelled successfully"
}
```

**Error Responses:**
- `404 Not Found`: Flow not found
- `401 Unauthorized`: Missing or invalid authentication
- `500 Internal Server Error`: Cancel operation failed

---

## Data Models

### DecommissionFlow (Child Flow)

**Database Table**: `migration.decommission_flows`

**Key Columns:**
```sql
flow_id              UUID PRIMARY KEY
master_flow_id       UUID REFERENCES crewai_flow_state_extensions(flow_id)
client_account_id    UUID REFERENCES client_accounts(id)
engagement_id        UUID REFERENCES engagements(id)
flow_name            VARCHAR(255)
status               VARCHAR(50) CHECK (status IN ('initialized', 'decommission_planning', ...))
current_phase        VARCHAR(50) CHECK (current_phase IN ('decommission_planning', ...))
selected_system_ids  UUID[]
system_count         INTEGER
decommission_strategy JSONB
runtime_state        JSONB
metrics              JSONB
compliance_score     NUMERIC(5,2) CHECK (compliance_score >= 0 AND compliance_score <= 100)
created_at           TIMESTAMP WITH TIME ZONE
updated_at           TIMESTAMP WITH TIME ZONE
```

### Phase Status Fields

Each phase has a dedicated status column:
- `decommission_planning_status`: `pending` | `in_progress` | `completed` | `failed`
- `data_migration_status`: `pending` | `in_progress` | `completed` | `failed`
- `system_shutdown_status`: `pending` | `in_progress` | `completed` | `failed`

---

## Multi-Tenancy & Security

### Required Scoping
All queries MUST include:
- `client_account_id`: Organization isolation
- `engagement_id`: Project/session isolation

### Authentication
- **Bearer Token**: Required in `Authorization` header
- **X-Engagement-ID**: Required header for engagement context

### Data Isolation
Database queries automatically filter by tenant scope:
```python
# Example query pattern
flow = await db.query(DecommissionFlow).filter(
    DecommissionFlow.flow_id == flow_id,
    DecommissionFlow.client_account_id == client_account_id,
    DecommissionFlow.engagement_id == engagement_id
).first()
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes
- `200 OK`: Success
- `400 Bad Request`: Validation errors, invalid input
- `401 Unauthorized`: Authentication failure
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side failures

---

## Usage Examples

### Complete Flow Lifecycle

```bash
# 1. Initialize decommission flow
curl -X POST "https://api.example.com/api/v1/decommission-flow/initialize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_system_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "flow_name": "Legacy System Retirement",
    "decommission_strategy": {
      "priority": "cost_savings",
      "execution_mode": "phased",
      "rollback_enabled": true
    }
  }'

# Response: { "flow_id": "...", "status": "initialized", ... }

# 2. Poll for status (every 5s while active)
curl -X GET "https://api.example.com/api/v1/decommission-flow/$FLOW_ID/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID"

# 3. Pause if needed
curl -X POST "https://api.example.com/api/v1/decommission-flow/$FLOW_ID/pause" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID"

# 4. Resume from specific phase
curl -X POST "https://api.example.com/api/v1/decommission-flow/$FLOW_ID/resume" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "phase": "data_migration",
    "user_input": {
      "approved_by": "admin@example.com"
    }
  }'

# 5. Cancel if necessary
curl -X POST "https://api.example.com/api/v1/decommission-flow/$FLOW_ID/cancel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID"
```

---

## Frontend Integration

### React Query Hook Example

```typescript
import { useDecommissionFlowStatus } from '@/hooks/decommissionFlow';

function DecommissionFlowDashboard({ flowId }: { flowId: string }) {
  const { data: status, isLoading, error } = useDecommissionFlowStatus(flowId, {
    refetchInterval: (data) => {
      // Poll every 5s when active, 15s when paused, stop when done
      if (!data) return false;
      if (['decommission_planning', 'data_migration', 'system_shutdown'].includes(data.status)) {
        return 5000;
      }
      if (data.status === 'paused') return 15000;
      return false; // Stop polling when completed/failed
    }
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Flow Status: {status.status}</h2>
      <p>Current Phase: {status.current_phase}</p>
      <p>Systems: {status.system_count}</p>
      <p>Estimated Savings: ${status.metrics.estimated_savings}</p>
      <p>Compliance Score: {status.metrics.compliance_score}%</p>
    </div>
  );
}
```

---

## Implementation Notes

### ADR Compliance
- **ADR-006**: Master Flow Orchestrator pattern with two-table architecture
- **ADR-012**: Child flow status for operational decisions
- **ADR-027**: Phase names match FlowTypeConfig exactly

### Field Naming Convention
All API responses use `snake_case` field names (e.g., `flow_id`, `current_phase`, `system_count`). Frontend should use these directly without transformation.

### Polling Strategy (Railway Deployment)
- No WebSockets or Server-Sent Events
- HTTP polling only
- 5s interval when active
- 15s interval when paused
- Stop polling when completed/failed

### Transaction Atomicity
Flow creation uses atomic transactions to ensure both master and child flows are created together or rolled back on failure.

---

## Related Documentation

- Master Flow Orchestrator: `/docs/adr/006-master-flow-orchestrator.md`
- Flow Status Separation: `/docs/adr/012-flow-status-separation.md`
- Phase Configuration: `/docs/adr/027-flow-type-config.md`
- User Guide: `/docs/user-guide/DECOMMISSION_FLOW.md`
- Frontend Hooks: `/src/hooks/decommissionFlow/`

---

**Last Updated**: November 5, 2025
**API Version**: 1.0
**Stability**: Beta (Issues #950-951)
