# Asset to Canonical Application Mapping Endpoint

## Overview

The `/api/v1/canonical-applications/map-asset` endpoint creates mappings between assets and canonical applications via the `CollectionFlowApplication` junction table. This enables application-level assessments, dependency tracking, and improved data association for collection flows.

## Endpoint Details

**URL**: `POST /api/v1/canonical-applications/map-asset`

**Authentication**: Required (via RequestContext headers)

**Content-Type**: `application/json`

## Request Headers

```http
X-Client-Account-ID: <client-account-uuid>
X-Engagement-ID: <engagement-uuid>
Content-Type: application/json
```

## Request Body

```typescript
{
  "asset_id": string,                      // Required: Asset UUID to map
  "canonical_application_id": string,      // Required: Canonical application UUID
  "collection_flow_id": string | null      // Optional: Collection flow ID for traceability
}
```

### Request Model (Pydantic)

```python
class MapAssetRequest(BaseModel):
    """Request to map an asset to a canonical application"""

    asset_id: str = Field(..., description="Asset UUID to map")
    canonical_application_id: str = Field(..., description="Canonical application UUID")
    collection_flow_id: Optional[str] = Field(None, description="Optional collection flow ID for traceability")
```

## Response Body

```typescript
{
  "success": boolean,      // Always true on success
  "message": string,       // Human-readable success message
  "mapping_id": string     // UUID of created/existing mapping
}
```

### Response Model (Pydantic)

```python
class MapAssetResponse(BaseModel):
    """Response after mapping asset"""

    success: bool
    message: str
    mapping_id: str  # UUID of created CollectionFlowApplication record
```

## Behavior

### Idempotency

The endpoint is **idempotent**. If a mapping already exists between the asset and canonical application:
- Returns HTTP 200 with `success: true`
- Returns the existing `mapping_id`
- Message indicates the mapping already exists
- No duplicate record is created

### Validation

1. **Client Account & Engagement**: Must be present in request headers
2. **UUID Format**: All UUIDs must be valid format
3. **Asset Existence**: Asset must exist and belong to the tenant (client_account_id + engagement_id)
4. **Application Existence**: Canonical application must exist and belong to the tenant
5. **Multi-Tenant Scoping**: All queries filtered by client_account_id and engagement_id

### Created Record

When creating a new mapping, the following fields are populated in `CollectionFlowApplication`:

```python
{
    "id": uuid.uuid4(),
    "asset_id": asset_uuid,
    "canonical_application_id": canonical_app_uuid,
    "collection_flow_id": collection_flow_uuid,  # Optional
    "application_name": canonical_app.canonical_name,  # Legacy field
    "client_account_id": client_account_id,
    "engagement_id": engagement_id,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}
```

## Error Responses

### 400 Bad Request - Missing Tenant Context

```json
{
  "detail": "Client account ID and engagement ID required"
}
```

### 400 Bad Request - Invalid UUID Format

```json
{
  "detail": "Invalid UUID format: badly formed hexadecimal UUID string"
}
```

### 404 Not Found - Asset Not Found

```json
{
  "detail": "Asset {asset_id} not found or access denied"
}
```

### 404 Not Found - Application Not Found

```json
{
  "detail": "Canonical application {canonical_application_id} not found or access denied"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Failed to create mapping: {error_message}"
}
```

## Example Usage

### Using cURL

```bash
curl -X POST http://localhost:8000/api/v1/canonical-applications/map-asset \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Engagement-ID: 123e4567-e89b-12d3-a456-426614174001" \
  -d '{
    "asset_id": "123e4567-e89b-12d3-a456-426614174002",
    "canonical_application_id": "123e4567-e89b-12d3-a456-426614174003"
  }'
```

### Success Response Example

```json
{
  "success": true,
  "message": "Successfully mapped asset 'MySQL Database' to application 'E-Commerce Platform'",
  "mapping_id": "123e4567-e89b-12d3-a456-426614174004"
}
```

### Idempotent Response (Already Mapped)

```json
{
  "success": true,
  "message": "Asset 'MySQL Database' is already mapped to application 'E-Commerce Platform'",
  "mapping_id": "123e4567-e89b-12d3-a456-426614174004"
}
```

### Using Python Requests

```python
import requests

url = "http://localhost:8000/api/v1/canonical-applications/map-asset"

headers = {
    "Content-Type": "application/json",
    "X-Client-Account-ID": "123e4567-e89b-12d3-a456-426614174000",
    "X-Engagement-ID": "123e4567-e89b-12d3-a456-426614174001"
}

payload = {
    "asset_id": "123e4567-e89b-12d3-a456-426614174002",
    "canonical_application_id": "123e4567-e89b-12d3-a456-426614174003",
    "collection_flow_id": "123e4567-e89b-12d3-a456-426614174005"  # Optional
}

response = requests.post(url, json=payload, headers=headers)
print(response.status_code)  # 200
print(response.json())
```

### Using TypeScript/Fetch

```typescript
const response = await fetch('/api/v1/canonical-applications/map-asset', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Client-Account-ID': clientAccountId,
    'X-Engagement-ID': engagementId,
  },
  body: JSON.stringify({
    asset_id: assetId,
    canonical_application_id: canonicalApplicationId,
    collection_flow_id: collectionFlowId, // Optional
  }),
});

if (!response.ok) {
  throw new Error(`Failed to map asset: ${response.statusText}`);
}

const data = await response.json();
console.log(data.message); // "Successfully mapped asset..."
console.log(data.mapping_id); // UUID of mapping
```

## Database Impact

### Table: `migration.collection_flow_applications`

Each successful mapping creates a record in this junction table:

