# Phase Executor Implementation Patterns

## Architecture Context
Phase executors in `execution_engine_crew_discovery/` delegate to specialized handlers in `crewai_flows/handlers/phase_executors/`.

## Common Pattern: AssetInventoryExecutor

### File Structure
```
phase_executors.py (_execute_discovery_asset_inventory)
    └─> AssetInventoryExecutor.execute_asset_creation()
            └─> AssetService (direct execution, NO crews)
```

### Implementation Template

```python
async def _execute_discovery_phase(
    self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute phase using specialized executor"""
    
    # 1. Import executor and state classes
    from app.services.crewai_flows.handlers.phase_executors.phase_executor import (
        PhaseExecutor,
    )
    from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
    
    # 2. Create minimal state object (required by BasePhaseExecutor.__init__)
    state = UnifiedDiscoveryFlowState()
    state.flow_id = phase_input.get("flow_id") or phase_input.get("master_flow_id")
    state.client_account_id = self.context.client_account_id
    state.engagement_id = self.context.engagement_id
    
    # 3. Initialize executor (state may not be used by execute method)
    executor = PhaseExecutor(state, crew_manager=None, flow_bridge=None)
    
    # 4. Build flow_context with ACTUAL execution data
    data_import_id = phase_input.get("data_import_id")
    flow_context = {
        "flow_id": phase_input.get("flow_id"),
        "master_flow_id": phase_input.get("master_flow_id") or phase_input.get("flow_id"),
        "data_import_id": str(data_import_id) if data_import_id else None,  # UUID→string
        "client_account_id": self.context.client_account_id,
        "engagement_id": self.context.engagement_id,
        "user_id": self.context.user_id,
        "db_session": self.db_session,  # Active transaction
    }
    
    # 5. Execute (NO transaction nesting - session already has one)
    try:
        result = await executor.execute_phase(flow_context)
        
        # 6. Flush to make IDs available for FK relationships
        await self.db_session.flush()
        
        # 7. Persist phase completion flag if successful
        if result.get("status") == "success":
            from app.models.discovery_flow import DiscoveryFlow
            master_flow_id = phase_input.get("master_flow_id")
            await self.db_session.execute(
                update(DiscoveryFlow)
                .where(DiscoveryFlow.master_flow_id == master_flow_id)
                .values(phase_completed=True)
            )
            await self.db_session.commit()
        
        return {
            "phase": "phase_name",
            "status": "completed",
            "crew_results": result,
            "agent": "phase_agent",
        }
        
    except Exception as e:
        logger.error(f"❌ Phase failed: {e}")
        return {
            "phase": "phase_name",
            "status": "error",
            "error": str(e),
        }
```

## Key Patterns

### UUID to String Conversion (Pydantic Validation)
```python
# Pydantic models expect strings, not UUID objects
data_import_id = phase_input.get("data_import_id")
flow_context = {
    "data_import_id": str(data_import_id) if data_import_id else None
}
```

### State vs flow_context
- **state**: Required by BasePhaseExecutor.__init__ (interface requirement)
- **flow_context**: Actual execution data passed to execute methods
- Modern executors use flow_context, not state

### Direct Execution Pattern (AssetInventoryExecutor)
- Uses `AssetService` directly (NO crews)
- `execute_asset_creation(flow_context)` is entry point
- Applies field mappings during asset creation
- Classification logic built-in

## Files to Reference
- `phase_executors.py`: Phase delegation methods
- `asset_inventory_executor.py`: Direct execution example
- `data_cleansing_executor.py`: Crew-based execution example
