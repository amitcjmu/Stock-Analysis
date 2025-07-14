# Active Discovery Endpoints Reference

## After Cleanup (January 2025)

### Query Endpoints (Still Active)
1. **GET /api/v1/discovery/flows/active**
   - Used by: Discovery dashboard
   - Purpose: Get all active discovery flows for the tenant
   - Features: ETag support, excludes deleted flows, only shows flows with data

2. **GET /api/v1/discovery/flows/{flow_id}/status**
   - Used by: Flow status components, polling mechanisms
   - Purpose: Get detailed status of a specific flow
   - Features: ETag support, phase completion, agent insights

3. **GET /api/v1/discovery/flow/{flow_id}/agent-insights**
   - Used by: useAgentQuestions hook, agent UI components
   - Purpose: Get AI agent insights and recommendations
   - Features: Page context filtering, ETag support

4. **GET /api/v1/discovery/agents/discovery/agent-questions**
   - Used by: useAgentQuestions hook
   - Purpose: Get agent questions needing user input
   - Note: Currently returns empty array (placeholder)

5. **GET /api/v1/discovery/flow/crews/monitoring/{flow_id}**
   - Used by: Crew monitoring components
   - Purpose: Monitor CrewAI crew execution
   - Features: Real-time crew status updates

### Execution Endpoints (Still Active)
1. **POST /api/v1/discovery/flow/{flow_id}/resume**
   - Purpose: Resume a paused flow after user approval
   - Features: Master Flow Orchestrator integration, field mapping approval

2. **POST /api/v1/discovery/flow/{flow_id}/resume-intelligent**
   - Purpose: Intelligently resume from any interrupted state
   - Features: Auto-detect resume point, restart from raw data option

3. **POST /api/v1/discovery/flow/{flow_id}/execute**
   - Purpose: Execute a specific phase manually
   - Features: Force execution option, phase validation

4. **POST /api/v1/discovery/flow/{flow_id}/retry**
   - Purpose: Retry a failed flow from last successful phase
   - Features: Automatic phase detection, metadata tracking

### Agent UI Integration Endpoints
1. **GET /api/v1/discovery/agent-status**
   - Purpose: Get current agent status for UI monitor
   - Features: Multi-tenant scoped, real-time status

2. **GET /api/v1/discovery/agent-questions**
   - Purpose: Get pending agent questions by page
   - Features: Page context filtering, sample question generation

3. **POST /api/v1/discovery/agent-questions/answer**
   - Purpose: Submit user responses to agent questions
   - Features: Communication protocol integration

### Removed/Commented Endpoints
1. ~~POST /api/v1/discovery/flow/{flow_id}/abort~~ - No frontend usage
2. ~~GET /api/v1/discovery/flow/{flow_id}/processing-status~~ - No frontend usage
3. ~~GET /api/v1/discovery/flows/agentic-analysis-status~~ - Never existed

### Migration Path
- Frontend should gradually migrate from `/api/v1/discovery/` to `/api/v1/flows/`
- Use Master Flow APIs for unified flow management across all flow types
- Consolidate duplicate type definitions and response formats