```sql
SELECT
    id,
    asset_id,
    canonical_application_id,
    collection_flow_id,
    application_name,
    client_account_id,
    engagement_id,
    created_at,
    updated_at
FROM migration.collection_flow_applications
WHERE asset_id = :asset_id
  AND canonical_application_id = :canonical_app_id
  AND client_account_id = :client_account_id
  AND engagement_id = :engagement_id;
```

## Use Cases

### 1. Map Non-Application Assets to Applications

Map databases, servers, and network devices to their parent applications:

```json
{
  "asset_id": "database-uuid",
  "canonical_application_id": "ecommerce-platform-uuid"
}
```

### 2. Collection Flow Integration

Track which collection flow created the mapping:

```json
{
  "asset_id": "server-uuid",
  "canonical_application_id": "crm-system-uuid",
  "collection_flow_id": "collection-flow-uuid"
}
```

### 3. Assessment Preparation

Create mappings to enable application-level assessments:

```json
{
  "asset_id": "load-balancer-uuid",
  "canonical_application_id": "web-portal-uuid"
}
```

## Security Considerations

1. **Multi-Tenant Isolation**: All queries scoped by `client_account_id` and `engagement_id`
2. **Ownership Validation**: Both asset and application must belong to the same tenant
3. **UUID Validation**: Prevents SQL injection via parameterized queries
4. **Audit Trail**: All mappings logged with timestamps and tenant context

## Testing

### Manual Testing via Docker

```bash
# 1. Start Docker environment
cd config/docker && docker-compose up -d

# 2. Get valid UUIDs from database
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
  SELECT id, name, asset_type
  FROM migration.assets
  WHERE client_account_id = '00000000-0000-0000-0000-000000000001'
  LIMIT 1;
"

docker exec -it migration_postgres psql -U postgres -d migration_db -c "
  SELECT id, canonical_name
  FROM migration.canonical_applications
  WHERE client_account_id = '00000000-0000-0000-0000-000000000001'
  LIMIT 1;
"

# 3. Call endpoint with valid UUIDs
curl -X POST http://localhost:8000/api/v1/canonical-applications/map-asset \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 00000000-0000-0000-0000-000000000001" \
  -H "X-Engagement-ID: 00000000-0000-0000-0000-000000000002" \
  -d '{
    "asset_id": "<asset-uuid-from-step-2>",
    "canonical_application_id": "<app-uuid-from-step-2>"
  }'

# 4. Verify mapping created
docker exec -it migration_postgres psql -U postgres -d migration_db -c "
  SELECT * FROM migration.collection_flow_applications
  WHERE asset_id = '<asset-uuid-from-step-2>'
    AND canonical_application_id = '<app-uuid-from-step-2>';
"
```

### Automated Testing

```python
# tests/backend/integration/test_canonical_applications.py

import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_map_asset_to_application_success(
    async_client: AsyncClient,
    test_asset,
    test_canonical_application,
    test_context_headers
):
    """Test successful asset mapping"""
    response = await async_client.post(
        "/api/v1/canonical-applications/map-asset",
        json={
            "asset_id": str(test_asset.id),
            "canonical_application_id": str(test_canonical_application.id)
        },
        headers=test_context_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "mapping_id" in data
    assert "MySQL Database" in data["message"]

@pytest.mark.asyncio
async def test_map_asset_idempotency(
    async_client: AsyncClient,
    test_asset,
    test_canonical_application,
    test_context_headers
):
    """Test idempotent behavior"""
    # First mapping
    response1 = await async_client.post(
        "/api/v1/canonical-applications/map-asset",
        json={
            "asset_id": str(test_asset.id),
            "canonical_application_id": str(test_canonical_application.id)
        },
        headers=test_context_headers
    )

    # Second mapping (should return same mapping_id)
    response2 = await async_client.post(
        "/api/v1/canonical-applications/map-asset",
        json={
            "asset_id": str(test_asset.id),
            "canonical_application_id": str(test_canonical_application.id)
        },
        headers=test_context_headers
    )

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["mapping_id"] == response2.json()["mapping_id"]

@pytest.mark.asyncio
async def test_map_asset_not_found(
    async_client: AsyncClient,
    test_canonical_application,
    test_context_headers
):
    """Test asset not found error"""
    response = await async_client.post(
        "/api/v1/canonical-applications/map-asset",
        json={
            "asset_id": str(uuid4()),  # Non-existent asset
            "canonical_application_id": str(test_canonical_application.id)
        },
        headers=test_context_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
```

## Implementation Details

### File Location

- **Router**: `/backend/app/api/v1/canonical_applications/router.py`
- **Models**: Inline in router file (MapAssetRequest, MapAssetResponse)
- **Database Model**: `/backend/app/models/canonical_applications/collection_flow_app.py`

### Dependencies

- FastAPI for endpoint definition
- SQLAlchemy for database operations
- Pydantic for request/response validation
- Multi-tenant RequestContext for security

### Logging

All operations are logged at INFO level:

```python
logger.info(f"✅ Created mapping: asset '{asset.name}' ({asset_id}) → "
            f"application '{canonical_app.canonical_name}' ({canonical_app_id})")

logger.info(f"Mapping already exists: asset {asset_id} → app {canonical_app_id}")
```

Errors are logged at ERROR level with full stack traces:

```python
logger.error(f"Failed to map asset to application: {str(e)}", exc_info=True)
```

## Related Documentation

- `/docs/adr/012-master-child-flow-separation.md` - Two-table pattern
- `/docs/guidelines/API_REQUEST_PATTERNS.md` - API conventions
- `/backend/app/models/canonical_applications/` - Data models
- `/backend/app/api/v1/canonical_applications/bulk_mapping.py` - Bulk operations
