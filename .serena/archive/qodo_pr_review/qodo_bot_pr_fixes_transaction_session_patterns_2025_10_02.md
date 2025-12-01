# Qodo Bot PR Fixes - Transaction and Session Patterns

**Context**: Fixed 6 code review issues from Qodo Bot feedback - critical transaction atomicity, session lifecycle, and data corruption bugs

## 1. Transaction Atomicity Pattern - Nested Operations

**Problem**: Nested commits breaking transaction atomicity in `status_commands.py`
```python
# ❌ WRONG - Nested commits break atomicity
async def update_flow_status(self, flow_id, new_status):
    async with self.db.begin():
        await self._update_master_flow(...)  # Contains commit()
        await self._update_child_flow(...)   # Contains commit()
    # Transaction broken - partial updates possible
```

**Solution**: Internal methods use `flush()`, outer method owns `commit()`
```python
# ✅ CORRECT - Single transaction boundary
async def update_flow_status_atomically(self, flow_id, new_status, metadata):
    async with self.db.begin():
        # Update master flow without intermediate commit
        master_result = await self._update_master_flow_in_transaction(flow_id, new_status, metadata)
        # Update child flow without intermediate commit
        child_result = await self._update_child_flow_in_transaction(flow_id, new_status, flow_type)
    # Transaction commits here - all or nothing

async def _update_master_flow_in_transaction(self, flow_id, new_status, metadata):
    """Internal method - flushes but does NOT commit"""
    master_flow = await self.db.get(MasterFlowModel, flow_id)
    master_flow.status = new_status
    await self.db.flush()  # Make visible to transaction, don't commit
    return master_flow

async def _update_child_flow_in_transaction(self, flow_id, new_status, flow_type):
    """Internal method - flushes but does NOT commit"""
    child_flow = await self.db.get(ChildFlowModel, flow_id)
    child_flow.status = new_status
    await self.db.flush()  # Make visible to transaction, don't commit
    return child_flow
```

**Usage**: When coordinating updates across multiple tables that MUST succeed/fail together

## 2. Database Session Lifecycle - Async Context Managers

**Problem**: Session closed before use in utility functions
```python
# ❌ WRONG - Session closes immediately after return
async def create_flow_manager(context: RequestContext) -> FlowStateManager:
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        return FlowStateManager(db, context)  # Session closes here!
    # Caller gets manager with closed session
```

**Solution**: Use `@asynccontextmanager` to keep session alive
```python
# ✅ CORRECT - Session stays open for caller
from contextlib import asynccontextmanager

@asynccontextmanager
async def create_flow_manager(context: RequestContext):
    """Create flow manager with managed session lifecycle"""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        yield FlowStateManager(db, context)  # Session stays open
    # Session closes when caller exits 'async with' block

# Usage:
async with create_flow_manager(context) as manager:
    await manager.update_flow_state(...)  # Session still open
# Session closes here
```

**Linting Fix**: Import must be at top of file
```python
# ✅ Line 12 - Top of file
from contextlib import asynccontextmanager

# ❌ Line 201 - Inside code (E402 error)
# from contextlib import asynccontextmanager
```

**Usage**: Utility functions that need to manage database sessions across caller's scope

## 3. Data Corruption Prevention - Field Order Consistency

**Problem**: Inconsistent field order causing row data misalignment in `suggestion_service.py`
```python
# ❌ WRONG - Field order changes per record
for record in sample_records:
    if record.raw_data:
        source_fields = list(record.raw_data.keys())  # Order may vary!
        sample_data_rows.append(list(record.raw_data.values()))
# Result: ["name", "ip"] → ["Alice", "10.0.0.1"]
#         ["ip", "name"] → ["10.0.0.2", "Bob"]  # CORRUPTED!
```

**Solution**: Establish field order from first record, enforce for all
```python
# ✅ CORRECT - Consistent field order
source_fields = []
sample_data_rows = []

for idx, record in enumerate(sample_records):
    if record.raw_data:
        if idx == 0:
            # Establish consistent field order from first record
            source_fields = list(record.raw_data.keys())
            logger.info(f"Established field order: {source_fields}")

        # Ensure values align with established field order
        if source_fields:
            ordered_values = [record.raw_data.get(field) for field in source_fields]
            sample_data_rows.append(ordered_values)
```

**Usage**: Any time constructing tabular data from dict/JSON records where field order matters

## 4. Error Handling - State Cleanup on Failure

**Problem**: Partial agent state left on creation failure
```python
# ❌ WRONG - Mixed valid/fallback agents
try:
    agents.append(create_agent_1())
    agents.append(create_agent_2())  # Fails here
    agents.append(create_agent_3())  # Never reached
except Exception as e:
    logger.error(f"Failed: {e}")
    # agents now has 1 valid agent + no fallback
```

**Solution**: Clear partial state before creating fallback
```python
# ✅ CORRECT - Clean state on failure
try:
    agents.append(create_agent_1())
    agents.append(create_agent_2())
    agents.append(create_agent_3())
except Exception as e:
    logger.error(f"Failed to create agents: {e}", exc_info=True)  # Full traceback
    agents.clear()  # Clear partial state
    # Create single fallback agent
    fallback_agent = Agent(role="fallback", ...)
    agents.append(fallback_agent)
```

**Usage**: Multi-step initialization where partial state is invalid

## 5. Defensive Programming - Bounds Checking

**Problem**: Index out of bounds when accessing list elements
```python
# ❌ WRONG - Assumes agents list has elements
tools = []
if hasattr(self.agents[0], "tools"):  # Crashes if empty!
    tools = self.agents[0].tools
```

**Solution**: Check list size before access
```python
# ✅ CORRECT - Bounds checking
tools = []
if self.agents and hasattr(self.agents[0], "tools"):
    tools = self.agents[0].tools
```

**Usage**: Always when accessing list elements by index

## 6. Manager Selection - Use Appropriate Service

**Problem**: Using wrong manager for operations in `basic_commands.py`
```python
# ❌ WRONG - Using state store for checkpoints
await self.store.create_checkpoint(...)  # store is for state, not checkpoints!
```

**Solution**: Use purpose-built manager
```python
# ✅ CORRECT - Using checkpoint manager
await self.secure_checkpoint_manager.create_checkpoint(
    flow_id=flow_id,
    phase="cleanup",
    state=current_state,
    metadata={"cleanup_archive": True},
    context=self.context,
)
```

**Usage**: Always use the manager designed for specific operations (checkpoints, state, recovery, etc.)

## Pre-commit Success Pattern

All fixes passed:
- ✅ Black reformatting (re-stage files after auto-format)
- ✅ Flake8 (E402 import location fixed)
- ✅ Mypy type checking
- ✅ File length checks (<400 LOC)
- ✅ Security scans (bandit, secrets detection)

**Files Modified**: 6 backend Python files (suggestion_service.py, status_commands.py, flow_state_manager/__init__.py, basic_commands.py, agents.py.deprecated, tasks.py.deprecated)

**Patterns Source**: All fixes aligned with `docs/analysis/Notes/coding-agent-guide.md`
