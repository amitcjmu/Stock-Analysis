# ADR-022: Asset Inventory Persistent Agent Architecture

## Status
Accepted (2025-09-10)

## Context

The asset inventory phase in discovery flows is currently implemented using a multi-agent CrewAI crew (`InventoryBuildingCrew`) that exhibits infinite loops, excessive hallucinations, and fails to create actual database asset records. Analysis of backend logs and code review reveals fundamental architectural issues that require a different approach.

### Current Problem: Over-Engineered Multi-Agent Crew

#### Root Cause Analysis
1. **Circular Agent Conversations**: The crew contains 4+ agents (Inventory Manager, Server Classification Expert, Application Discovery Expert, Device Classification Expert) that continuously coordinate with each other, creating endless conversation loops.

2. **Recursive Tool Dependencies**: Tools create circular logic patterns:
   ```python
   # problematic tools in inventory_building_crew.py
   - task_completion_checker  # Checks if work is done instead of doing work
   - asset_deduplication_checker  # Creates checking loops
   - execution_coordinator  # Agents coordinate instead of execute
   ```

3. **Analysis Paralysis**: 100+ line agent backstories create over-thinking scenarios where agents spend cycles on coordination rather than execution.

4. **Unnecessary Complexity**: Shared memory, knowledge base setup, and cross-domain validation add overhead without benefit for the core task of creating database records.

#### Current Implementation Problems
```python
# In inventory_building_crew.py - PROBLEMATIC PATTERN
class InventoryBuildingCrew:
    def create_agents(self):
        # 4+ agents that coordinate endlessly
        inventory_manager = Agent(...)  # Coordinates other agents
        server_expert = Agent(...)      # Talks to manager
        app_expert = Agent(...)         # Talks to manager  
        device_expert = Agent(...)      # Talks to manager
```

**Result**: Asset inventory phase completes in 0.05s with no actual assets created, or runs indefinitely in coordination loops.

### Evidence from Backend Logs
```
✅ inventory crew created successfully
╭─────────────────────────── Crew Execution Started ───────────────────────────╮
╭──────────────────────────────── Crew Failure ────────────────────────────────╮
ERROR - Asset inventory failed: Error interpolating description: Invalid value for key 'flow_id': Unsupported type UUID
```

The crew architecture is fundamentally incompatible with the straightforward task of creating asset database records from cleaned CMDB data.

## Decision

Replace the multi-agent CrewAI crew with a **single persistent agent** architecture that:

1. **Uses Existing Persistent Agent Infrastructure**: Leverage the proven `TenantScopedAgentPool` pattern used successfully in other phases
2. **Single Agent Execution**: Eliminate agent coordination overhead and infinite loops
3. **Direct Database Operations**: Use existing `create_asset_creation_tools` for direct database persistence
4. **Minimal Tool Set**: Only essential tools without coordination/checking complexity
5. **Clear Single Purpose**: Transform cleaned data → create asset records → return counts

### Architectural Pattern
```python
# New implementation pattern - SOLUTION
async def _execute_discovery_asset_inventory(self, agent_pool, phase_input):
    # Get persistent agent (no crew creation)
    agent = await TenantScopedAgentPool.get_agent(
        context=self.context,
        agent_type="asset_inventory_agent"
    )
    
    # Direct agent execution with serialized inputs
    result = await agent.execute_async(
        task="Create database asset records from cleaned CMDB data",
        context=serializable_input
    )
```

### Agent Configuration
- **Agent Type**: `"asset_inventory_agent"`
- **Tools**: `create_asset_creation_tools` + `create_data_validation_tools`
- **Goal**: "Create database asset records efficiently from cleaned CMDB data"
- **Backstory**: Focused 2-3 line description emphasizing direct execution over analysis

## Consequences

### Positive
- ✅ **Eliminates Infinite Loops**: Single agent removes coordination conversations
- ✅ **Prevents Hallucinations**: Focused tools prevent creative interpretation
- ✅ **Direct Database Access**: Asset creation tools handle persistence correctly
- ✅ **Consistent with Codebase**: Uses proven persistent agent patterns from other phases
- ✅ **Performance**: Fast execution without crew coordination overhead
- ✅ **Debuggable**: Single agent behavior is easier to trace and fix
- ✅ **Tenant Persistence**: Agent memory accumulates asset classification expertise

### Negative
- ⚠️ **Loss of Multi-Domain Expertise**: Single agent vs domain specialists (acceptable trade-off)
- ⚠️ **Refactoring Required**: Existing crew integration needs replacement
- ⚠️ **Tool Integration**: Need to ensure asset creation tools work with persistent agents

### Neutral
- 🔄 **Consistency**: Aligns asset inventory with other discovery phases using persistent agents
- 🔄 **Maintainability**: Simpler architecture reduces maintenance burden

## Implementation

### Phase 1: Create Persistent Asset Inventory Agent
1. Define agent configuration in persistent agent system
2. Configure with `create_asset_creation_tools`
3. Add asset inventory agent type to tool manager

### Phase 2: Replace Crew Execution
1. Modify `_execute_discovery_asset_inventory` method
2. Replace crew creation with persistent agent retrieval
3. Update input serialization for agent compatibility

### Phase 3: Verification
1. Test asset creation from cleaned data
2. Verify database persistence
3. Confirm UI inventory page population

## References
- ADR-015: Persistent Multi-Tenant Agent Architecture (foundation)
- `backend/app/services/persistent_agents/` (existing infrastructure)
- `backend/app/services/flow_orchestration/execution_engine_crew_discovery.py` (implementation target)