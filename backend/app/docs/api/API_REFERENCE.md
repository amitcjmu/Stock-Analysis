# AI Force Migration Platform - API Reference

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Data Import API](#data-import-api)
4. [Discovery Flow API](#discovery-flow-api)
5. [Master Flow API](#master-flow-api)
6. [Field Mapping API](#field-mapping-api)
7. [WebSocket Events](#websocket-events)
8. [Error Reference](#error-reference)

## Overview

The AI Force Migration Platform API provides comprehensive endpoints for managing cloud migration discovery, assessment, planning, and execution flows.

### Base URL
```
Production: https://api.aiforce.com
Staging: https://staging-api.aiforce.com
Development: http://localhost:8000
```

### API Versioning
All API endpoints are versioned. Current version: `v1`

```
https://api.aiforce.com/api/v1/...
```

### Request Format
- All requests must include `Content-Type: application/json`
- Request bodies must be valid JSON
- All timestamps use ISO 8601 format

### Response Format
All responses follow a consistent structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "metadata": {
    "request_id": "req_123",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

## Authentication

### Bearer Token Authentication

All API requests require Bearer token authentication:

```http
Authorization: Bearer <your-token>
```

### Multi-Tenant Headers

All requests must include tenant identification headers:

```http
X-Client-Account-ID: <client-id>
X-Engagement-ID: <engagement-id>
```

### Example Authenticated Request

```bash
curl -X GET https://api.aiforce.com/api/v1/health \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "X-Client-Account-ID: 1" \
  -H "X-Engagement-ID: 1"
```

## Data Import API

### Store Import Data

Store CSV data and trigger discovery flow processing.

**Endpoint:** `POST /api/v1/data-import/store-import`

**Request Body:**
```json
{
  "file_data": [
    {
      "server_name": "prod-web-01",
      "ip_address": "10.0.1.10",
      "os": "Ubuntu 20.04",
      "cpu_cores": 8,
      "memory_gb": 16
    }
  ],
  "metadata": {
    "filename": "servers.csv",
    "size": 102400,
    "type": "text/csv"
  },
  "upload_context": {
    "intended_type": "servers",
    "upload_timestamp": "2025-01-15T10:30:00Z"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Data imported successfully",
  "data_import_id": "imp_789e0123",
  "flow_id": "disc_flow_456e7890",
  "total_records": 1,
  "import_type": "servers",
  "next_steps": [
    "Monitor discovery flow progress",
    "Review field mappings"
  ]
}
```

### Get Latest Import

Retrieve the most recent import for the current context.

**Endpoint:** `GET /api/v1/data-import/latest-import`

**Response (200 OK):**
```json
{
  "success": true,
  "data": [...],
  "import_metadata": {
    "import_id": "imp_789e0123",
    "filename": "servers.csv",
    "import_type": "servers",
    "imported_at": "2025-01-15T10:30:00Z",
    "total_records": 150,
    "status": "completed"
  }
}
```

### Get Import Status

Check the status of an import operation.

**Endpoint:** `GET /api/v1/data-import/import/{import_id}/status`

**Response (200 OK):**
```json
{
  "success": true,
  "import_status": {
    "import_id": "imp_789e0123",
    "status": "processing",
    "progress": 75,
    "current_phase": "field_mapping",
    "updated_at": "2025-01-15T10:35:00Z"
  }
}
```

## Discovery Flow API

### Initialize Discovery Flow

Start a new discovery flow (handled automatically by data import).

**Endpoint:** `POST /api/v1/unified-discovery/flow/initialize`

**Request Body:**
```json
{
  "flow_name": "Q1 2025 Server Discovery",
  "description": "Discovering server infrastructure",
  "data_import_id": "imp_789e0123"
}
```

### Get Flow Status

Get the current status of a discovery flow.

**Endpoint:** `GET /api/v1/unified-discovery/flow/status/{flow_id}`

**Response (200 OK):**
```json
{
  "success": true,
  "flow": {
    "flow_id": "disc_flow_456e7890",
    "status": "processing",
    "current_phase": "field_mapping",
    "progress": 45,
    "phases_completed": ["data_import", "validation"],
    "phases_pending": ["field_mapping", "critical_attributes", "completion"]
  }
}
```

### Get Active Flows

List all active discovery flows for the current context.

**Endpoint:** `GET /api/v1/discovery/flows/active`

**Response (200 OK):**
```json
{
  "success": true,
  "flows": [
    {
      "flow_id": "disc_flow_456e7890",
      "flow_name": "Q1 2025 Server Discovery",
      "status": "processing",
      "created_at": "2025-01-15T10:00:00Z",
      "progress": 45
    }
  ],
  "total": 1
}
```

## Master Flow API

### Get All Active Flows

Get all active flows across all types (discovery, assessment, etc.).

**Endpoint:** `GET /api/v1/master-flows/active`

**Response (200 OK):**
```json
{
  "success": true,
  "flows": [
    {
      "flow_id": "master_123",
      "flow_type": "discovery",
      "child_flow_id": "disc_flow_456",
      "status": "active",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### Delete Flow

Delete any flow via master orchestration (cascades to child flows).

**Endpoint:** `DELETE /api/v1/master-flows/{flow_id}`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Flow deleted successfully",
  "deleted_flows": {
    "master": "master_123",
    "children": ["disc_flow_456"]
  }
}
```

## Field Mapping API

### Get Field Mappings

Get field mapping suggestions for imported data.

**Endpoint:** `GET /api/v1/data-import/field-mapping/{import_id}`

**Response (200 OK):**
```json
{
  "success": true,
  "mappings": [
    {
      "source_field": "server_name",
      "target_field": "asset_name",
      "confidence": 0.95,
      "data_type": "string",
      "sample_values": ["prod-web-01", "prod-db-01"]
    }
  ]
}
```

### Approve Field Mappings

Approve or modify field mapping suggestions.

**Endpoint:** `POST /api/v1/data-import/field-mapping/{import_id}/approve`

**Request Body:**
```json
{
  "approved_mappings": [
    {
      "source_field": "server_name",
      "target_field": "asset_name",
      "transformation": "uppercase"
    }
  ]
}
```

## WebSocket Events

### Connection

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket('wss://api.aiforce.com/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'Bearer YOUR_TOKEN',
    client_id: '1',
    engagement_id: '1'
  }));
};
```

### Event Types

| Event | Description | Payload |
|-------|-------------|---------|
| `flow.started` | Flow initiated | `{flow_id, flow_type}` |
| `flow.progress` | Progress update | `{flow_id, progress, phase}` |
| `flow.completed` | Flow finished | `{flow_id, results}` |
| `flow.error` | Error occurred | `{flow_id, error}` |
| `import.progress` | Import progress | `{import_id, progress}` |

## Error Reference

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error context"
  },
  "request_id": "req_123"
}
```

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `auth_token_invalid` | Invalid or expired token | Refresh authentication |
| `auth_token_missing` | No token provided | Include Bearer token |
| `tenant_headers_missing` | Missing tenant headers | Include X-Client-Account-ID and X-Engagement-ID |
| `validation_error` | Request validation failed | Check request format |
| `incomplete_discovery_flow_exists` | Active flow exists | Complete or cancel existing flow |
| `rate_limit_exceeded` | Too many requests | Implement backoff strategy |
| `import_not_found` | Import ID not found | Verify import ID |
| `flow_not_found` | Flow ID not found | Verify flow ID |

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Data Import | 100 requests | Per minute |
| Flow Status | 300 requests | Per minute |
| General API | 1000 requests | Per minute |

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1673870400
```

## Pagination

List endpoints support pagination:

```
GET /api/v1/resource?page=1&limit=20
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

## Filtering and Sorting

### Filtering
```
GET /api/v1/resource?status=active&type=servers
```

### Sorting
```
GET /api/v1/resource?sort=created_at&order=desc
```

## SDK Examples

### Python SDK
```python
from aiforce import Client

client = Client(
    api_key="YOUR_API_KEY",
    client_id="1",
    engagement_id="1"
)

# Import data
result = client.data_import.store(
    file_path="servers.csv",
    import_type="servers"
)
```

### JavaScript SDK
```javascript
import { AIForceClient } from '@aiforce/sdk';

const client = new AIForceClient({
    apiKey: 'YOUR_API_KEY',
    clientId: '1',
    engagementId: '1'
});

// Import data
const result = await client.dataImport.store({
    filePath: 'servers.csv',
    importType: 'servers'
});
```

## Support

- **Documentation**: https://docs.aiforce.com
- **API Status**: https://status.aiforce.com
- **Support Email**: api-support@aiforce.com
- **Community Forum**: https://community.aiforce.com