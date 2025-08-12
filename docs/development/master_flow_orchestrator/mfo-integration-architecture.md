# MFO Integration Architecture for Agentic Discovery Flow

## Overview

This document explains how the agentic Discovery flow improvements integrate with the existing Master Flow Orchestrator (MFO) architecture without creating redundant systems.

## Current MFO Architecture

The Master Flow Orchestrator uses a **modular composition pattern** with these components:

```
Master Flow Orchestrator
├── FlowLifecycleManager (lifecycle operations)
├── FlowExecutionEngine (execution logic)
├── FlowErrorHandler (error handling)
├── FlowPerformanceMonitor (performance tracking)
├── FlowAuditLogger (audit logging)
├── FlowStatusManager (status management)
└── Registries
    ├── FlowTypeRegistry (flow type definitions)
    ├── ValidatorRegistry (validation logic)
    └── HandlerRegistry (flow handlers)
```

## Integration Points for Agentic Improvements

### 1. **Agent Decision Integration**

The agentic improvements will integrate at the **FlowExecutionEngine** level:

```python
# In FlowExecutionEngine
async def execute_flow_phase(self, flow_id: str, phase: str):
    # Existing logic
    handler = self.handler_registry.get_handler(flow_type)
    
    # NEW: Agent decision point
    if self.agent_decision_enabled:
        decision_agent = self.get_phase_decision_agent(flow_type, phase)
        next_action = await decision_agent.analyze_and_decide(
            current_phase=phase,
            flow_state=state,
            phase_results=results
        )
        
        # Agent can override default flow
        if next_action.override_default:
            return await self.execute_agent_decision(next_action)
    
    # Continue with existing flow
    return await handler.execute_phase(phase)
```

### 2. **Real-Time Updates via Agent-UI Bridge**

The Agent-UI Bridge will be connected at the **FlowStatusManager** level:

```python
# In FlowStatusManager
async def update_flow_status(self, flow_id: str, status: str, metadata: Dict):
    # Existing status update
    await super().update_flow_status(flow_id, status, metadata)
    
    # NEW: Broadcast to Agent-UI Bridge
    from app.services.agent_ui_bridge import agent_ui_bridge
    await agent_ui_bridge.broadcast_flow_update(
        flow_id=flow_id,
        update_type="status_change",
        data={
            "status": status,
            "metadata": metadata,
            "timestamp": datetime.utcnow()
        }
    )
```

### 3. **Agent Audit Trail**

Agent decisions will be logged through the existing **FlowAuditLogger**:

```python
# Agent decisions become first-class audit events
self.audit_logger.log_event(
    flow_id=flow_id,
    category=AuditCategory.AGENT_DECISION,
    level=AuditLevel.INFO,
    message="Agent recommended phase transition",
    metadata={
        "agent": "PhaseTransitionAgent",
        "current_phase": "field_mapping",
        "recommended_phase": "data_cleansing",
        "confidence": 0.95,
        "reasoning": agent_decision.reasoning
    }
)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Master Flow Orchestrator                         │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ Lifecycle Mgr   │  │ Execution Engine │  │ Status Manager  │   │
│  │                 │  │                  │  │                 │   │
│  │ • Create flows  │  │ • Execute phases │  │ • Track status  │   │
│  │ • Delete flows  │  │ • AGENT DECIDES │  │ • AGENT UPDATES │   │
│  │                 │  │   NEXT PHASE    │  │   VIA BRIDGE    │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘   │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ Error Handler   │  │ Performance Mon  │  │ Audit Logger    │   │
│  │                 │  │                  │  │                 │   │
│  │ • Retry logic   │  │ • Track metrics  │  │ • LOG AGENT     │   │
│  │ • Recovery      │  │ • Resource usage │  │   DECISIONS     │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CrewAI Flow Layer                             │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ Discovery Flow  │  │ Assessment Flow  │  │ Planning Flow   │   │
│  │                 │  │                  │  │                 │   │
│  │ WITH AUTONOMOUS │  │ WITH AUTONOMOUS  │  │ WITH AUTONOMOUS │   │
│  │ AGENT DECISIONS │  │ AGENT DECISIONS  │  │ AGENT DECISIONS │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Agent-UI Bridge                              │
│                                                                      │
│  • WebSocket connections for real-time updates                      │
│  • Agent insights and recommendations                               │
│  • User feedback loop to agents                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Integration Benefits

### 1. **No New Orchestration System**
We're not creating a separate orchestration system for each flow type. The MFO remains the single orchestrator, with agents providing intelligent decision-making within the existing framework.

### 2. **Leverage Existing Infrastructure**
- FlowLifecycleManager continues to manage lifecycle
- FlowExecutionEngine gains agent decision capabilities
- FlowAuditLogger captures agent decisions
- FlowStatusManager broadcasts real-time updates

### 3. **Consistent Across All Flow Types**
The same agent decision pattern will work for:
- Discovery flows
- Assessment flows  
- Planning flows
- Execution flows
- All future flow types

### 4. **Backward Compatible**
Flows can operate with or without agent decisions:
```python
# Configuration option
flow_config = {
    "agent_decisions_enabled": True,  # New flows
    "fallback_to_hardcoded": True    # Safety net
}
```

## Implementation Approach

### Phase 1: Discovery Flow Pilot
1. Implement agent decisions in Discovery flow only
2. Test and refine the integration patterns
3. Measure improvements in automation

### Phase 2: Extend to Other Flows
1. Apply learnings to Assessment flow
2. Then Planning and Execution flows
3. Ensure consistency across all flows

### Phase 3: Advanced Features
1. Cross-flow agent coordination
2. Learning from historical decisions
3. Predictive flow optimization

## Not Creating New Infrastructure

We are **NOT** creating:
- ❌ New orchestration systems per flow type
- ❌ Parallel flow execution engines
- ❌ Duplicate state management
- ❌ Alternative audit systems

We **ARE** enhancing:
- ✅ Existing MFO with agent decision points
- ✅ Existing flows with autonomous capabilities
- ✅ Existing audit trail with agent decisions
- ✅ Existing status updates with real-time streaming

## Summary

The agentic improvements integrate seamlessly with the MFO architecture by:
1. Adding agent decision points to FlowExecutionEngine
2. Connecting Agent-UI Bridge to FlowStatusManager
3. Logging agent decisions through FlowAuditLogger
4. Maintaining all existing MFO benefits (multi-tenancy, error handling, performance monitoring)

This approach ensures we build on the solid foundation of the MFO rather than creating competing systems, while enabling true autonomous agent-driven workflows.