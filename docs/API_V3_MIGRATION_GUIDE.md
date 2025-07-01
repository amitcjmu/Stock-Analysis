# API V3 Migration Guide

## Overview

This guide documents the migration from the V1/V2 API to the consolidated V3 API as part of the database consolidation effort. The V3 API provides a cleaner, more consistent interface with proper field naming conventions and improved error handling.

## Table of Contents

1. [Key Changes](#key-changes)
2. [Field Name Mappings](#field-name-mappings)
3. [API Endpoint Changes](#api-endpoint-changes)
4. [Error Handling](#error-handling)
5. [Migration Steps](#migration-steps)
6. [Backward Compatibility](#backward-compatibility)
7. [Code Examples](#code-examples)

## Key Changes

### 1. Database Schema Consolidation
- Removed `v3_` prefixed tables
- Consolidated duplicate table structures
- Eliminated redundant fields
- Standardized field naming conventions

### 2. Improved API Structure
- Consistent RESTful patterns
- Standardized error responses
- Better multi-tenant isolation
- Enhanced field validation

### 3. Field Name Standardization
- Renamed fields for clarity and consistency
- Removed deprecated fields
- Added proper unit conversions

## Field Name Mappings

### Data Import Fields

| Old Field Name | New Field Name | Notes |
|----------------|----------------|-------|
| `source_filename` | `filename` | Simplified naming |
| `file_size_bytes` | `file_size` | Still in bytes, clearer name |
| `file_type` | `mime_type` | More accurate description |
| `is_mock` | *removed* | Deprecated field |

### Asset Fields

| Old Field Name | New Field Name | Notes |
|----------------|----------------|-------|
| `name` | `asset_name` | More descriptive |
| `type` | `asset_type` | Avoids reserved keywords |
| `cpu_count` | `cpu_cores` | Industry standard terminology |
| `memory_mb` | `memory_gb` | **Unit conversion: MB → GB** |
| `storage_mb` | `storage_gb` | **Unit conversion: MB → GB** |

### Discovery Flow Fields

| Old Field Name | New Field Name | Notes |
|----------------|----------------|-------|
| `flow_status` | `status` | Simplified |
| `phase` | `current_phase` | More descriptive |
| `user_id` | `created_by_user_id` | Clarifies purpose |

## API Endpoint Changes

### Base URL
```
Old: https://api.example.com/api/v1
New: https://api.example.com/api/v3
```

### Discovery Flow Endpoints

| Operation | Old Endpoint | New Endpoint |
|-----------|-------------|--------------|
| Create Flow | `POST /api/v1/unified-discovery/flow/initialize` | `POST /api/v3/discovery-flow/flows` |
| Get Flow Status | `GET /api/v1/unified-discovery/flow/status/{session_id}` | `GET /api/v3/discovery-flow/flows/{flow_id}/status` |
| List Flows | `GET /api/v1/discovery-flows` | `GET /api/v3/discovery-flow/flows` |
| Delete Flow | `DELETE /api/v1/discovery-flows/{session_id}` | `DELETE /api/v3/discovery-flow/flows/{flow_id}` |

### Data Import Endpoints

| Operation | Old Endpoint | New Endpoint |
|-----------|-------------|--------------|
| Create Import | `POST /api/v1/data-import/store-import` | `POST /api/v3/data-import/imports` |
| Upload File | `POST /api/v1/data-import/upload` | `POST /api/v3/data-import/imports/upload` |
| Get Import | `GET /api/v1/data-import/import/{import_id}` | `GET /api/v3/data-import/imports/{import_id}` |
| Validate Import | N/A | `POST /api/v3/data-import/imports/{import_id}/validate` |

### Field Mapping Endpoints

| Operation | Old Endpoint | New Endpoint |
|-----------|-------------|--------------|
| Create Mapping | `POST /api/v1/field-mappings` | `POST /api/v3/field-mapping/mappings` |
| Get Mapping | `GET /api/v1/field-mappings/{flow_id}` | `GET /api/v3/field-mapping/mappings/{flow_id}` |
| Update Mapping | `PUT /api/v1/field-mappings/{flow_id}` | `PUT /api/v3/field-mapping/mappings/{flow_id}` |

## Error Handling

### V3 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Request validation failed",
    "details": {
      "validation_errors": [
        {
          "field": "asset_name",
          "message": "Field is required",
          "type": "required"
        }
      ]
    },
    "request_id": "abc123",
    "timestamp": "2025-01-01T12:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request format or parameters |
| `VALIDATION_FAILED` | 422 | Request validation failed |
| `RESOURCE_NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Database constraint violation |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable |

## Migration Steps

### 1. Update API Base URL

```typescript
// Old
const API_BASE = 'https://api.example.com/api/v1';

// New
const API_BASE = 'https://api.example.com/api/v3';
```

### 2. Update Field Names in Requests

```typescript
// Old request
const oldRequest = {
  source_filename: 'data.csv',
  file_size_bytes: 1024000,
  file_type: 'text/csv'
};

// New request
const newRequest = {
  filename: 'data.csv',
  file_size: 1024000,
  mime_type: 'text/csv'
};
```

### 3. Handle Unit Conversions

```typescript
// Old: Memory in MB
const oldAsset = {
  name: 'server-01',
  memory_mb: 16384,
  storage_mb: 512000
};

// New: Memory in GB
const newAsset = {
  asset_name: 'server-01',
  memory_gb: 16,    // 16384 MB → 16 GB
  storage_gb: 500   // 512000 MB → 500 GB
};
```

### 4. Update Response Handling

```typescript
// Handle backward compatibility
function processResponse(response: any) {
  // V3 responses include legacy fields during transition
  const assetName = response.asset_name || response.name;
  const memoryGB = response.memory_gb || (response.memory_mb / 1024);
  
  return {
    assetName,
    memoryGB
  };
}
```

## Backward Compatibility

### Transition Period Support

During the migration period, the V3 API provides backward compatibility:

1. **Request Compatibility**: Old field names in requests are automatically mapped to new names
2. **Response Compatibility**: Responses include both old and new field names
3. **Field Mapping Endpoint**: `GET /api/v3/data-import/field-mappings` provides current mappings

### Example Compatible Response

```json
{
  "import_id": "123",
  "name": "My Import",
  "metadata": {
    "filename": "data.csv",
    "file_size": 1024000,
    "mime_type": "text/csv",
    
    // Legacy fields included for compatibility
    "source_filename": "data.csv",
    "file_size_bytes": 1024000,
    "file_type": "text/csv"
  }
}
```

## Code Examples

### TypeScript/React

```typescript
import { createApiV3Client } from '@/api/v3';

// Initialize V3 client
const apiClient = createApiV3Client({
  baseURL: process.env.REACT_APP_API_URL + '/api/v3',
  timeout: 30000
});

// Create a discovery flow
async function createFlow(data: any[]) {
  try {
    const response = await apiClient.discoveryFlow.createFlow({
      name: 'My Discovery Flow',
      description: 'Imported from CSV',
      raw_data: data,
      metadata: {
        source: 'manual_upload'
      }
    });
    
    console.log('Flow created:', response.flow_id);
    return response;
  } catch (error) {
    if (isValidationApiError(error)) {
      console.error('Validation errors:', error.details.validation_errors);
    }
    throw error;
  }
}

// Upload and import data
async function importData(file: File) {
  try {
    const response = await apiClient.dataImport.uploadFile(
      file,
      {
        name: file.name,
        auto_create_flow: true
      },
      {
        onProgress: (progress) => {
          console.log(`Upload progress: ${progress.percentage}%`);
        }
      }
    );
    
    return response;
  } catch (error) {
    console.error('Import failed:', error);
    throw error;
  }
}
```

### Python

```python
import requests
from typing import Dict, Any

class ApiV3Client:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_discovery_flow(self, name: str, data: list) -> Dict[str, Any]:
        """Create a new discovery flow"""
        response = requests.post(
            f'{self.base_url}/api/v3/discovery-flow/flows',
            json={
                'name': name,
                'raw_data': data,
                'execution_mode': 'hybrid'
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow status"""
        response = requests.get(
            f'{self.base_url}/api/v3/discovery-flow/flows/{flow_id}/status',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ApiV3Client('https://api.example.com', 'your-token')

# Create flow with new field names
flow = client.create_discovery_flow(
    name='Asset Import',
    data=[
        {
            'asset_name': 'server-01',  # New field name
            'asset_type': 'server',     # New field name
            'memory_gb': 16,            # New unit (GB instead of MB)
            'storage_gb': 500           # New unit (GB instead of MB)
        }
    ]
)
```

## Troubleshooting

### Common Issues

1. **404 Not Found Errors**
   - Ensure you're using the correct V3 endpoint paths
   - Check that IDs are properly formatted (UUIDs)

2. **Field Name Errors**
   - Update all field names according to the mapping table
   - Remove any references to deprecated fields

3. **Unit Conversion Issues**
   - Remember to convert MB to GB for memory and storage fields
   - The API expects GB values, not MB

4. **Authentication Errors**
   - V3 uses the same authentication as V1/V2
   - Ensure Bearer token is included in headers

### Debug Endpoints

- **Field Mappings**: `GET /api/v3/data-import/field-mappings`
- **API Health**: `GET /api/v3/discovery-flow/health`
- **Debug Context**: `GET /api/v3/data-import/debug/context`

## Support

For questions or issues during migration:

1. Check the [API documentation](/docs/api/v3)
2. Review error response details and request IDs
3. Contact the platform team with specific error details

## Timeline

- **Phase 1** (Current): V3 API available with backward compatibility
- **Phase 2** (Q2 2025): Deprecation warnings for V1/V2 endpoints
- **Phase 3** (Q3 2025): V1/V2 endpoints removed

---

Last Updated: January 2025