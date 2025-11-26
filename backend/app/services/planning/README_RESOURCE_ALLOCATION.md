# Resource Allocation Service Integration Guide

## Overview

The `ResourceAllocationService` provides AI-driven resource allocation for migration waves using the `resource_allocation_specialist` CrewAI agent. It supports:

- AI-generated resource allocations with confidence scores
- Manual overrides with audit trail
- Learning from human adjustments (via TenantMemoryManager)
- Full observability integration (ADR-031)

## Architecture Compliance

### ADR-015: Persistent Multi-Tenant Agent Architecture
✅ Uses `TenantScopedAgentPool.get_agent()` to retrieve persistent agent instances
✅ Agent singleton per (client_account_id, engagement_id) tuple

### ADR-024: TenantMemoryManager
✅ `memory=False` enforced (CrewAI memory disabled)
✅ TODO placeholder for TenantMemoryManager integration for override learning

### ADR-029: LLM Output JSON Sanitization
✅ Uses `sanitize_for_json()` for all LLM-generated data
✅ Handles NaN, Infinity, and other non-JSON-safe values

### ADR-031: Observability
✅ Full `CallbackHandlerIntegration` instrumentation
✅ Task start/completion tracking
✅ Tenant context propagation
✅ Error handling with callback notifications

## Usage Example

```python
from app.services.planning.resource_allocation_service import ResourceAllocationService

# Initialize service with DB session and request context
service = ResourceAllocationService(db=db, context=request_context)

# Generate AI allocations
wave_plan_data = {
    "waves": [
        {
            "wave_id": "wave-1",
            "applications": [...],
            "dependencies": []
        }
    ]
}

allocations = await service.generate_ai_allocations(
    planning_flow_id=planning_flow_id,
    wave_plan_data=wave_plan_data,
    resource_pools={"architects": 5, "developers": 20},
    historical_data={"avg_effort_per_app": 100}
)

# Apply manual override
updated_allocations = await service.apply_manual_override(
    planning_flow_id=planning_flow_id,
    wave_id="wave-1",
    overrides={
        "resources.cloud_architect.count": 3,
        "resources.developer.effort_hours": 200
    },
    user_id=str(user_id),
    reason="Additional capacity for parallel workstreams"
)
```

## JSONB Storage Schema

Data is stored in `planning_flows.resource_allocation_data` JSONB column:

```json
{
    "allocations": [
        {
            "wave_id": "wave-1",
            "resources": [
                {
                    "role": "cloud_architect",
                    "count": 2,
                    "effort_hours": 120,
                    "confidence_score": 85,
                    "rationale": "Complex architecture requires dedicated architects"
                }
            ],
            "total_cost": 50000.00,
            "overrides": [
                {
                    "timestamp": "2025-11-26T10:00:00Z",
                    "user_id": "user-uuid",
                    "field": "resources.cloud_architect.count",
                    "old_value": 2,
                    "new_value": 3,
                    "reason": "Additional capacity needed"
                }
            ]
        }
    ],
    "metadata": {
        "generated_at": "2025-11-26T10:00:00Z",
        "agent_version": "resource_allocation_specialist_v1",
        "total_estimated_cost": 150000.00
    }
}
```

## Agent Configuration

The `resource_allocation_specialist` agent is defined in:
`backend/app/services/crewai_flows/crews/config/planning_agents.yaml`

Agent capabilities:
- Role-based resource requirement analysis
- Workload estimation based on application complexity
- Resource leveling across parallel waves
- Cost-aware allocation with budget constraints
- Capacity planning and utilization forecasting

## Testing

Unit tests are located at:
`backend/tests/unit/services/planning/test_resource_allocation_service.py`

Run tests:
```bash
cd backend
pytest tests/unit/services/planning/test_resource_allocation_service.py -v
```

## Next Steps

1. **API Integration**: Create REST endpoints in `/api/v1/planning-flow/` for:
   - `POST /resource-allocation/generate` - Generate AI allocations
   - `POST /resource-allocation/override` - Apply manual overrides
   - `GET /resource-allocation/{planning_flow_id}` - Retrieve allocations

2. **Frontend Integration**: Build UI components for:
   - Displaying AI-generated allocations with confidence scores
   - Manual override interface with field-level editing
   - Audit trail visualization for override history

3. **TenantMemoryManager Integration**: Implement learning from overrides:
   - Store override patterns in tenant memory
   - Use historical override data to improve future allocations
   - Track which overrides improve outcomes

4. **Validation Rules**: Add business logic validation:
   - Check resource pool availability
   - Validate budget constraints
   - Ensure role requirements match wave complexity

## Observability

All LLM calls and agent task executions are automatically tracked:

- **LLM Costs**: View in Grafana at http://localhost:9999/d/llm-costs/
- **Agent Activity**: View in Grafana at http://localhost:9999/d/agent-activity/
- **Database**: Query `migration.agent_task_history` and `migration.llm_usage_logs`

## Issue Tracking

Related GitHub Issue: #1147 - Integrate Resource Allocation CrewAI Agent
