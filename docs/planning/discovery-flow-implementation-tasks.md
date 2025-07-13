# Discovery Flow Implementation Tasks - Team Coordination Plan

## Overview

This document breaks down the Discovery Flow Agentic Implementation into specific tasks organized for parallel AI agent teams. Each team has clear responsibilities, dependencies, and deliverables.

## Team Structure

### Team Alpha: Agent Decision Engine
**Focus**: Implement autonomous agent decision-making logic

### Team Bravo: Real-Time Communication
**Focus**: Connect Agent-UI Bridge with WebSocket/SSE

### Team Charlie: Frontend Refactoring
**Focus**: Convert frontend to passive event-driven viewer

### Team Delta: Integration & Testing
**Focus**: End-to-end integration and test coverage

## Implementation Phases & Tasks

### Phase 0: Foundation Setup (All Teams - Day 1)
**Objective**: Ensure all teams understand the architecture and have access to required files

#### Task 0.1: Architecture Review [All Teams]
- **Description**: Review implementation plan and MFO integration architecture
- **Files to Study**:
  - `/docs/planning/discovery-flow-agentic-implementation-plan.md`
  - `/docs/planning/mfo-integration-architecture.md`
  - `/backend/app/services/master_flow_orchestrator.py`
  - `/backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py`
- **Deliverable**: Team acknowledgment of architecture understanding
- **Duration**: 2 hours
- **Dependencies**: None

#### Task 0.2: Development Environment Setup [Team Delta]
- **Description**: Create feature branches and setup test environment
- **Actions**:
  - Create feature branch: `feature/agentic-discovery-flow`
  - Setup integration test framework
  - Create mock data for testing
- **Deliverable**: Development environment ready
- **Duration**: 2 hours
- **Dependencies**: None

### Phase 1: Core Agent Implementation (Day 1-3)

#### Task 1.1: Create Agent Decision Framework [Team Alpha]
- **Description**: Build the base framework for agent decision-making
- **File to Create**: `/backend/app/services/crewai_flows/agents/decision_agents.py`
- **Implementation**:
  ```python
  from crewai import Agent, Task
  from abc import ABC, abstractmethod
  
  class BaseDecisionAgent(Agent):
      """Base class for all decision-making agents"""
      
      @abstractmethod
      async def analyze_phase_transition(self, current_phase, results, state):
          """Analyze and decide next phase transition"""
          pass
  
  class PhaseTransitionAgent(BaseDecisionAgent):
      """Agent that decides phase transitions based on data analysis"""
      
      def __init__(self):
          super().__init__(
              role="Flow Orchestration Strategist",
              goal="Determine optimal phase transitions based on data quality and business context",
              backstory="Expert in workflow optimization and data quality assessment"
          )
  ```
- **Deliverable**: Base decision agent framework
- **Duration**: 4 hours
- **Dependencies**: Task 0.1

#### Task 1.2: Implement Field Mapping Decision Agent [Team Alpha]
- **Description**: Replace hardcoded field mapping logic with intelligent agent
- **File to Modify**: `/backend/app/services/crewai_flows/unified_discovery_flow/phases/field_mapping.py`
- **Key Changes**:
  - Remove hardcoded 90% threshold
  - Remove hardcoded critical fields list
  - Implement dynamic threshold calculation based on data quality
  - Add agent reasoning for field criticality
- **Deliverable**: Working FieldMappingDecisionAgent
- **Duration**: 6 hours
- **Dependencies**: Task 1.1

#### Task 1.3: Create Agent Tools for Analysis [Team Alpha]
- **Description**: Build tools that agents use for decision-making
- **File to Create**: `/backend/app/services/crewai_flows/agents/analysis_tools.py`
- **Tools to Implement**:
  - `DataQualityAnalyzer`: Assess data quality metrics
  - `FieldComplexityAnalyzer`: Determine field mapping complexity
  - `BusinessContextAnalyzer`: Apply business rules to decisions
  - `HistoricalPatternMatcher`: Learn from past decisions
- **Deliverable**: Agent analysis tools
- **Duration**: 6 hours
- **Dependencies**: Task 1.1

### Phase 2: Real-Time Communication (Day 2-4)

