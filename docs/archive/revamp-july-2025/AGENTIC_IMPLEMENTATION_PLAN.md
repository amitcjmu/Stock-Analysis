# AGENTIC IMPLEMENTATION PLAN
## 48-Hour Aggressive Discovery Flow Fix
### Execution Date: July 2025

---

## MISSION CRITICAL: Fix Discovery Flow in 48 Hours

**Total Duration**: 48 hours (2 days)  
**Team Structure**: 5 parallel AI agent teams working 24/7  
**Critical Path**: State Management → Field Mapping → Real CrewAI → Testing → Frontend  
**Rollback Points**: Every 4 hours with automated testing checkpoints

---

## Team Structure & Responsibilities

### Team Alpha: State Management Consolidation
**Mission**: Establish PostgreSQL discovery_flows table as single source of truth
**Skills**: Database architecture, transaction management, race condition prevention

### Team Beta: Field Mapping Fix  
**Mission**: Fix the broken field mapping approval flow
**Skills**: Frontend/backend integration, UI state management, user flow

### Team Gamma: Real CrewAI Implementation
**Mission**: Replace pseudo-agents with actual CrewAI crews and agents
**Skills**: CrewAI framework, agent orchestration, tool development

### Team Delta: Testing & Validation
**Mission**: Continuous testing and validation of changes
**Skills**: E2E testing, integration testing, performance monitoring

### Team Epsilon: Frontend Fixes
**Mission**: Fix frontend state management and API integration
**Skills**: React, TypeScript, state management, API integration

---

## HOUR-BY-HOUR BREAKDOWN: First 12 Hours

### Hour 0-1: Emergency Triage & Setup
**ALL TEAMS**
```bash
# Clone current state and create feature branches
git checkout -b fix/alpha-state-consolidation
git checkout -b fix/beta-field-mapping
git checkout -b fix/gamma-crewai-implementation
git checkout -b fix/delta-testing-framework
git checkout -b fix/epsilon-frontend-fixes
```

**Team Alpha Actions**:
1. Analyze all state storage locations:
   - `/backend/app/services/crewai_flows/flow_state_bridge.py`
   - `/backend/app/services/crewai_flows/flow_state_manager.py`
   - `/backend/app/services/crewai_flows/postgresql_flow_persistence.py`
   - `/backend/app/repositories/discovery_flow_repository/base_repository.py`

2. Document exact state flow and identify redundancies

**Team Beta Actions**:
1. Trace field mapping approval flow:
   - `/backend/app/services/crewai_flows/unified_discovery_flow/phases/field_mapping.py`
   - `/backend/app/services/crewai_flows/unified_discovery_flow/state_management.py`
   - `/src/hooks/useUnifiedDiscoveryFlow.ts`
   - `/src/pages/discovery/AttributeMapping.tsx`

**Team Gamma Actions**:
1. Audit pseudo-agent implementations:
   - `/backend/app/services/crewai_flows/unified_discovery_flow/`
   - Identify all @start/@listen decorators
   - Map current "fake" CrewAI patterns

**Team Delta Actions**:
1. Set up continuous testing pipeline:
   ```python
   # /backend/tests/emergency/test_state_consistency.py
   async def test_single_source_of_truth():
       # Test that only discovery_flows table is updated
       pass
   ```

**Team Epsilon Actions**:
1. Map all frontend state management:
   - Identify session_id vs flow_id usage
   - Document all API calls and their patterns

### Hour 1-2: Critical Path Identification
**Team Alpha**: 
- CREATE state consolidation plan
- REMOVE competing state managers

**Team Beta**:
- IDENTIFY exact blocking condition in field mapping
- DESIGN bypass mechanism

**Team Gamma**:
- DESIGN real CrewAI crew structure
- CREATE agent role definitions

### Hour 2-4: Initial Implementation Sprint
**Team Alpha Code Changes**:
```python
# /backend/app/services/crewai_flows/single_state_manager.py
class SingleStateManager:
    """Single source of truth for all flow state"""
    
    def __init__(self, db: AsyncSession, flow_id: str):
        self.db = db
        self.flow_id = flow_id
        self._cache = None
        self._lock = asyncio.Lock()
    
    async def get_state(self) -> DiscoveryFlow:
        """Get state from PostgreSQL only"""
        async with self._lock:
            if not self._cache:
                self._cache = await self.db.get(DiscoveryFlow, self.flow_id)
            return self._cache
    
    async def update_state(self, updates: dict):
        """Atomic state update with transaction"""
        async with self._lock:
            async with self.db.begin():
                flow = await self.db.get(DiscoveryFlow, self.flow_id, with_for_update=True)
                for key, value in updates.items():
                    setattr(flow, key, value)
                await self.db.commit()
                self._cache = flow
```

