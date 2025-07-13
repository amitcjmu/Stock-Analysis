# Discovery Flow Agentic Implementation Plan

## Executive Summary

This plan addresses the circular issues in the Discovery flow where hardcoded heuristic logic bypasses the existing agentic workflows. The solution leverages the **existing Master Flow Orchestrator (MFO)** infrastructure and CrewAI capabilities without recreating functionality that already exists.

## Current State Analysis

### What Already Exists (DO NOT RECREATE)
1. **Master Flow Orchestrator (MFO)** - Complete flow lifecycle management
2. **Agent-UI Bridge** - Real-time agent-user communication infrastructure
3. **Flow State Management** - PostgreSQL-based state persistence
4. **Phase Execution Manager** - Coordinates phase execution
5. **Crew Coordinator** - Orchestrates agent execution
6. **Background Task Execution** - Async flow execution
7. **Error Recovery & Retry** - Resilient execution patterns

### Key Problems Identified

#### 1. **Hardcoded Business Logic Bypassing Agents**
- 90% approval threshold hardcoded in frontend
- Critical field definitions hardcoded
- Phase transition logic hardcoded in `@listen` decorators

#### 2. **Frontend-Driven Orchestration**
- Frontend directly triggers phase transitions
- Navigation commands bypass agent recommendations
- User actions directly control flow state

#### 3. **Polling Instead of Event-Driven Updates**
- 90-second polling intervals for status checks
- Agent-UI bridge exists but not connected
- No real-time agent insights during execution

#### 4. **Mock Agent Implementations**
- Field mapping using placeholder logic
- Agents not making autonomous decisions
- CrewAI infrastructure underutilized

## Implementation Strategy

### Core Principle: Fix Bypass Points, Not Recreate

We will **NOT** create new orchestration systems. Instead, we will:
1. Remove hardcoded logic and delegate to agents
2. Connect existing agent-UI bridge for real-time updates
3. Enable agent-driven phase transitions within MFO
4. Implement real CrewAI agents where mocks exist

### Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│  MFO API Layer   │────▶│  Master Flow    │
│  (Passive View) │◀────│  (Event Stream)  │◀────│  Orchestrator   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
         ▲                                                  │
         │                                                  ▼
         │              ┌──────────────────┐     ┌─────────────────┐
         └──────────────│  Agent-UI Bridge │◀────│  CrewAI Agents  │
                        │  (Real-time)     │     │  (Autonomous)   │
                        └──────────────────┘     └─────────────────┘
```

## Detailed Implementation Plan

### Phase 1: Enable Agent-Driven Decision Making

#### 1.1 Remove Hardcoded Business Logic

**File**: `backend/app/services/crewai_flows/unified_discovery_flow/phases/field_mapping.py`

**Changes**:
- Replace mock `MappingResult` with real CrewAI agent output
- Implement `FieldMappingDecisionAgent` that analyzes:
  - Data quality and complexity
  - Field ambiguity and mapping confidence
  - Business context to determine critical fields
  - Approval thresholds based on data characteristics

**Implementation**:
```python
class FieldMappingDecisionAgent(Agent):
    """Agent that makes autonomous decisions about field mappings"""
    
    def analyze_mapping_requirements(self, data: List[Dict]) -> Dict:
        # Agent analyzes data to determine:
        # - Which fields are critical (not hardcoded)
        # - What approval threshold is appropriate
        # - Whether user review is needed
        return {
            "critical_fields": self._identify_critical_fields(data),
            "approval_threshold": self._calculate_threshold(data),
            "user_review_required": self._assess_complexity(data)
        }
```

#### 1.2 Implement Agent-Based Phase Transitions

**File**: `backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py`

**Changes**:
- Add `PhaseTransitionAgent` to each phase method
- Agent decides next phase based on results, not hardcoded `@listen`
- Maintain `@listen` decorators but make them conditional

**Implementation**:
```python
@listen(execute_data_import_validation_agent)
async def generate_field_mapping_suggestions(self, previous_result):
    # Let agent decide if field mapping is needed
    transition_agent = self.phase_transition_agent
    decision = await transition_agent.analyze_phase_transition(
        current_phase="data_import",
        results=previous_result,
        state=self.state
    )
    
    if decision.skip_phase:
        # Agent determined field mapping not needed
        return await self.execute_next_phase(decision.next_phase)
    
    # Continue with field mapping
    ...
```

### Phase 2: Connect Agent-UI Bridge for Real-Time Updates

#### 2.1 Implement WebSocket/SSE Endpoint

**File**: `backend/app/api/v1/endpoints/agent_communication.py` (new)

**Implementation**:
```python
@router.websocket("/ws/flow/{flow_id}")
async def flow_updates_websocket(
    websocket: WebSocket,
    flow_id: str,
    context: RequestContext = Depends(get_current_context)
):
    """WebSocket endpoint for real-time flow updates"""
    await websocket.accept()
    
    # Subscribe to agent-ui-bridge for this flow
    async for update in agent_ui_bridge.subscribe_to_flow(flow_id):
        await websocket.send_json(update)