#### Task 2.1: Implement WebSocket Endpoint [Team Bravo]
- **Description**: Create WebSocket endpoint for real-time flow updates
- **File to Create**: `/backend/app/api/v1/endpoints/agent_communication.py`
- **Implementation**:
  ```python
  from fastapi import WebSocket, WebSocketDisconnect
  from app.services.agent_ui_bridge import agent_ui_bridge
  
  @router.websocket("/ws/flow/{flow_id}")
  async def flow_updates_websocket(websocket: WebSocket, flow_id: str):
      await websocket.accept()
      
      # Subscribe to flow updates
      async for update in agent_ui_bridge.subscribe_to_flow(flow_id):
          await websocket.send_json(update)
  ```
- **Deliverable**: Working WebSocket endpoint
- **Duration**: 4 hours
- **Dependencies**: Task 0.1

#### Task 2.2: Connect Agent-UI Bridge to Flow Execution [Team Bravo]
- **Description**: Wire up existing agent-ui-bridge to broadcast flow updates
- **Files to Modify**:
  - `/backend/app/services/flow_orchestration/status_manager.py`
  - `/backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py`
- **Key Changes**:
  - Add agent_ui_bridge imports
  - Broadcast status updates in real-time
  - Send agent insights and decisions
- **Deliverable**: Real-time flow updates working
- **Duration**: 6 hours
- **Dependencies**: Task 2.1

#### Task 2.3: Implement Event Subscription System [Team Bravo]
- **Description**: Create subscription mechanism for frontend clients
- **File to Create**: `/backend/app/services/event_bus.py`
- **Features**:
  - Flow-specific event channels
  - Client subscription management
  - Event filtering and routing
  - Automatic cleanup on disconnect
- **Deliverable**: Event subscription system
- **Duration**: 4 hours
- **Dependencies**: Task 2.1

### Phase 3: Frontend Refactoring (Day 3-5)

#### Task 3.1: Create WebSocket Hook [Team Charlie]
- **Description**: Replace polling with WebSocket connection
- **File to Create**: `/src/hooks/useFlowWebSocket.ts`
- **Implementation**:
  ```typescript
  import { useEffect, useState } from 'react';
  
  export const useFlowWebSocket = (flowId: string) => {
      const [updates, setUpdates] = useState([]);
      const [connected, setConnected] = useState(false);
      
      useEffect(() => {
          const ws = new WebSocket(`/api/v1/ws/flow/${flowId}`);
          
          ws.onmessage = (event) => {
              const update = JSON.parse(event.data);
              setUpdates(prev => [...prev, update]);
          };
          
          return () => ws.close();
      }, [flowId]);
      
      return { updates, connected };
  };
  ```
- **Deliverable**: WebSocket hook for React
- **Duration**: 3 hours
- **Dependencies**: Task 2.1 completion

#### Task 3.2: Remove Polling Logic [Team Charlie]
- **Description**: Remove all polling-based status checks
- **Files to Modify**:
  - `/src/hooks/useUnifiedDiscoveryFlow.ts`
  - `/src/hooks/discovery/useAttributeMappingLogic.ts`
- **Key Changes**:
  - Remove `refetchInterval` configurations
  - Remove polling state management
  - Replace with WebSocket updates
- **Deliverable**: No more polling in frontend
- **Duration**: 4 hours
- **Dependencies**: Task 3.1

#### Task 3.3: Remove Hardcoded Business Logic [Team Charlie]
- **Description**: Remove all hardcoded thresholds and business rules
- **Files to Modify**:
  - `/src/hooks/discovery/attribute-mapping/useAttributeMappingActions.ts`
  - `/src/hooks/discovery/useAttributeMappingNavigation.ts`
- **Key Removals**:
  - 90% approval threshold
  - Critical fields list
  - Direct phase navigation logic
  - Frontend orchestration decisions
- **Deliverable**: Frontend as passive viewer
- **Duration**: 6 hours
- **Dependencies**: Task 3.1

#### Task 3.4: Implement Agent Recommendation Display [Team Charlie]
- **Description**: Create UI components to display agent decisions
- **Files to Create**:
  - `/src/components/discovery/AgentInsights.tsx`
  - `/src/components/discovery/AgentRecommendations.tsx`
- **Features**:
  - Display agent reasoning
  - Show confidence scores
  - Present recommendations
  - Allow user override with justification
- **Deliverable**: Agent decision UI components
- **Duration**: 6 hours
- **Dependencies**: Task 3.2

### Phase 4: Integration Points (Day 4-6)