**Team Beta Code Changes**:
```python
# /backend/app/services/crewai_flows/unified_discovery_flow/phases/field_mapping.py
@listen("data_cleansing_completed")
async def field_mapping_phase(self):
    """Fixed field mapping with proper approval flow"""
    
    # REMOVE the broken confidence check
    # if self.state.field_mapping_confidence < FlowConfig.DEFAULT_CONFIDENCE_THRESHOLD:
    #     return True  # This was blocking forever
    
    # NEW: Proper approval mechanism
    if self.state.awaiting_user_approval and not self.state.user_approval_received:
        # Set proper state for frontend
        await self.state_manager.update_state({
            "current_phase": "field_mapping",
            "phase_status": "awaiting_approval",
            "ui_state": {
                "show_approval_ui": True,
                "mappings_to_approve": self.state.field_mappings
            }
        })
        return False  # Don't proceed until approved
    
    # Continue with mapping
    return True
```

### Hour 4-6: State Management Overhaul
**Team Alpha Major Changes**:

1. **DELETE** these files/classes:
   - `/backend/app/services/crewai_flows/flow_state_manager.py` (old multi-layer manager)
   - Event-based state updates in `/backend/app/services/crewai_flows/event_listeners/`
   
2. **MODIFY** `/backend/app/services/crewai_flows/flow_state_bridge.py`:
```python
class FlowStateBridge:
    """Simplified bridge - PostgreSQL only"""
    
    def __init__(self, context: RequestContext):
        self.context = context
        self.state_manager = SingleStateManager(context.db, context.flow_id)
    
    async def load_state(self) -> UnifiedDiscoveryFlowState:
        """Load from PostgreSQL only"""
        flow = await self.state_manager.get_state()
        return self._db_to_flow_state(flow)
    
    async def save_state(self, state: UnifiedDiscoveryFlowState):
        """Save to PostgreSQL only - no events"""
        updates = self._flow_state_to_db(state)
        await self.state_manager.update_state(updates)
```

**Team Beta Frontend Fix**:
```typescript
// /src/pages/discovery/AttributeMapping.tsx
const AttributeMapping: React.FC = () => {
  const { flowData, approveFieldMappings } = useUnifiedDiscoveryFlow();
  
  // FIX: Properly handle approval state
  const needsApproval = flowData?.phase_status === 'awaiting_approval' 
    && flowData?.ui_state?.show_approval_ui;
  
  const handleApprove = async () => {
    await approveFieldMappings(flowData.flow_id, flowData.ui_state.mappings_to_approve);
  };
  
  if (needsApproval) {
    return <FieldMappingApprovalUI mappings={flowData.ui_state.mappings_to_approve} onApprove={handleApprove} />;
  }
  
  // Normal mapping UI
  return <FieldMappingUI />;
};
```

### Hour 6-8: Real CrewAI Implementation
**Team Gamma Creates Real Crews**:

```python
# /backend/app/services/crewai_flows/crews/discovery_crew.py
from crewai import Agent, Crew, Task, Process

class DiscoveryCrewFactory:
    """Factory for real CrewAI crews"""
    
    @staticmethod
    def create_data_validation_crew(llm_config):
        # Real agent with role and tools
        validator_agent = Agent(
            role='Data Validation Specialist',
            goal='Ensure imported data quality and completeness',
            backstory='Expert in enterprise data validation with 10 years experience',
            tools=[
                SchemaValidatorTool(),
                DataQualityCheckerTool(),
                AnomalyDetectorTool()
            ],
            llm=llm_config
        )
        
        # Real task definition
        validation_task = Task(
            description='Validate imported {data_type} data for completeness and quality',
            expected_output='Validation report with issues and recommendations',
            agent=validator_agent
        )
        
        # Real crew
        return Crew(
            agents=[validator_agent],
            tasks=[validation_task],
            process=Process.sequential
        )
    
    @staticmethod
    def create_field_mapping_crew(llm_config):
        mapper_agent = Agent(
            role='Field Mapping Expert',
            goal='Create intelligent field mappings between source and target schemas',
            backstory='ML engineer specializing in schema matching and data integration',
            tools=[
                SemanticMatcherTool(),
                PatternRecognizerTool(),
                HistoricalMappingTool()
            ],
            llm=llm_config
        )
        
        return Crew(
            agents=[mapper_agent],
            tasks=[
                Task(
                    description='Map source fields to target schema',
                    expected_output='Field mappings with confidence scores',
                    agent=mapper_agent
                )
            ]
        )
```

