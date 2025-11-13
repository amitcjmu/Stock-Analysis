# Frontend-Backend Schema Mismatch - Detection and Resolution

## Common Symptom Patterns

### 1. NaN% in UI
**Symptom**: Percentage displays show "NaN%"
**Root Cause**: `Math.round(undefined * 100)` when backend field missing
**Example**: Issue #875 - Data cleansing confidence scores

**Detection**:
```typescript
// Browser console shows:
// NaN% confidence

// Code shows:
<span>{Math.round(rec.confidence * 100)}% confidence</span>

// Backend response missing:
{
  "id": "123",
  "title": "Fix data",
  // ❌ NO confidence field
}
```

**Fix Pattern**:
```python
# Backend: Add optional field with default
class Recommendation(BaseModel):
    id: str
    title: str
    confidence: Optional[float] = 0.85  # Prevents NaN

# Frontend: Add defensive null check
{rec.confidence !== undefined && rec.confidence !== null
  ? `${Math.round(rec.confidence * 100)}%`
  : 'N/A'}
```

### 2. Buttons Always Disabled
**Symptom**: Interactive buttons grayed out, cannot click
**Root Cause**: `disabled={rec.field !== 'expected'}` when field undefined
**Example**: Issue #876 - Apply/Reject buttons

**Detection**:
```typescript
// Button logic:
<Button disabled={rec.status !== 'pending'}>Apply</Button>

// Evaluates to:
disabled={undefined !== 'pending'}  // = true (always disabled)

// Backend response:
{
  "id": "123",
  // ❌ NO status field
}
```

**Fix Pattern**:
```python
# Backend: Add field with enabling default
class Recommendation(BaseModel):
    status: str = 'pending'  # Default enables buttons

# Frontend: Optional defensive check
disabled={rec.status !== 'pending' || !rec.status}
```

### 3. Empty Lists/Tables
**Symptom**: "No items" despite data existing
**Root Cause**: Frontend maps over undefined array field

**Detection**:
```typescript
// Code:
{items.map(item => <Card key={item.id} />)}

// Runtime error or empty render when:
items = undefined  // Backend didn't return items array
```

**Fix Pattern**:
```python
# Backend: Return empty array, not null
class Response(BaseModel):
    items: List[Item] = []  # Not Optional[List[Item]]

# Frontend: Defensive
{(items || []).map(item => ...)}
```

## Systematic Debugging Process

### Step 1: Network Tab Investigation
```typescript
// Open browser DevTools → Network → Find API call
// Click response → Preview tab

// Check JSON structure matches TypeScript interface
interface Expected {
  confidence: number;    // ✅ Present in response?
  status: string;        // ✅ Present in response?
  items: Array<Item>;    // ✅ Present in response?
}
```

### Step 2: Backend Schema Verification
```bash
# Find Pydantic model
rg "class DataCleansingRecommendation" backend/

# Read model definition
cat backend/app/api/v1/endpoints/data_cleansing/base.py

# Compare to frontend TypeScript interface
cat src/services/dataCleansingService.ts
```

### Step 3: Add Missing Fields
```python
# Backend: Update Pydantic model
from typing import Optional, List

class MyModel(BaseModel):
    # Existing fields
    id: str
    title: str

    # Add missing fields that frontend expects
    confidence: Optional[float] = None  # Optional if sometimes missing
    status: str = 'pending'  # Required with default
    items: List[str] = []  # Empty list default
```

### Step 4: Update Response Generation
```python
# Find where model instances are created
rg "MyModel\(" backend/

# Update all creation sites
return MyModel(
    id=str(uuid.uuid4()),
    title="Sample",
    confidence=0.85,  # ADD: New field
    status='pending',  # ADD: New field
    items=['item1'],  # ADD: New field
)
```

### Step 5: Update TypeScript Interface
```typescript
// Match backend exactly
interface MyModel {
  id: string;
  title: string;
  confidence?: number;  // Optional matches Optional[float]
  status: string;       // Required matches str
  items: string[];      // Array matches List[str]
}
```

### Step 6: Update Test Fixtures
```python
# backend/tests/test_fixtures.py
@pytest.fixture
def sample_data():
    return MyModel(
        id="test-123",
        title="Test",
        confidence=0.9,   # ADD: Match production
        status='pending',  # ADD: Match production
        items=['test'],    # ADD: Match production
    )
```