#### Task 4.1: Integrate Agent Decisions with MFO [Team Alpha + Team Delta]
- **Description**: Connect agent decisions to Master Flow Orchestrator
- **File to Modify**: `/backend/app/services/flow_orchestration/execution_engine.py`
- **Implementation**:
  ```python
  async def execute_flow_phase(self, flow_id: str, phase: str):
      # Get decision agent for this phase
      decision_agent = self.agent_registry.get_decision_agent(flow_type, phase)
      
      # Let agent analyze and decide
      decision = await decision_agent.analyze_phase_transition(
          current_phase=phase,
          results=phase_results,
          state=flow_state
      )
      
      # Log agent decision
      self.audit_logger.log_agent_decision(flow_id, decision)
      
      # Execute based on agent decision
      if decision.action == "proceed":
          return await self._proceed_to_phase(decision.next_phase)
      elif decision.action == "pause":
          return await self._pause_for_user(decision.reason)
  ```
- **Deliverable**: Agent decisions integrated with MFO
- **Duration**: 6 hours
- **Dependencies**: Tasks 1.2, 1.3

#### Task 4.2: Update Flow State Management [Team Alpha]
- **Description**: Ensure flow state includes agent decisions
- **File to Modify**: `/backend/app/models/unified_discovery_flow_state.py`
- **Additions**:
  - `agent_decisions: List[Dict]` - History of agent decisions
  - `current_agent_recommendation: Dict` - Active recommendation
  - `decision_overrides: List[Dict]` - User overrides of agent decisions
- **Deliverable**: Extended flow state model
- **Duration**: 3 hours
- **Dependencies**: Task 1.1

#### Task 4.3: Implement Agent Audit Trail [Team Delta]
- **Description**: Ensure all agent decisions are logged
- **File to Modify**: `/backend/app/services/flow_orchestration/audit_logger.py`
- **New Audit Categories**:
  - `AGENT_DECISION` - Agent makes a decision
  - `AGENT_ANALYSIS` - Agent analyzes data
  - `USER_OVERRIDE` - User overrides agent decision
  - `AGENT_LEARNING` - Agent learns from feedback
- **Deliverable**: Complete agent audit trail
- **Duration**: 4 hours
- **Dependencies**: Task 4.1

### Phase 5: Testing & Validation (Day 5-7)

#### Task 5.1: Create Unit Tests for Agents [Team Delta]
- **Description**: Test agent decision logic
- **File to Create**: `/backend/tests/test_agent_decisions.py`
- **Test Cases**:
  - Test data quality analysis
  - Test threshold calculations
  - Test phase transition logic
  - Test error handling
- **Deliverable**: Comprehensive unit tests
- **Duration**: 6 hours
- **Dependencies**: All Phase 1 tasks

#### Task 5.2: Create Integration Tests [Team Delta]
- **Description**: Test end-to-end flow with agent decisions
- **File to Create**: `/backend/tests/test_discovery_flow_e2e.py`
- **Test Scenarios**:
  - High quality data - automatic progression
  - Low quality data - agent pauses for review
  - Complex mappings - user approval required
  - Agent recommendation override
- **Deliverable**: E2E test suite
- **Duration**: 8 hours
- **Dependencies**: All Phase 1-4 tasks

#### Task 5.3: Performance Testing [Team Delta]
- **Description**: Ensure real-time updates don't impact performance
- **File to Create**: `/backend/tests/test_websocket_performance.py`
- **Metrics to Test**:
  - WebSocket connection handling (100+ concurrent)
  - Message throughput
  - Memory usage
  - CPU utilization
- **Deliverable**: Performance test results
- **Duration**: 4 hours
- **Dependencies**: Task 2.1, 2.2

#### Task 5.4: Create Frontend Integration Tests [Team Charlie + Team Delta]
- **Description**: Test frontend WebSocket integration
- **File to Create**: `/src/__tests__/discovery-flow-websocket.test.tsx`
- **Test Cases**:
  - WebSocket connection establishment
  - Real-time update handling
  - Reconnection logic
  - Error scenarios
- **Deliverable**: Frontend integration tests
- **Duration**: 4 hours
- **Dependencies**: All Phase 3 tasks

### Phase 6: Documentation & Deployment (Day 6-7)

#### Task 6.1: Update API Documentation [Team Bravo]
- **Description**: Document new WebSocket endpoints
- **Files to Update**:
  - API documentation
  - WebSocket protocol specification
  - Event message formats
- **Deliverable**: Updated API docs
- **Duration**: 3 hours
- **Dependencies**: Phase 2 completion

