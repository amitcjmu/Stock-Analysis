# Modularized Repository Pattern - Parameter Propagation

## Problem: Parameter Mismatch in Layered Repository Architecture

**Error**:
```
AssessmentFlowRepository.create_assessment_flow() got an unexpected keyword argument 'collection_flow_id'
```

**Root Cause**: Modularized repository had parameter added to implementation but not to facade/wrapper

## Architecture: Three-Layer Repository Pattern

```
base_repository.py (Facade)
    ↓ delegates to
commands/flow_commands.py (Implementation)
    ↓ calls
CrewAIFlowStateExtensionsRepository (MFO)
```

## Solution: Propagate Parameters Through ALL Layers

When adding a new parameter to modularized repositories, update EVERY layer:

### Layer 1: Implementation (flow_commands.py)
```python
async def create_assessment_flow(
    self,
    engagement_id: str,
    selected_application_ids: List[str],
    created_by: Optional[str] = None,
    collection_flow_id: Optional[str] = None,  # ✅ Added
) -> str:
    """Implementation logic"""
```

### Layer 2: Facade (base_repository.py)
```python
async def create_assessment_flow(
    self,
    engagement_id: str,
    selected_application_ids: List[str],
    created_by: Optional[str] = None,
    collection_flow_id: Optional[str] = None,  # ✅ Must add here too
) -> str:
    return await self._flow_commands.create_assessment_flow(
        engagement_id,
        selected_application_ids,
        created_by,
        collection_flow_id  # ✅ Pass through
    )
```

### Layer 3: Service Integration (MFO registration)
```python
await extensions_repo.create_master_flow(
    flow_id=str(flow_record.id),
    flow_type="assessment",
    # ... other params ...
    collection_flow_id=collection_flow_id,  # ✅ Use new parameter
)
```

## Repository Pattern Files to Check

When modifying assessment flow repository:
1. `backend/app/repositories/assessment_flow_repository/base_repository.py` - Facade
2. `backend/app/repositories/assessment_flow_repository/commands/flow_commands.py` - Implementation
3. `backend/app/services/collection_transition_service.py` - Service caller

When modifying MFO repository:
1. `backend/app/repositories/crewai_flow_state_extensions_repository.py` - Facade
2. `backend/app/repositories/crewai_flow_state_extensions/commands.py` - Implementation
3. Any service calling MFO operations

## Verification Checklist

After adding a parameter:
- [ ] Added to implementation method signature
- [ ] Added to facade method signature
- [ ] Passed through in facade delegation call
- [ ] Updated all callers to pass parameter
- [ ] Backend restart successful (no TypeError on startup)
- [ ] Test endpoint with new parameter

## Common Mistake Pattern

❌ **Wrong**: Only updating the implementation
```python
# commands.py - UPDATED
async def create_flow(..., new_param: str):
    ...

# base_repository.py - FORGOTTEN
async def create_flow(...):  # Missing new_param
    return await self.commands.create_flow(...)  # TypeError!
```

✅ **Correct**: Update both layers synchronously
```python
# commands.py
async def create_flow(..., new_param: str):
    ...

# base_repository.py
async def create_flow(..., new_param: str):  # Added
    return await self.commands.create_flow(..., new_param)  # Pass through
```

## Usage

When adding cross-cutting concerns (like collection_flow_id for asset resolution):
1. Start from the implementation layer (commands.py)
2. Work upward to facade (base_repository.py)
3. Work downward to dependencies (MFO repository if needed)
4. Update all service callers
5. Restart backend to catch missing signatures early
