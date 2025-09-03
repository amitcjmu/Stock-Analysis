# API Endpoint Patterns and Usage

## Collection Flow Endpoints
- `/api/v1/collection/flows/{flow_id}` - Get flow details
- `/api/v1/collection/flows/{flow_id}/questionnaires` - Get questionnaires (returns bootstrap if none exist)
- `/api/v1/collection/flows/{flow_id}/questionnaires/{questionnaire_id}/responses` - Submit responses
- `/api/v1/collection/status` - Check active flow status

## Asset Inventory vs Discovery
### For Collection Flows:
- Use: `/api/v1/asset-inventory/list/paginated`
- Supports: Pagination without Flow ID requirement
- Returns: All asset types (filter client-side)

### For Discovery Flows:
- Use: `/api/v1/unified-discovery/assets`
- Requires: X-Flow-ID header
- Returns: Discovery-specific asset data

## Critical Headers
- Discovery endpoints require `X-Flow-ID` header
- Collection endpoints use flow_id in URL path
- Asset inventory works without flow context

## Response Structure Patterns
### Asset Inventory Response:
```json
{
  "assets": [...],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 100,
    "pages": 5
  }
}
```

### Collection Questionnaire Response:
```json
{
  "id": "bootstrap_<flow_id>",
  "collection_flow_id": "<flow_id>",
  "questions": [...],
  "completion_status": "pending"
}
```