## Prevention Strategies

### 1. Contract-First Development
```typescript
// Define TypeScript interface FIRST
interface DataModel {
  id: string;
  confidence: number;
  status: 'pending' | 'applied' | 'rejected';
}

// Then implement backend to match
// Use interface as API contract documentation
```

### 2. Schema Validation Tests
```python
# backend/tests/test_schemas.py
def test_model_has_required_fields():
    """Ensure model matches frontend expectations."""
    model = MyModel(id="1", title="Test")

    # Assert frontend-expected fields exist
    assert hasattr(model, 'confidence')
    assert hasattr(model, 'status')
    assert hasattr(model, 'items')

    # Assert defaults work
    assert model.status == 'pending'
    assert model.items == []
```

### 3. OpenAPI/Swagger Documentation
```python
# FastAPI generates OpenAPI schema automatically
# Frontend can validate responses against it

from fastapi import FastAPI

app = FastAPI()

@app.get("/api/data", response_model=MyModel)
def get_data():
    return MyModel(...)  # FastAPI validates response
```

## Common Field Patterns

### Confidence Scores
```python
# Backend
confidence: Optional[float] = None  # 0.0 to 1.0 range
# Or with validation:
from pydantic import Field
confidence: float = Field(default=0.85, ge=0.0, le=1.0)
```

### Status Fields
```python
# Backend
from enum import Enum

class Status(str, Enum):
    PENDING = 'pending'
    APPLIED = 'applied'
    REJECTED = 'rejected'

status: Status = Status.PENDING
```

```typescript
// Frontend
type Status = 'pending' | 'applied' | 'rejected';
status: Status;
```

### Optional vs Required
```python
# Optional: May be absent
items: Optional[List[str]] = None

# Required with default: Always present
items: List[str] = []

# Required no default: Must be provided
items: List[str]  # Validation error if missing
```

## Real-World Example: Issues #875, #876

**Context**: Data cleansing recommendations

**Frontend Expected**:
```typescript
interface DataCleansingRecommendation {
  id: string;
  confidence: number;           // ❌ Missing in backend
  status: string;               // ❌ Missing in backend
  agent_source: string;         // ❌ Missing in backend
  implementation_steps: string[]; // ❌ Missing in backend
}
```

**Backend Provided**:
```python
class DataCleansingRecommendation(BaseModel):
    id: str
    category: str
    title: str
    # ... other fields ...
    # ❌ confidence, status, agent_source, implementation_steps MISSING
```

**Symptoms**:
- Confidence displayed as "NaN%"
- Apply/Reject buttons always disabled

**Fix Applied**:
```python
class DataCleansingRecommendation(BaseModel):
    id: str
    category: str
    title: str
    # ... existing fields ...

    # ✅ Added missing fields
    confidence: Optional[float] = 0.85
    status: str = 'pending'
    agent_source: Optional[str] = 'Data Quality Agent'
    implementation_steps: Optional[List[str]] = []
```

**Result**:
- Confidence displays as "85%", "92%", etc.
- Buttons enabled (status='pending' by default)
- Zero breaking changes (optional fields with defaults)

## Diagnostic Checklist

When debugging UI issues:

- [ ] Check browser console for NaN, undefined errors
- [ ] Inspect Network tab → API response structure
- [ ] Compare response JSON to TypeScript interface
- [ ] Find Pydantic model in backend
- [ ] Check if field exists in model
- [ ] Check if field populated in response generation
- [ ] Add missing field with sensible default
- [ ] Update TypeScript interface to match
- [ ] Update test fixtures
- [ ] Add defensive null checks in UI
- [ ] Test with real API response

## Quick Fix Template

```python
# 1. Backend model update
class MyModel(BaseModel):
    existing_field: str
    new_field: Optional[float] = 0.85  # ADD THIS

# 2. Response generation update
def create_response():
    return MyModel(
        existing_field="value",
        new_field=0.92  # ADD THIS
    )

# 3. TypeScript interface update
interface MyModel {
  existingField: string;
  newField?: number;  // ADD THIS
}

# 4. Frontend defensive check
{model.newField !== undefined
  ? `${model.newField}`
  : 'N/A'}
```

## Related Memory
- See: `automated_bug_fix_multi_agent_workflow_2025_11` for bug fix process
- See: `coding-agent-guide.md` for snake_case convention (backend uses snake_case, frontend now matches)