### Hour 8-10: Integration Sprint
**All Teams Converge**:

**Team Alpha + Beta Integration**:
- Ensure field mapping uses single state manager
- Remove all event-based DB updates

**Team Gamma Integration**:
```python
# /backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py
class UnifiedDiscoveryFlow(Flow):
    def __init__(self, context: RequestContext):
        super().__init__()
        self.context = context
        self.state_manager = SingleStateManager(context.db, context.flow_id)
        self.crew_factory = DiscoveryCrewFactory()
        
    @start()
    async def initialize_flow(self):
        """Initialize with real state management"""
        self.state = await self.state_manager.get_state()
        return self.state
    
    @listen("initialize_flow")
    async def data_import_phase(self):
        """Use real CrewAI crew for validation"""
        crew = self.crew_factory.create_data_validation_crew(self.llm_config)
        result = await crew.kickoff({
            'data_type': self.state.import_type,
            'raw_data': self.state.raw_data
        })
        
        await self.state_manager.update_state({
            'validation_results': result,
            'current_phase': 'data_import',
            'phase_status': 'completed'
        })
        
        return "data_import_completed"
```

**Team Delta Continuous Testing**:
```python
# Run every 30 minutes
async def test_checkpoint_hour_8():
    # Test single state source
    assert await count_state_updates() == 1  # Only PostgreSQL
    
    # Test field mapping approval
    assert await test_approval_flow_works()
    
    # Test real CrewAI execution
    assert await test_crew_execution_completes()
```

### Hour 10-12: Frontend State Consolidation
**Team Epsilon Major Refactor**:

```typescript
// /src/hooks/useUnifiedDiscoveryFlow.ts
export const useUnifiedDiscoveryFlow = (flowId?: string) => {
  // REMOVE all session_id references
  // SINGLE API for all operations
  
  const flowQuery = useQuery({
    queryKey: ['discovery-flow', flowId],
    queryFn: () => apiClient.get(`/api/v1/discovery/flows/${flowId}`),
    refetchInterval: 5000 // Poll for updates
  });
  
  const approveFieldMappings = useMutation({
    mutationFn: (mappings) => 
      apiClient.post(`/api/v1/discovery/flows/${flowId}/approve-mappings`, { mappings }),
    onSuccess: () => {
      queryClient.invalidateQueries(['discovery-flow', flowId]);
    }
  });
  
  return {
    flowData: flowQuery.data,
    isLoading: flowQuery.isLoading,
    approveFieldMappings: approveFieldMappings.mutate
  };
};
```

---

## CRITICAL PATH TIMELINE (Hours 12-48)

### Hours 12-16: Integration Testing Phase
**Team Delta Leading**:
- Full E2E test of discovery flow
- Performance benchmarking
- Race condition testing
- Multi-tenant isolation verification

**Checkpoint Tests**:
```bash
# Every 4 hours run:
docker exec -it migration_backend pytest tests/emergency/test_discovery_flow_e2e.py -v
docker exec -it migration_frontend npm run test:e2e:discovery
```

### Hours 16-24: Bug Fix Sprint
**All Teams**:
- Fix issues found in testing
- Optimize performance bottlenecks
- Handle edge cases

**Critical Fixes Expected**:
1. Transaction deadlocks in state updates
2. Frontend state sync delays
3. CrewAI timeout handling
4. Memory leaks in long-running flows

### Hours 24-32: Master Flow Integration
**Team Alpha + Gamma**:
```python
# Ensure all flows register with master orchestrator
async def create_discovery_flow(self, data_import_id: str):
    # Create discovery flow
    flow = await self._create_discovery_flow_record(data_import_id)
    
    # CRITICAL: Register with master flow
    master_repo = CrewAIFlowStateExtensionsRepository(self.db, self.context.client_account_id)
    await master_repo.create_master_flow(
        flow_id=flow.id,
        flow_type='discovery',
        user_id=self.context.user_id,
        flow_configuration={'import_id': data_import_id}
    )
```

### Hours 32-40: Production Hardening
**All Teams**:
1. Add comprehensive error handling
2. Implement retry mechanisms
3. Add circuit breakers
4. Performance optimization

**Key Hardening Areas**:
```python
# Add to all state operations
async def update_state_with_retry(self, updates: dict, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with asyncio.timeout(30):  # 30 second timeout
                return await self.state_manager.update_state(updates)
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Hours 40-48: Final Validation & Deployment
**Team Delta + DevOps**:
1. Full regression testing
2. Load testing with 1000 concurrent flows
3. Security validation
4. Deployment to staging
5. Smoke tests in staging
6. Production deployment plan

---

## ROLLBACK PROCEDURES

### Checkpoint Rollbacks (Every 4 Hours)
```bash
# Automated rollback if tests fail
if ! docker exec -it migration_backend pytest tests/emergency/; then
    git checkout main
    docker-compose down
    docker-compose up -d --build
    echo "ROLLBACK EXECUTED AT HOUR $CURRENT_HOUR"