#### Task 6.2: Create Agent Decision Documentation [Team Alpha]
- **Description**: Document how agents make decisions
- **File to Create**: `/docs/architecture/agent-decision-making.md`
- **Contents**:
  - Agent roles and responsibilities
  - Decision criteria
  - Override mechanisms
  - Learning capabilities
- **Deliverable**: Agent documentation
- **Duration**: 3 hours
- **Dependencies**: Phase 1 completion

#### Task 6.3: Update Frontend Developer Guide [Team Charlie]
- **Description**: Document new event-driven patterns
- **File to Update**: `/docs/development/frontend-guide.md`
- **Topics**:
  - WebSocket usage
  - Event handling
  - Agent recommendation display
  - No more polling
- **Deliverable**: Updated frontend guide
- **Duration**: 3 hours
- **Dependencies**: Phase 3 completion

## Coordination Points

### Daily Sync Points
1. **Morning Standup** (All Teams)
   - Progress updates
   - Blocker identification
   - Dependency coordination

2. **Midday Integration Check** (Team Leads)
   - API contract verification
   - Integration point testing
   - Cross-team dependencies

3. **End of Day Review** (All Teams)
   - Code review submissions
   - Test results
   - Next day planning

### Critical Integration Milestones

#### Milestone 1: Agent Framework Complete (End of Day 2)
- Teams Alpha completes Tasks 1.1-1.3
- Integration point: Agent decision interface defined
- Validation: Unit tests pass

#### Milestone 2: WebSocket Infrastructure Ready (End of Day 3)
- Team Bravo completes Tasks 2.1-2.3
- Integration point: WebSocket endpoint live
- Validation: Can establish connections

#### Milestone 3: Frontend Connected (End of Day 4)
- Team Charlie completes Tasks 3.1-3.2
- Integration point: Frontend receives real-time updates
- Validation: No more polling

#### Milestone 4: Full Integration (End of Day 5)
- All teams complete integration tasks
- Integration point: End-to-end flow works
- Validation: Integration tests pass

## Dependency Matrix

| Task | Depends On | Blocks | Team |
|------|-----------|--------|------|
| 1.1 | 0.1 | 1.2, 1.3, 4.1 | Alpha |
| 1.2 | 1.1 | 4.1, 5.1 | Alpha |
| 1.3 | 1.1 | 4.1, 5.1 | Alpha |
| 2.1 | 0.1 | 2.2, 2.3, 3.1 | Bravo |
| 2.2 | 2.1 | 3.1, 5.3 | Bravo |
| 2.3 | 2.1 | 3.1 | Bravo |
| 3.1 | 2.1 | 3.2, 3.3, 3.4 | Charlie |
| 3.2 | 3.1 | 3.4, 5.4 | Charlie |
| 3.3 | 3.1 | 3.4, 5.4 | Charlie |
| 3.4 | 3.2 | 5.4 | Charlie |
| 4.1 | 1.2, 1.3 | 5.2 | Alpha + Delta |
| 4.2 | 1.1 | 4.1 | Alpha |
| 4.3 | 4.1 | 5.2 | Delta |
| 5.1 | Phase 1 | - | Delta |
| 5.2 | All Phase 1-4 | 6.3 | Delta |
| 5.3 | 2.1, 2.2 | 6.1 | Delta |
| 5.4 | Phase 3 | 6.3 | Charlie + Delta |

## Risk Mitigation

### Risk 1: Agent Decisions Too Conservative
- **Mitigation**: Implement confidence thresholds with admin overrides
- **Owner**: Team Alpha
- **Fallback**: Configurable automatic progression

### Risk 2: WebSocket Scalability
- **Mitigation**: Implement connection pooling and rate limiting
- **Owner**: Team Bravo
- **Fallback**: Graceful degradation to polling

### Risk 3: Frontend State Synchronization
- **Mitigation**: Implement optimistic updates with reconciliation
- **Owner**: Team Charlie
- **Fallback**: Full state refresh on reconnection

## Success Criteria

1. **No Hardcoded Business Logic**
   - All thresholds determined by agents
   - No critical fields list in code
   - Phase transitions agent-driven

2. **Real-Time Updates Working**
   - WebSocket connections stable
   - Updates received within 100ms
   - No polling anywhere

3. **Agent Decisions Auditable**
   - All decisions logged
   - Reasoning accessible
   - Override history maintained

4. **Performance Maintained**
   - Response time < 200ms
   - Support 100+ concurrent flows
   - Memory usage stable

5. **User Experience Improved**
   - Clear agent recommendations
   - Smooth real-time updates
   - Intuitive override mechanism