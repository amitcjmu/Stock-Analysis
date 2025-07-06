# PRIORITY FIX CHECKLIST - Discovery Flow Critical Fixes (24 Hours)

## Context
The discovery flow is currently stuck due to multiple issues preventing users from completing an end-to-end flow. This checklist prioritizes fixes in order of criticality to get the system operational within 24 hours.

---

## 1. IMMEDIATE FIXES (0-4 hours) - Get the flow unstuck

### 1.1 Fix API Import Error Blocking Backend Startup
- [ ] **Task**: Fix syntax error in discovery_flow_service.py
- **Files to modify**: 
  - `/backend/app/services/discovery_flow_service.py` (line 334)
  - `/backend/app/api/v2/api.py` (remove v1 discovery_flow_v2 import)
- **Specific code changes**:
  ```python
  # In discovery_flow_service.py, check line 334 for unmatched brace
  # In api.py, remove: from app.api.v1.discovery_flow_v2 import router
  ```
- **How to verify**: 
  - Run `docker-compose logs -f backend` - should show no import errors
  - Health check endpoint returns 200: `curl http://localhost:8000/api/v1/health`
- **Impact if not fixed**: Backend won't start, entire system is down

### 1.2 Fix Flow State Initialization
- [ ] **Task**: Ensure flow_id is properly generated and stored
- **Files to modify**:
  - `/backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py`
  - `/backend/app/services/crewai_flows/flow_state_bridge.py`
- **Specific code changes**:
  ```python
  # In base_flow.py __init__, ensure:
  self.flow_id = str(uuid.uuid4()) if not hasattr(self, 'flow_id') else self.flow_id
  # Add early validation in initialize_flow()
  ```
- **How to verify**:
  - Initialize a flow via API and check PostgreSQL: `SELECT * FROM unified_discovery_flow_states;`
  - Flow ID should be present and valid UUID
- **Impact if not fixed**: Flows can't be tracked, status updates fail

### 1.3 Fix Frontend API Endpoint Mismatch
- [ ] **Task**: Align frontend API calls with backend routes
- **Files to modify**:
  - `/src/hooks/useUnifiedDiscoveryFlow.ts`
  - `/backend/app/api/v1/unified_discovery.py`
- **Specific code changes**:
  ```typescript
  // Update endpoint from:
  `/api/v1/discovery/flows/${flowId}/status`
  // To:
  `/api/v1/unified-discovery/flow/status/${flowId}`
  ```
- **How to verify**:
  - Network tab shows 200 responses for flow status calls
  - No 404 errors in browser console
- **Impact if not fixed**: Frontend can't get flow status, UI appears frozen

### 1.4 Enable Basic Flow Progression
- [ ] **Task**: Remove blocking conditions preventing phase transitions
- **Files to modify**:
  - `/backend/app/services/crewai_flows/unified_discovery_flow/phases/field_mapping.py`
  - `/backend/app/services/crewai_flows/unified_discovery_flow/state_management.py`
- **Specific code changes**:
  ```python
  # Add fallback for missing agents:
  if not self.attribute_mapping_agent:
      logger.warning("No agent available, using mock response")
      return "field_mapping_completed"
  ```
- **How to verify**:
  - Flow progresses from data_import → field_mapping → data_cleansing
  - Check logs: `docker-compose logs backend | grep "Phase transition"`
- **Impact if not fixed**: Flow gets stuck after data import

---

## 2. CRITICAL FIXES (4-12 hours) - Stabilize the system

### 2.1 Implement Proper Multi-Tenant Headers
- [ ] **Task**: Ensure all API calls include required tenant headers
- **Files to modify**:
  - `/backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`
  - `/src/contexts/AuthContext.tsx`
- **Specific code changes**:
  ```typescript
  // Add to getAuthHeaders():
  'X-Client-Account-ID': clientAccountId,
  'X-Engagement-ID': engagementId,
  'X-User-ID': userId
  ```
- **How to verify**:
  - All API calls show tenant headers in network tab
  - No 403 errors for missing context
- **Impact if not fixed**: Random authentication failures, data isolation issues

### 2.2 Fix PostgreSQL State Persistence
- [ ] **Task**: Ensure state updates are properly committed
- **Files to modify**:
  - `/backend/app/services/crewai_flows/postgresql_flow_persistence.py`
  - `/backend/app/services/crewai_flows/persistence/postgres_store.py`
- **Specific code changes**:
  ```python
  # Add explicit commits after state updates:
  await db.commit()
  # Add retry logic for concurrent updates
  ```
- **How to verify**:
  - State changes persist across page refreshes
  - Database shows updated timestamps
- **Impact if not fixed**: Progress lost, users have to restart

### 2.3 Implement Missing Phase Executors
- [ ] **Task**: Add fallback executors for phases without CrewAI agents
- **Files to modify**:
  - `/backend/app/services/crewai_flows/handlers/phase_executors/`
  - `/backend/app/services/master_flow_orchestrator.py`
