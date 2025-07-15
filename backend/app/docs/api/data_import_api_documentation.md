# Data Import API Documentation

## Overview

The Data Import API provides endpoints for uploading, storing, and managing CSV data imports for the AI Force Migration Platform. These endpoints handle the initial data ingestion phase of the discovery flow process.

## Base URL

```
https://api.yourdomain.com/api/v1/data-import
```

## Authentication

All endpoints require authentication using Bearer tokens and multi-tenant headers:

```http
Authorization: Bearer <your-token>
X-Client-Account-ID: <client-id>
X-Engagement-ID: <engagement-id>
```

## Endpoints

### 1. Store Import Data

Store validated CSV data and trigger a discovery flow.

**Endpoint:** `POST /store-import`

**Request Body:**
```json
{
  "file_data": [
    {
      "server_name": "prod-web-01",
      "ip_address": "10.0.1.10",
      "os": "Ubuntu 20.04",
      "cpu_cores": 8,
      "memory_gb": 16,
      "storage_gb": 500
    },
    {
      "server_name": "prod-db-01",
      "ip_address": "10.0.1.20",
      "os": "RHEL 8",
      "cpu_cores": 16,
      "memory_gb": 64,
      "storage_gb": 2000
    }
  ],
  "metadata": {
    "filename": "servers_inventory.csv",
    "size": 102400,
    "type": "text/csv"
  },
  "upload_context": {
    "intended_type": "servers",
    "upload_timestamp": "2025-01-15T10:30:00Z"
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Data imported successfully and discovery flow triggered",
  "data_import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
  "flow_id": "disc_flow_456e7890-1234-56ab-cdef-0123456789ab",
  "total_records": 2,
  "import_type": "servers",
  "next_steps": [
    "Monitor discovery flow progress",
    "Review field mappings when available",
    "Validate critical attributes"
  ]
}
```

**Error Response (409 - Conflict):**
```json
{
  "success": false,
  "error": "incomplete_discovery_flow_exists",
  "message": "An incomplete discovery flow already exists for this engagement",
  "details": {
    "existing_flow": {
      "flow_id": "disc_flow_123",
      "status": "processing",
      "created_at": "2025-01-15T09:00:00Z"
    }
  },
  "recommendations": [
    "Complete or cancel the existing discovery flow",
    "Review the current flow status"
  ]
}
```

**cURL Example:**
```bash
curl -X POST https://api.yourdomain.com/api/v1/data-import/store-import \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Client-Account-ID: 1" \
  -H "X-Engagement-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "file_data": [{
      "server_name": "prod-web-01",
      "ip_address": "10.0.1.10",
      "os": "Ubuntu 20.04"
    }],
    "metadata": {
      "filename": "servers.csv",
      "size": 1024,
      "type": "text/csv"
    },
    "upload_context": {
      "intended_type": "servers",
      "upload_timestamp": "2025-01-15T10:30:00Z"
    }
  }'
```

**Python Example:**
```python
import requests
import json

url = "https://api.yourdomain.com/api/v1/data-import/store-import"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "X-Client-Account-ID": "1",
    "X-Engagement-ID": "1",
    "Content-Type": "application/json"
}

data = {
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
        "size": 1024,
        "type": "text/csv"
    },
    "upload_context": {
        "intended_type": "servers",
        "upload_timestamp": "2025-01-15T10:30:00Z"
    }
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

**JavaScript/TypeScript Example:**
```typescript
const storeImportData = async () => {
  const response = await fetch('https://api.yourdomain.com/api/v1/data-import/store-import', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN',
      'X-Client-Account-ID': '1',
      'X-Engagement-ID': '1',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      file_data: [
        {
          server_name: 'prod-web-01',
          ip_address: '10.0.1.10',
          os: 'Ubuntu 20.04',
          cpu_cores: 8,
          memory_gb: 16
        }
      ],
      metadata: {
        filename: 'servers.csv',
        size: 1024,
        type: 'text/csv'
      },
      upload_context: {
        intended_type: 'servers',
        upload_timestamp: new Date().toISOString()
      }
    })
  });

  const data = await response.json();
  console.log(data);
};
```

### 2. Get Latest Import

Retrieve the most recent import for the current context.

**Endpoint:** `GET /latest-import`

**Success Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "server_name": "prod-web-01",
      "ip_address": "10.0.1.10",
      "os": "Ubuntu 20.04"
    }
  ],
  "import_metadata": {
    "import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
    "filename": "servers_inventory.csv",
    "import_type": "servers",
    "imported_at": "2025-01-15T10:30:00Z",
    "total_records": 150,
    "status": "completed",
    "flow_id": "disc_flow_456e7890-1234-56ab-cdef-0123456789ab",
    "client_account_id": 1,
    "engagement_id": 1
  }
}
```

