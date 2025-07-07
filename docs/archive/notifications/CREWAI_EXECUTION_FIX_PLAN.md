# CrewAI Execution Layer Fix Plan

## Problem Summary

Based on test results, the discovery flow fails at the execution layer:
- ✅ Frontend works (upload, navigation)
- ✅ API works (file upload, flow creation)
- ✅ Database works (flow state persisted)
- ❌ **CrewAI execution completely broken** (no agents run, no phases execute)

## Root Cause Analysis

### 1. **Flow Stuck at INITIALIZING**
```
Current State: Flow created with status "INITIALIZING" at 0%
Expected: Flow should transition to "running" and execute import phase
Actual: Flow remains at INITIALIZING forever
```

### 2. **No Agent Execution**
- ImportAgent never runs
- No validation occurs
- No data processing happens
- No state updates

### 3. **Phase Execution Broken**
The connection between MFO → ImportExec → ImportAgent is severed.

## Investigation Areas

### 1. Check UnifiedDiscoveryFlow Implementation
```python
# backend/app/services/crewai_flows/unified_discovery_flow.py
# Is the @start() method actually being triggered?
# Are the phase methods (@listen decorators) connected?
```

### 2. Check Flow State Manager
```python
# backend/app/services/crewai_flows/flow_state_manager.py
# Is execute_phase() working?
# Are phase transitions happening?
```

### 3. Check Import Execution
```python
# backend/app/services/crewai_flows/unified_discovery_flow/phases/data_import.py
# Is the import crew being created?
# Are agents being kickstarted?
```

## Fix Plan

### Phase 1: Diagnose CrewAI Integration (2 hours)

1. **Add Logging to Track Execution Flow**
   ```python
   # In UnifiedDiscoveryFlow.__init__
   logger.info(f"🚀 UnifiedDiscoveryFlow initialized for flow {flow_id}")
   
   # In @start() method
   logger.info(f"🎯 Starting discovery flow {self.flow_id}")
   
   # In each @listen method
   logger.info(f"📊 Executing phase: {phase_name}")
   ```

2. **Verify CrewAI Flow is Actually Running**
   ```python
   # In flow initialization
   flow = UnifiedDiscoveryFlow(flow_id=flow_id)
   logger.info(f"Flow instance created: {flow}")
   
   # Check if kickoff() is being called
   result = flow.kickoff()
   logger.info(f"Flow kickoff result: {result}")
   ```

3. **Check Event Listeners**
   ```python
   # Ensure @listen decorators are properly connected
   @listen(start_method)
   def data_import_phase(self):
       logger.info("DATA IMPORT PHASE TRIGGERED")
   ```

### Phase 2: Fix Execution Chain (3 hours)

1. **Fix Flow Initialization**
   ```python
   # In MasterFlowOrchestrator.create_flow()
   if flow_type == 'discovery':
       # Ensure flow is properly started
       flow_instance = UnifiedDiscoveryFlow(flow_id=flow_id)
       flow_instance.kickoff()  # <-- This might be missing
   ```

2. **Fix Phase Execution**
   ```python
   # In FlowStateManager.execute_phase()
   async def execute_phase(self, phase_name: str):
       logger.info(f"Executing phase {phase_name} for flow {self.flow_id}")
       
       # Get the flow instance
       flow = self.get_flow_instance()
       
       # Trigger the phase method
       phase_method = getattr(flow, f"{phase_name}_phase", None)
       if phase_method:
           result = phase_method()
       else:
           logger.error(f"Phase method {phase_name}_phase not found")
   ```

3. **Fix Agent Execution**
   ```python
   # In data_import.py
   def execute_data_import(self):
       logger.info("Creating import crew")
       crew = self._create_import_crew()
       
       logger.info("Kicking off crew execution")
       result = crew.kickoff(inputs={
           'flow_id': self.flow_id,
           'raw_data': self.state.raw_data
       })
       
       logger.info(f"Crew result: {result}")
       return result
   ```