- **Specific code changes**:
  ```python
  # Create mock executors that return success:
  class MockFieldMappingExecutor:
      async def execute(self, context):
          return {"status": "completed", "mappings": {}}
  ```
- **How to verify**:
  - All phases can execute without errors
  - Flow reaches "completed" status
- **Impact if not fixed**: Flow stops at phases without implementation

### 2.4 Fix Frontend State Management
- [ ] **Task**: Ensure frontend properly tracks flow state
- **Files to modify**:
  - `/src/pages/discovery/CMDBImport.tsx`
  - `/src/components/discovery/DiscoveryFlowProgress.tsx`
- **Specific code changes**:
  ```typescript
  // Add polling for flow status:
  useEffect(() => {
    const interval = setInterval(refreshFlow, 5000);
    return () => clearInterval(interval);
  }, [flowId]);
  ```
- **How to verify**:
  - UI updates automatically as flow progresses
  - Progress bar shows correct percentage
- **Impact if not fixed**: UI appears frozen, users don't see progress

---

## 3. ESSENTIAL FIXES (12-24 hours) - Make it production-ready

### 3.1 Add Error Recovery Mechanisms
- [ ] **Task**: Implement retry logic and error boundaries
- **Files to modify**:
  - `/backend/app/services/flow_error_handler.py`
  - `/backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py`
- **Specific code changes**:
  ```python
  # Add retry decorator:
  @retry(max_attempts=3, delay=1.0)
  async def execute_phase_with_retry(self, phase):
  ```
- **How to verify**:
  - Transient errors don't fail the entire flow
  - Error messages are user-friendly
- **Impact if not fixed**: Single errors break entire flow

### 3.2 Implement Flow Cleanup and Reset
- [ ] **Task**: Allow users to cancel/restart stuck flows
- **Files to modify**:
  - `/backend/app/api/v1/master_flows.py`
  - `/backend/app/services/crewai_flows/discovery_flow_cleanup_service.py`
- **Specific code changes**:
  ```python
  # Add endpoint:
  @router.delete("/flows/{flow_id}/reset")
  async def reset_flow(flow_id: str):
  ```
- **How to verify**:
  - Users can cancel stuck flows
  - New flow can be started after cancellation
- **Impact if not fixed**: Users stuck with broken flows

### 3.3 Add Basic Monitoring and Logging
- [ ] **Task**: Implement flow event logging for debugging
- **Files to modify**:
  - `/backend/app/services/crewai_flows/event_listeners/discovery_flow_listener.py`
  - `/backend/app/api/v1/endpoints/monitoring.py`
- **Specific code changes**:
  ```python
  # Log all phase transitions:
  logger.info(f"FLOW_EVENT: {flow_id} -> {phase} -> {status}")
  ```
- **How to verify**:
  - Can trace flow execution in logs
  - Monitoring endpoint shows active flows
- **Impact if not fixed**: Can't debug production issues

### 3.4 Validate End-to-End Flow
- [ ] **Task**: Create integration test for complete flow
- **Files to modify**:
  - `/backend/tests/integration/test_discovery_flow_e2e.py` (create)
  - `/docs/testing/discovery_flow_test_plan.md` (create)
- **Specific code changes**:
  ```python
  # Test: Import CSV → Field Mapping → Cleansing → Inventory → Complete
  async def test_complete_discovery_flow():
      # 1. Initialize flow
      # 2. Upload test data
      # 3. Verify each phase
      # 4. Check final output
  ```
- **How to verify**:
  - Test passes consistently
  - Manual testing confirms flow works
- **Impact if not fixed**: No confidence in deployment

---

## Quick Validation Script

```bash
#!/bin/bash
# Run after implementing fixes to validate system

echo "1. Checking backend health..."
curl -s http://localhost:8000/api/v1/health | jq .

echo "2. Checking database connections..."
docker exec migration_backend python -c "
from app.core.database import AsyncSessionLocal
import asyncio
async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute('SELECT 1')
        print('Database OK')
asyncio.run(test())
"

echo "3. Checking flow initialization..."
curl -X POST http://localhost:8000/api/v1/unified-discovery/flow/initialize \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 1" \
  -H "X-Engagement-ID: 1" \
  -d '{"test": true}'

echo "4. Checking frontend build..."
docker exec migration_frontend npm run build

echo "✅ Validation complete"
```

---

## Success Criteria
- [ ] User can upload CSV data without errors
- [ ] Flow progresses through all phases automatically
- [ ] Frontend shows real-time progress updates
- [ ] Flow completes successfully with asset inventory
- [ ] No critical errors in logs
- [ ] System remains stable under normal load

## Notes
- Focus on getting basic flow working first, optimize later
- Use mock responses where CrewAI agents aren't ready
- Log everything for debugging
- Test with small datasets first (< 100 records)