```

#### 2.2 Connect Flow Execution to Agent-UI Bridge

**File**: `backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py`

**Changes**:
- Already has agent-ui-bridge imports and usage
- Ensure ALL agent decisions are broadcast
- Add real-time status updates at each step

### Phase 3: Update Frontend to be Event-Driven

#### 3.1 Replace Polling with WebSocket Connection

**File**: `src/hooks/useUnifiedDiscoveryFlow.ts`

**Changes**:
```typescript
// Replace polling with WebSocket
const { data: flowUpdates } = useWebSocket(
  `/api/v1/ws/flow/${flowId}`,
  {
    onMessage: (event) => {
      const update = JSON.parse(event.data);
      // Update local state with real-time agent insights
      handleAgentUpdate(update);
    }
  }
);
```

#### 3.2 Remove Frontend Orchestration Logic

**Files to Update**:
- `src/hooks/discovery/useAttributeMappingActions.ts`
- `src/hooks/discovery/useAttributeMappingNavigation.ts`

**Changes**:
- Remove hardcoded 90% threshold check
- Remove direct phase navigation
- Replace with agent recommendation display
- User actions trigger agent re-evaluation, not direct transitions

### Phase 4: Integration with Master Flow Orchestrator

#### 4.1 Ensure All Flows Use MFO Lifecycle

**Already Implemented** - No changes needed. Discovery flows already register with MFO.

#### 4.2 Add Agent Decision Points to MFO

**File**: `backend/app/services/flow_orchestration/execution_engine.py`

**Changes**:
- Add hooks for agent decision points
- Allow agents to influence execution flow
- Log all agent decisions for audit trail

### Phase 5: Implement Missing CrewAI Agents

#### 5.1 Field Mapping Agent

**File**: `backend/app/services/crewai_flows/crews/field_mapping_crew.py`

**Implementation**:
```python
class FieldMappingCrew(Crew):
    """Real CrewAI implementation for field mapping"""
    
    agents = [
        Agent(
            role="Data Schema Analyst",
            goal="Analyze source data schema and identify mapping patterns",
            tools=[SchemaAnalysisTool(), PatternRecognitionTool()]
        ),
        Agent(
            role="Business Context Mapper",
            goal="Apply business context to determine critical fields",
            tools=[BusinessRulesEngine(), ContextAnalyzer()]
        )
    ]
```

## Implementation Timeline

### Week 1: Agent Decision Making
- [ ] Implement FieldMappingDecisionAgent
- [ ] Implement PhaseTransitionAgent
- [ ] Remove hardcoded business logic
- [ ] Test agent decision accuracy

### Week 2: Real-Time Communication
- [ ] Implement WebSocket endpoint
- [ ] Connect agent-ui-bridge to flow execution
- [ ] Update frontend to use WebSocket
- [ ] Remove polling logic

### Week 3: Frontend Updates
- [ ] Convert frontend to passive viewer
- [ ] Remove hardcoded thresholds
- [ ] Display agent recommendations
- [ ] Test end-to-end flow

### Week 4: Testing & Refinement
- [ ] Integration tests
- [ ] Performance optimization
- [ ] Agent training/tuning
- [ ] Documentation updates

## Success Metrics

1. **Zero Hardcoded Business Logic** - All decisions made by agents
2. **Real-Time Updates** - No polling, all updates via WebSocket
3. **Agent Autonomy** - Agents control phase transitions
4. **Frontend Simplification** - Frontend only displays, doesn't orchestrate
5. **Flow Completion Rate** - >95% successful autonomous completion

## Risk Mitigation

1. **Agent Decisions Too Conservative**: Implement confidence thresholds with override capability
2. **Performance Impact**: Use background tasks for heavy agent processing
3. **User Confusion**: Clear UI showing agent reasoning and recommendations
4. **Backward Compatibility**: Maintain API contracts, only change internals

## NOT Included (Already Exists)

- Master Flow Orchestrator architecture
- State persistence mechanisms
- Multi-tenant isolation
- Error handling and recovery
- Background task execution
- Basic agent-UI bridge infrastructure
- Flow pause/resume capabilities

## Key Differentiator

This plan focuses on **removing bypasses** rather than building new systems. We're enabling the existing CrewAI agents to actually make decisions rather than just execute tasks, and connecting the existing agent-UI bridge to provide real-time updates rather than using polling.

The result will be a truly autonomous Discovery flow that leverages all the existing infrastructure while removing the hardcoded logic that currently bypasses the agentic capabilities.