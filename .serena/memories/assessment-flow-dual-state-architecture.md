# Assessment Flow Dual State Architecture

## Why There Are Two `AssessmentFlowState` Classes

The codebase has **TWO intentionally different** `AssessmentFlowState` classes serving **distinct architectural purposes**.

## The Two Models

### 1. Pydantic Model (API/Database Layer)
- **Location**: `backend/app/models/assessment_flow_state/flow_state_models.py`
- **Type**: `BaseModel` (Pydantic v2)
- **Import**: `from app.models.assessment_flow_state import AssessmentFlowState`
- **Purpose**:
  - API request/response validation
  - Database persistence (PostgreSQL JSONB)
  - Type-safe data transfer objects
  - Frontend contract enforcement
  - Repository/service layer operations

```python
class AssessmentFlowState(BaseModel):
    """Complete assessment flow state with all components"""
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    flow_id: UUID = Field(..., description="Unique flow identifier")
    client_account_id: UUID = Field(...)
    # ... strict Pydantic validation
```

### 2. In-Memory Model (CrewAI Integration Layer)
- **Location**: `backend/app/models/assessment_flow/in_memory_models.py`
- **Type**: Plain Python class (no Pydantic)
- **Import**: `from app.models.assessment_flow import AssessmentFlowState`
- **Purpose**:
  - CrewAI agent execution context
  - Avoid Pydantic serialization overhead during agent processing
  - Mutable state for agent operations
  - No validation during rapid state changes
  - Agent helper classes

```python
class AssessmentFlowState:
    """
    In-memory assessment flow state for CrewAI integration.

    This class provides a simplified interface for CrewAI crews to work with
    assessment flow data without direct database dependencies.
    """
    def __init__(self, flow_id: str, engagement_id: str, ...):
        # Plain Python attributes - no Pydantic validation
        self.flow_id = flow_id
        self.sixr_decisions: List[InMemorySixRDecision] = []
```

## Why This Architecture Exists

### Problem 1: Pydantic Validation Overhead in Agent Loops

CrewAI agents make **hundreds of micro-state changes** during execution:
- Adding 6R decisions incrementally
- Updating phase progress
- Appending learning feedback
- Modifying component analysis

**With Pydantic**: Every attribute assignment triggers validation
- ❌ 100+ validations per flow execution
- ❌ Serialization/deserialization overhead
- ❌ Enum conversions on every field access

**With Plain Python**:
- ✅ Direct attribute mutation (fast)
- ✅ No validation penalty during agent execution
- ✅ Convert to Pydantic only when persisting to database

### Problem 2: CrewAI TaskOutput Serialization

From Serena memory `taskoutput_serialization_crewai.md`:

> CrewAI's `task.execute_async()` returns `TaskOutput` Pydantic objects, not plain strings. When passed to SQLAlchemy JSONB fields without extraction, causes:
> ```
> TypeError: Object of type TaskOutput is not JSON serializable
> ```

**Solution**: Use in-memory plain Python objects during agent execution, then extract and convert to Pydantic for persistence.

### Problem 3: Circular Import Prevention

Original architecture (single Pydantic model) created circular dependencies:
```
assessment_flow_state.py imports enums.py
  ↓
enums.py imports CrewAI agents
  ↓
agents import assessment_flow_state.py
  ↓
🔥 CIRCULAR IMPORT ERROR
```

**Fix**: Separate concerns:
- Pydantic models: API layer (no agent imports)
- In-memory models: Agent layer (no Pydantic imports)

## Architectural Pattern (MFO Integration - Commit 166d61bc7)

Introduced in October 2024 as part of Master Flow Orchestrator alignment:

```
┌─────────────────────────────────────────────┐
│         API Layer (FastAPI)                  │
│   Uses: AssessmentFlowState (Pydantic)      │
│   Purpose: Validation, Serialization        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│    Master Flow Orchestrator (MFO)           │
│    Converts: Pydantic → In-Memory           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│       CrewAI Agent Execution                │
│   Uses: AssessmentFlowState (Plain Python)  │
│   Purpose: Fast mutation, agent context     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│      Database Persistence                   │
│   Converts: In-Memory → Pydantic → JSONB   │
└─────────────────────────────────────────────┘
```