### 3. Get Import by ID

Retrieve specific import data by import ID.

**Endpoint:** `GET /import/{import_id}`

**Parameters:**
- `import_id` (path parameter): The unique identifier of the import

**Example:** `GET /import/imp_789e0123-4567-89ab-cdef-0123456789ab`

### 4. Get Import Status

Check the current status of an import operation.

**Endpoint:** `GET /import/{import_id}/status`

**Success Response (200):**
```json
{
  "success": true,
  "import_status": {
    "import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
    "status": "processing",
    "progress": 75,
    "current_phase": "field_mapping",
    "updated_at": "2025-01-15T10:35:00Z"
  }
}
```

### 5. Cancel Import

Cancel an ongoing import operation.

**Endpoint:** `DELETE /import/{import_id}`

**Success Response (200):**
```json
{
  "success": true,
  "message": "Import imp_789e0123-4567-89ab-cdef-0123456789ab cancelled successfully"
}
```

### 6. Retry Failed Import

Retry a failed import operation.

**Endpoint:** `POST /import/{import_id}/retry`

**Success Response (200):**
```json
{
  "success": true,
  "message": "Import retry initiated",
  "new_flow_id": "disc_flow_987e6543-21ba-98dc-fedc-ba9876543210"
}
```

## Error Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | validation_error | Invalid request data or CSV format |
| 401 | unauthorized | Missing or invalid authentication token |
| 403 | forbidden | Insufficient permissions |
| 404 | not_found | Import or resource not found |
| 409 | incomplete_discovery_flow_exists | An incomplete flow already exists |
| 422 | unprocessable_entity | Missing required fields |
| 500 | internal_error | Server error |

## Common Error Scenarios

### 1. Incomplete Discovery Flow Exists

**Problem:** Attempting to import data when an incomplete discovery flow already exists.

**Solution:** 
- Complete the existing flow
- Cancel the existing flow using the master flow deletion endpoint
- Wait for the flow to timeout

### 2. Invalid CSV Format

**Problem:** The CSV data doesn't match expected format.

**Solution:**
- Ensure all required columns are present
- Check data types match expected values
- Validate no special characters in critical fields

### 3. Authentication Errors

**Problem:** Missing or invalid authentication headers.

**Solution:**
- Include valid Bearer token
- Include both X-Client-Account-ID and X-Engagement-ID headers
- Ensure token hasn't expired

## Data Types and Limits

### File Size Limits
- Maximum file size: 100MB
- Maximum records per import: 10,000

### Supported Import Types
- `servers`: Server infrastructure data
- `applications`: Application inventory
- `databases`: Database instances
- `storage`: Storage systems
- `network`: Network devices
- `security`: Security appliances

### Required Fields by Type

**Servers:**
- server_name (string)
- ip_address (string)
- os (string)

**Applications:**
- app_name (string)
- version (string)
- server_name (string)

## Rate Limits

- 100 requests per minute per client
- 10 concurrent imports per engagement

## Webhook Events

The following events are triggered during import operations:

- `import.started`: Import process initiated
- `import.validated`: Data validation completed
- `import.stored`: Data successfully stored
- `import.flow_triggered`: Discovery flow started
- `import.failed`: Import process failed
- `import.completed`: Import fully processed

## Best Practices

1. **Validate Data Before Upload**
   - Check CSV format locally
   - Ensure required fields are present
   - Remove duplicate records

2. **Handle Conflicts Gracefully**
   - Check for existing flows before importing
   - Implement retry logic with exponential backoff
   - Store import IDs for tracking

3. **Monitor Import Progress**
   - Poll status endpoint periodically
   - Subscribe to webhook events
   - Log all import operations

4. **Error Recovery**
   - Implement proper error handling
   - Store failed imports for retry
   - Alert on repeated failures

## Migration Guide

If migrating from older API versions:

1. Replace `session_id` with `flow_id` in all requests
2. Update to use multi-tenant headers
3. Switch from `/api/v3/*` to `/api/v1/*` endpoints
4. Update response parsing for new format