fi
```

### Critical Rollback Points:
1. **Hour 4**: State management changes
2. **Hour 8**: CrewAI implementation
3. **Hour 12**: Frontend integration
4. **Hour 24**: Master flow integration
5. **Hour 40**: Production readiness

---

## SPECIFIC CODE CHANGES BY FILE

### Backend Critical Files to Modify:

1. **DELETE THESE FILES**:
   - `/backend/app/services/crewai_flows/flow_state_manager.py`
   - `/backend/app/services/crewai_flows/event_listeners/discovery_flow_listener.py`
   - All files in `/backend/archive/legacy/` (ensure not imported)

2. **CREATE THESE FILES**:
   - `/backend/app/services/crewai_flows/single_state_manager.py`
   - `/backend/app/services/crewai_flows/crews/discovery_crew.py`
   - `/backend/app/services/crewai_flows/crews/field_mapping_crew.py`
   - `/backend/app/services/crewai_flows/crews/data_cleansing_crew.py`

3. **MODIFY THESE FILES**:
   - `/backend/app/services/crewai_flows/flow_state_bridge.py` - Remove multi-layer state
   - `/backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py` - Use real crews
   - `/backend/app/services/crewai_flows/unified_discovery_flow/phases/field_mapping.py` - Fix approval
   - `/backend/app/repositories/discovery_flow_repository/base_repository.py` - Single DB updates
   - `/backend/app/api/v1/endpoints/unified_discovery.py` - Add approval endpoint

### Frontend Critical Files to Modify:

1. **UPDATE ALL REFERENCES**:
   - Replace `session_id` with `flow_id` globally
   - Remove `/api/v2` and `/api/v3` references
   - Use only `/api/v1` endpoints

2. **MODIFY THESE FILES**:
   - `/src/hooks/useUnifiedDiscoveryFlow.ts` - Simplify to single API
   - `/src/pages/discovery/AttributeMapping.tsx` - Fix approval UI
   - `/src/pages/discovery/CMDBImport.tsx` - Remove session references
   - `/src/config/api.ts` - Remove v2/v3 configurations

---

## SUCCESS CRITERIA

### Must Complete in 48 Hours:
1. ✅ Single source of truth (PostgreSQL only)
2. ✅ Field mapping approval flow works
3. ✅ Real CrewAI agents executing
4. ✅ No race conditions in state updates
5. ✅ Frontend properly synced with backend
6. ✅ All flows registered with master orchestrator
7. ✅ E2E tests passing
8. ✅ Performance: <5s phase transitions

### Validation Tests:
```python
# Final validation suite
async def validate_discovery_flow_fixed():
    # 1. Create flow
    flow = await create_discovery_flow()
    
    # 2. Import data
    await import_cmdb_data(flow.id, test_csv)
    
    # 3. Validate approval UI appears
    assert await check_approval_ui_visible(flow.id)
    
    # 4. Approve mappings
    await approve_mappings(flow.id)
    
    # 5. Complete flow
    await complete_discovery_flow(flow.id)
    
    # 6. Verify single DB updates
    assert count_db_updates(flow.id) == expected_count
    
    # 7. Verify no orphaned state
    assert not check_orphaned_state(flow.id)
```

---

## CRITICAL WARNINGS

### DO NOT:
1. Add new state storage mechanisms
2. Create new event systems
3. Implement workarounds instead of fixes
4. Add complexity to "fix" issues
5. Create new competing architectures

### ALWAYS:
1. Use PostgreSQL as single source of truth
2. Test after every change
3. Maintain transaction boundaries
4. Use proper async/await patterns
5. Follow the principle of simplification

---

## POST-48 HOUR TASKS

Once core is fixed:
1. Add WebSocket for real-time updates
2. Implement caching layer (Redis)
3. Add comprehensive monitoring
4. Build admin dashboard
5. Create flow analytics

---

**Remember**: The goal is SIMPLIFICATION. Every line of code should reduce complexity, not add it. The system is broken because of too many competing patterns - fix by removing, not adding.

**Team Coordination**: Use shared Slack channel #emergency-discovery-fix for real-time updates. Post progress every hour.

**Final Note**: This is an emergency fix. Make it work, make it simple, then make it better. In that order.