## Real-World Usage Example

**CrewAI Agent Helper** (`backend/app/services/crewai_flows/assessment_flow/strategy_analysis_helper.py:11`):

```python
from app.models.assessment_flow import AssessmentFlowState, InMemorySixRDecision

class StrategyAnalysisHelper:
    def __init__(self, flow_state: AssessmentFlowState):  # ← In-memory version
        self.flow_state = flow_state

    def analyze_component_for_sixr(self, component, context) -> InMemorySixRDecision:
        # Fast mutations during agent processing - no validation overhead
        decision = InMemorySixRDecision(
            component_id=component_id,
            sixr_strategy=strategy,
            confidence=confidence
        )
        return decision
```

**Database Persistence** (conversion to Pydantic):

```python
# Convert in-memory → Pydantic for validation/persistence
pydantic_state = AssessmentFlowStatePydantic(
    flow_id=in_memory_state.flow_id,
    sixr_decisions=[decision.to_dict() for decision in in_memory_state.sixr_decisions]
)
await db.save(pydantic_state.model_dump())
```

## Decision Matrix: Which Model to Use?

| Context | Use Pydantic Model | Use In-Memory Model |
|---------|-------------------|---------------------|
| API endpoints | ✅ Yes | ❌ No |
| Database operations | ✅ Yes | ❌ No |
| Repository layer | ✅ Yes | ❌ No |
| Repository tests | ✅ Yes | ❌ No |
| Service layer (API-facing) | ✅ Yes | ❌ No |
| CrewAI agent execution | ❌ No | ✅ Yes |
| Agent helper classes | ❌ No | ✅ Yes |
| Rapid state mutations | ❌ No | ✅ Yes |
| Flow state tracking | ❌ No | ✅ Yes |

## Common Import Mistakes

### ❌ WRONG - Using In-Memory for Database Tests
```python
# This will cause import failures in repository tests
from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase
```

### ✅ CORRECT - Using Pydantic for Database Tests
```python
# Repository tests need Pydantic for validation
from app.models.assessment_flow_state import AssessmentFlowState, AssessmentPhase
```

### ❌ WRONG - Using Pydantic in Agent Helpers
```python
# This adds validation overhead during agent execution
from app.models.assessment_flow_state import AssessmentFlowState
```

### ✅ CORRECT - Using In-Memory in Agent Helpers
```python
# Fast mutations, no validation penalty
from app.models.assessment_flow import AssessmentFlowState
```

## Test Failure Pattern

**Symptom**: Tests get skipped with "REPOSITORY_AVAILABLE = False"

**Root Cause**: Test file imports in-memory model instead of Pydantic model

**Example** (`tests/backend/assessment_flow/test_modules/repository_tests/common.py:23`):
```python
try:
    from app.models.assessment_flow import AssessmentFlowState  # ❌ WRONG
    REPOSITORY_AVAILABLE = True
except ImportError:
    REPOSITORY_AVAILABLE = False  # Tests get skipped
```

**Fix**:
```python
try:
    from app.models.assessment_flow_state import AssessmentFlowState  # ✅ CORRECT
    REPOSITORY_AVAILABLE = True
except ImportError:
    REPOSITORY_AVAILABLE = False
```

## Historical Context

- **Introduced**: October 2024 (Commit 166d61bc7)
- **Reason**: MFO Integration + CrewAI Performance
- **Pattern Name**: "MFO Dual State Architecture"
- **Related ADRs**: ADR-006 (MFO), ADR-024 (TenantMemoryManager)

## Key Takeaway

This is **NOT accidental duplication** - it's **intentional architectural separation** between:
1. **API/Persistence Layer** (Pydantic) - strict validation, database operations
2. **Agent Execution Layer** (Plain Python) - fast mutations, no validation overhead

The architecture solves three critical problems:
1. Pydantic validation performance in agent loops
2. CrewAI TaskOutput serialization issues
3. Circular import dependencies

When in doubt: **Database/API → Pydantic**, **CrewAI/Agents → In-Memory**
