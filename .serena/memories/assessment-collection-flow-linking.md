# Assessment → Collection Flow Linking Pattern

## Problem
Clicking "Collect Missing Data" from assessment returns wrong collection flow with different applications. User expected "Admin Dashboard" but got flow with "1.9.3", "2.0.0", "2.3.1" (corrupted server assets).

## Root Cause
`ensure_collection_flow()` returned ANY active collection flow for engagement without checking `assessment_flow_id` linkage.

## Solution Architecture
Link collection flows to specific assessment flows via `assessment_flow_id` foreign key.

### Database Schema
```sql
-- migration.collection_flows table has assessment_flow_id column
assessment_flow_id UUID REFERENCES assessment_flows(id)
```

### Frontend Changes

**1. ReadinessDashboardWidget.tsx**
```typescript
// Pass assessment_flow_id to ensureFlow()
const collectionFlow = await collectionFlowApi.ensureFlow(
  missing_attributes,
  flow_id  // assessment_flow_id
);

// Use flow_id (UUID) not id (database PK) for navigation
navigate(`/collection/adaptive-forms?flowId=${collectionFlow.flow_id || collectionFlow.id}`);
```

**2. flows.ts API client**
```typescript
async ensureFlow(
  missing_attributes?: Record<string, string[]>,
  assessment_flow_id?: string  // NEW parameter
): Promise<CollectionFlowResponse> {
  const body: Record<string, unknown> = {};
  if (missing_attributes) body.missing_attributes = missing_attributes;
  if (assessment_flow_id) body.assessment_flow_id = assessment_flow_id;

  return await apiCall(`${this.baseUrl}/flows/ensure`, {
    method: "POST",
    body: JSON.stringify(body)
  });
}
```

### Backend Changes

**1. Endpoint - collection.py**
```python
@router.post("/flows/ensure", response_model=CollectionFlowResponse)
async def ensure_collection_flow(
    request_body: Optional[Dict[str, Any]] = None,
    # ... other params
):
    assessment_flow_id = None
    if request_body:
        assessment_flow_id = request_body.get("assessment_flow_id")

    return await collection_crud.ensure_collection_flow(
        # ... other params
        assessment_flow_id=assessment_flow_id,
    )
```

**2. Query Logic - queries.py**
```python
async def ensure_collection_flow(
    # ... params
    assessment_flow_id: str | None = None,
):
    # Build query conditions
    query_conditions = [
        CollectionFlow.client_account_id == context.client_account_id,
        CollectionFlow.engagement_id == context.engagement_id,
        CollectionFlow.status.notin_([COMPLETED, CANCELLED]),
    ]

    # Filter by assessment_flow_id if provided
    if assessment_flow_id:
        assessment_uuid = UUID(assessment_flow_id) if isinstance(assessment_flow_id, str) else assessment_flow_id
        query_conditions.append(CollectionFlow.assessment_flow_id == assessment_uuid)

    result = await db.execute(
        select(CollectionFlow).where(*query_conditions)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return existing

    # Create new flow with assessment link
    flow_data = CollectionFlowCreate(
        assessment_flow_id=assessment_flow_id  # Store the link
    )
```

**3. Schema - collection_flow.py**
```python
class CollectionFlowCreate(BaseModel):
    assessment_flow_id: Optional[str] = Field(
        default=None,
        description="UUID of assessment flow to link to"
    )
```

**4. Flow Creation - collection_crud_create_commands.py**
```python
# Parse assessment_flow_id to UUID
assessment_uuid = None
if flow_data.assessment_flow_id:
    assessment_uuid = UUID(flow_data.assessment_flow_id) if isinstance(flow_data.assessment_flow_id, str) else flow_data.assessment_flow_id

collection_flow = CollectionFlow(
    # ... other fields
    assessment_flow_id=assessment_uuid,  # Store the link
)
```

## Usage Pattern
When user clicks "Collect Missing Data" from any assessment:
1. Frontend passes assessment UUID
2. Backend checks for existing collection flows WITH that assessment_flow_id
3. If none found, creates new flow linked to that assessment
4. Each assessment gets its own collection flow (no mixing of data)

## Verification
```sql
-- Check flow linkage
SELECT cf.flow_id, cf.assessment_flow_id, af.id as assessment_id
FROM migration.collection_flows cf
LEFT JOIN migration.assessment_flows af ON cf.assessment_flow_id = af.id
WHERE cf.flow_id = '10ee28e9-e3fb-4b41-81ff-19cf05bb783e';

-- Should show proper assessment_flow_id, not NULL
```

## Key Insight
Always scope "ensure" or "get_or_create" operations by ALL relevant foreign keys, not just tenant context.
