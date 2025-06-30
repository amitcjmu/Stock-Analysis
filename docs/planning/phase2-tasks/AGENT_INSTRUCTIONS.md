# Phase 2 Parallel Agent Execution Instructions

## Overview
This document provides copy-paste instructions for creating 5 parallel Agent conversations to execute Phase 2 of the remediation plan.

## Current Status
- **Phase 1**: Should be complete (V3 APIs, PostgreSQL state management)
- **Phase 1.5**: V3 Persistence Layer (AGENT_E1) should be in progress or complete
- **Phase 2**: Ready to begin architectural transformation to CrewAI patterns

## Agent Setup Instructions

### 🟢 Agent C1 - Context Management (START IMMEDIATELY)
**Dependencies**: None - Can start immediately

Create a new Agent conversation with:
```
Please execute the Phase 2 remediation task defined in:
docs/planning/phase2-tasks/AGENT_C1_CONTEXT_MANAGEMENT.md

Follow the coordination guide at:
docs/planning/phase2-tasks/PHASE2_COORDINATION_GUIDE.md

This is Agent C1 focusing on context management and multi-tenant infrastructure. This task has NO dependencies and can start immediately.

Key deliverables:
- Enhanced context framework with ContextVars
- Context-aware base classes
- Database RLS policies
- Context middleware

Please begin implementation following the task file instructions.
```

### 🟡 Agent A1 - Agent System Core (START AFTER PHASE 1 COMPLETE)
**Dependencies**: Phase 1 must be complete

Create a new Agent conversation with:
```
Please execute the Phase 2 remediation task defined in:
docs/planning/phase2-tasks/AGENT_A1_AGENT_SYSTEM_CORE.md

Follow the coordination guide at:
docs/planning/phase2-tasks/PHASE2_COORDINATION_GUIDE.md

This is Agent A1 focusing on core agent infrastructure and registry. 

Prerequisites check:
- Phase 1 V3 APIs should be complete
- PostgreSQL state management should be working

Key deliverables:
- Agent registry with auto-discovery
- Base agent classes
- Convert 13 agents to CrewAI patterns
- Agent factory

Please begin implementation following the task file instructions.
```

### 🟡 Agent B1 - Flow Framework (START AFTER PHASE 1 COMPLETE)
**Dependencies**: Phase 1 V3 APIs must be complete

Create a new Agent conversation with:
```
Please execute the Phase 2 remediation task defined in:
docs/planning/phase2-tasks/AGENT_B1_FLOW_FRAMEWORK.md

Follow the coordination guide at:
docs/planning/phase2-tasks/PHASE2_COORDINATION_GUIDE.md

This is Agent B1 focusing on CrewAI Flow framework with @start/@listen decorators.

Prerequisites check:
- API v3 consolidation from Phase 1 should be complete
- PostgreSQL-only state management should be ready

Key deliverables:
- Base flow framework with CrewAI patterns
- Discovery flow with @start/@listen decorators
- Flow manager for lifecycle
- Event bus integration

Please begin implementation following the task file instructions.
```

### 🔴 Agent A2 - Crew Management (START AFTER A1 PROVIDES AGENT REGISTRY)
**Dependencies**: Must wait for A1 to provide agent registry

Create a new Agent conversation with:
```
Please execute the Phase 2 remediation task defined in:
docs/planning/phase2-tasks/AGENT_A2_CREW_MANAGEMENT.md

Follow the coordination guide at:
docs/planning/phase2-tasks/PHASE2_COORDINATION_GUIDE.md

This is Agent A2 focusing on crew factory and task orchestration.

IMPORTANT: This task depends on Agent A1's deliverables:
- Agent registry must be available at: backend/app/services/agents/registry.py
- Base agent classes must be implemented

If these are not ready, please wait or implement minimal stubs to proceed.

Key deliverables:
- Base crew class
- Crew factory
- Specialized crews (field mapping, data cleansing, etc.)
- Task orchestration patterns

Please begin implementation following the task file instructions.
```

### 🔴 Agent D1 - Tool System (START AFTER C1 PROVIDES CONTEXT PATTERNS)
**Dependencies**: Should wait for C1 to provide context patterns

Create a new Agent conversation with:
```
Please execute the Phase 2 remediation task defined in:
docs/planning/phase2-tasks/AGENT_D1_TOOL_SYSTEM.md

Follow the coordination guide at:
docs/planning/phase2-tasks/PHASE2_COORDINATION_GUIDE.md

This is Agent D1 focusing on tool system implementation.

IMPORTANT: This task benefits from Agent C1's context patterns:
- Context-aware base classes from: backend/app/core/context_aware.py
- Context framework from: backend/app/core/context.py

If C1 hasn't completed yet, you can start with tool registry and base classes.

Key deliverables:
- Tool registry with auto-discovery
- Base tool classes
- Core tools (schema analyzer, field matcher, PII scanner)
- Tool factory

Please begin implementation following the task file instructions.
```

## Execution Timeline

### Day 1 (Immediate)
- Start C1 (Context) - No dependencies
- Start A1 (Agents) - If Phase 1 complete
- Start B1 (Flows) - If Phase 1 complete

### Day 2-3
- Start A2 (Crews) - Once A1 provides registry
- Start D1 (Tools) - Once C1 provides context

### Integration Points
- **Day 3**: First integration sync
- **Day 5**: Full integration testing
- **Day 7**: Final testing and merge

## Coordination Tips

1. **Branch Naming**: Each agent should create branches like:
   - `feature/phase2-c1-context-management`
   - `feature/phase2-a1-agent-registry`

2. **PR Communication**: Agents should update their PRs daily with:
   - Completed work
   - Current focus
   - Any blockers
   - Integration needs

3. **Shared Interfaces**: Agents should check these locations:
   - Agent Registry: `backend/app/services/agents/registry.py`
   - Context: `backend/app/core/context.py`
   - Tools: `backend/app/services/tools/registry.py`
   - Crews: `backend/app/services/crews/factory.py`

## Critical Path
```
C1 (Context) ──┬──> A1 (Agents) ──> A2 (Crews) ──┐
               └──> D1 (Tools) ───────────────────┴──> B1 (Flows)
```

## Success Criteria
Each agent should verify:
- [ ] Unit tests pass (>85% coverage)
- [ ] Integration points work with other agents
- [ ] No context leakage between tenants
- [ ] Performance targets met
- [ ] Documentation updated

## Emergency Contact
If agents encounter blocking issues:
1. Check if other agents have pushed partial implementations
2. Create minimal stubs to continue progress
3. Document the blocker in PR description
4. Continue with other parts of the task

---
*Note: Save this file and use it to create the 5 parallel agent conversations*