### Phase 3: Implement Proper Flow Lifecycle (4 hours)

1. **Create Flow Execution Service**
   ```python
   class FlowExecutionService:
       async def start_flow(self, flow_id: str):
           """Start a flow and ensure it executes"""
           flow = await self.get_flow(flow_id)
           
           if flow.flow_type == 'discovery':
               # Create and start UnifiedDiscoveryFlow
               discovery_flow = UnifiedDiscoveryFlow(flow_id)
               
               # Start in background task
               asyncio.create_task(self._run_flow(discovery_flow))
               
       async def _run_flow(self, flow):
           """Run flow with error handling"""
           try:
               result = await flow.kickoff()
               logger.info(f"Flow completed: {result}")
           except Exception as e:
               logger.error(f"Flow failed: {e}")
               await self.mark_flow_failed(flow.flow_id, str(e))
   ```

2. **Update API Endpoints**
   ```python
   @router.post("/flows/")
   async def create_flow(request: CreateFlowRequest):
       # Create flow in database
       flow_id = await orchestrator.create_flow(...)
       
       # Start execution
       execution_service = FlowExecutionService()
       await execution_service.start_flow(flow_id)
       
       return {"flow_id": flow_id, "status": "running"}
   ```

3. **Add Progress Tracking**
   ```python
   class ProgressTracker:
       async def update_progress(self, flow_id: str, phase: str, progress: int):
           """Update flow progress in database"""
           await self.db.execute(
               "UPDATE flows SET current_phase = ?, progress = ? WHERE flow_id = ?",
               (phase, progress, flow_id)
           )
           
           # Notify frontend via websocket/SSE
           await self.notify_progress(flow_id, phase, progress)
   ```

### Phase 4: Testing & Validation (2 hours)

1. **Create Integration Test**
   ```python
   async def test_discovery_flow_execution():
       # Upload file
       response = await client.post("/api/v1/data-import/upload", ...)
       
       # Create flow
       flow_response = await client.post("/api/v1/flows/", ...)
       flow_id = flow_response.json()["flow_id"]
       
       # Wait for execution
       await asyncio.sleep(5)
       
       # Check progress
       status = await client.get(f"/api/v1/flows/{flow_id}/status")
       assert status.json()["status"] == "running"
       assert status.json()["progress"] > 0
   ```

2. **Add Health Check**
   ```python
   @router.get("/flows/health")
   async def check_crew_health():
       """Verify CrewAI is working"""
       try:
           # Create minimal test crew
           test_crew = Crew(agents=[test_agent], tasks=[test_task])
           result = test_crew.kickoff()
           return {"status": "healthy", "test_result": result}
       except Exception as e:
           return {"status": "unhealthy", "error": str(e)}
   ```

## Implementation Priority

1. **Immediate (Today)**
   - Add comprehensive logging to trace execution flow
   - Identify where the chain breaks
   - Fix flow kickoff mechanism

2. **Short Term (This Week)**
   - Implement proper flow execution service
   - Add progress tracking
   - Fix phase transitions

3. **Medium Term (Next Week)**
   - Add monitoring and health checks
   - Implement retry logic
   - Add integration tests

## Success Criteria

1. **Flow Execution**: Flow transitions from INITIALIZING to running
2. **Agent Execution**: ImportAgent processes uploaded data
3. **Progress Updates**: UI shows progress > 0%
4. **Phase Completion**: Data import phase completes successfully
5. **Field Mappings**: Mappings are generated and available
6. **Asset Creation**: Assets appear in inventory

## Quick Wins

1. **Check if `kickoff()` is being called** on UnifiedDiscoveryFlow
2. **Add logging** to every phase method
3. **Verify database has CrewAI tables** (crews, agents, tasks)
4. **Check for Python async/await issues** (CrewAI might need sync execution)

## Next Steps

1. Start with logging to understand the current execution flow
2. Identify the exact point of failure
3. Implement the minimal fix to get flows executing
4. Then improve with proper service architecture