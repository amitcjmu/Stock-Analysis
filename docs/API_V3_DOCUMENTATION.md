# API V3 Documentation

## Overview

The V3 API provides a consolidated, RESTful interface for the AI Force Migration Platform. It features improved consistency, better error handling, and full backward compatibility during the migration period.

## Authentication

All API requests require authentication using a Bearer token:

```http
Authorization: Bearer <your-token>
```

## Base URL

```
https://api.your-domain.com/api/v3
```

## Common Headers

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token for authentication |
| `Content-Type` | Yes | `application/json` for JSON payloads |
| `X-Client-Account-ID` | Yes | Client account UUID |
| `X-Engagement-ID` | Yes | Engagement UUID |
| `X-User-ID` | No | User UUID (defaults to auth token user) |
| `X-Request-ID` | No | Client-generated request ID for tracking |

### Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Request tracking ID |
| `X-Rate-Limit-Remaining` | Remaining API calls in window |
| `X-Rate-Limit-Reset` | Unix timestamp for rate limit reset |

## Standard Response Format

### Success Response

```json
{
  "data": {
    // Response data
  },
  "meta": {
    "request_id": "abc123",
    "timestamp": "2025-01-01T12:00:00Z"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error context
    },
    "request_id": "abc123",
    "timestamp": "2025-01-01T12:00:00Z"
  }
}
```

## API Endpoints

### Discovery Flow API

#### Create Discovery Flow

Creates a new discovery flow for asset migration analysis.

```http
POST /api/v3/discovery-flow/flows
```

**Request Body:**
```json
{
  "name": "Q1 2025 Migration",
  "description": "Server migration for data center consolidation",
  "raw_data": [
    {
      "asset_name": "server-01",
      "asset_type": "server",
      "ip_address": "10.0.1.100",
      "operating_system": "Ubuntu 20.04",
      "cpu_cores": 8,
      "memory_gb": 32,
      "storage_gb": 500
    }
  ],
  "metadata": {
    "source": "manual_upload",
    "department": "IT Infrastructure"
  },
  "execution_mode": "hybrid"
}
```

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Q1 2025 Migration",
  "status": "initializing",
  "current_phase": "initialization",
  "progress_percentage": 0,
  "created_at": "2025-01-01T12:00:00Z",
  "records_total": 1
}
```

#### Get Flow Status

Retrieves the current status and progress of a discovery flow.

```http
GET /api/v3/discovery-flow/flows/{flow_id}/status
```

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "current_phase": "field_mapping",
  "progress_percentage": 35.5,
  "phases_completed": ["initialization", "data_validation"],
  "phases_status": {
    "initialization": "completed",
    "data_validation": "completed",
    "field_mapping": "in_progress",
    "data_cleansing": "pending",
    "inventory_building": "pending",
    "dependency_analysis": "pending",
    "tech_debt_analysis": "pending"
  },
  "execution_mode": "hybrid",
  "is_running": true,
  "can_pause": true,
  "can_resume": false,
  "updated_at": "2025-01-01T12:15:00Z"
}
```

#### List Discovery Flows

Lists all discovery flows with filtering and pagination.

```http
GET /api/v3/discovery-flow/flows?status=active&page=1&page_size=20
```

**Query Parameters:**
- `status_filter` - Filter by status (active, completed, failed, paused)
- `current_phase` - Filter by current phase
- `execution_mode` - Filter by execution mode (crewai, database, hybrid)
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)
- `sort_by` - Sort field (default: created_at)
- `sort_order` - Sort order (asc, desc)

**Response:**
```json
{
  "flows": [
    {
      "flow_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Q1 2025 Migration",
      "status": "active",
      "current_phase": "field_mapping",
      "progress_percentage": 35.5,
      "created_at": "2025-01-01T12:00:00Z",
      "records_total": 150
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

### Data Import API

#### Create Data Import

Creates a new data import from structured data.

```http
POST /api/v3/data-import/imports
```

**Request Body:**
```json
{
  "name": "Server Inventory Import",
  "description": "Q1 2025 server inventory",
  "source_type": "csv",
  "data": [
    {
      "hostname": "server-01",
      "ip": "10.0.1.100",
      "os": "Ubuntu 20.04",
      "cpu": 8,
      "memory": 32768,
      "storage": 512000
    }
  ],
  "metadata": {
    "department": "IT",
    "imported_by": "john.doe"
  },
  "auto_create_flow": true
}
```

**Response:**
```json
{
  "import_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Server Inventory Import",
  "status": "processing",
  "source_type": "csv",
  "total_records": 1,
  "valid_records": 1,
  "data_quality_score": 0.95,
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-01T12:00:00Z"
}
```

#### Upload File

Uploads a file for data import (CSV, Excel, JSON).

```http
POST /api/v3/data-import/imports/upload
Content-Type: multipart/form-data
```

**Form Data:**
- `file` - The file to upload
- `name` - Import name (optional)
- `description` - Import description (optional)
- `auto_create_flow` - Create discovery flow (default: true)

**Response:**
```json
{
  "import_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "servers.csv",
  "status": "processing",
  "source_type": "csv",
  "total_records": 150,
  "metadata": {
    "filename": "servers.csv",
    "file_size": 45678,
    "mime_type": "text/csv"
  },
  "flow_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Validate Import

Validates imported data against quality rules.

```http
POST /api/v3/data-import/imports/{import_id}/validate
```

**Request Body:**
```json
{
  "validation_rules": [
    {
      "field": "ip_address",
      "rule_type": "format",
      "parameters": {"pattern": "ipv4"},
      "severity": "error"
    },
    {
      "field": "memory_gb",
      "rule_type": "range",
      "parameters": {"min": 1, "max": 1024},
      "severity": "warning"
    }
  ]
}
```

**Response:**
```json
{
  "is_valid": true,
  "validation_score": 0.92,
  "total_records": 150,
  "valid_records": 145,
  "invalid_records": 5,
  "validation_errors": [
    {
      "type": "FORMAT_ERROR",
      "field": "ip_address",
      "message": "Invalid IP address format",
      "severity": "error",
      "affected_records": [23, 67]
    }
  ],
  "recommendations": [
    "Fix IP address format errors before proceeding",
    "Review memory values that exceed typical ranges"
  ]
}
```

### Field Mapping API

#### Create Field Mapping

Creates automatic field mappings for imported data.

```http
POST /api/v3/field-mapping/mappings
```

**Request Body:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_fields": ["hostname", "ip", "os", "cpu", "memory", "storage"],
  "target_schema": "asset_inventory",
  "auto_map": true,
  "mapping_rules": {
    "hostname": "asset_name",
    "ip": "ip_address"
  }
}
```

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "mapping_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "created",
  "mappings": {
    "hostname": "asset_name",
    "ip": "ip_address",
    "os": "operating_system",
    "cpu": "cpu_cores",
    "memory": "memory_gb",
    "storage": "storage_gb"
  },
  "confidence_scores": {
    "hostname": 0.95,
    "ip": 0.98,
    "os": 0.85,
    "cpu": 0.80,
    "memory": 0.80,
    "storage": 0.80
  },
  "unmapped_fields": [],
  "mapping_percentage": 100.0,
  "avg_confidence": 0.863
}
```

#### Get Mapping Suggestions

Gets AI-powered mapping suggestions for a field.

```http
GET /api/v3/field-mapping/suggestions/{flow_id}?source_field=hostname
```

**Response:**
```json
{
  "source_field": "hostname",
  "suggestions": [
    {
      "target": "asset_name",
      "confidence": 0.95,
      "reason": "Field name contains 'hostname'"
    },
    {
      "target": "server_name",
      "confidence": 0.70,
      "reason": "Alternative naming convention"
    }
  ],
  "auto_mapping_available": true
}
```

### Flow Control Endpoints

#### Pause Flow

Pauses a running discovery flow.

```http
POST /api/v3/discovery-flow/flows/{flow_id}/pause
```

**Request Body:**
```json
{
  "reason": "Manual review required"
}
```

#### Resume Flow

Resumes a paused discovery flow.

```http
POST /api/v3/discovery-flow/flows/{flow_id}/resume
```

**Request Body:**
```json
{
  "target_phase": "data_cleansing",
  "resume_context": {
    "skip_validation": false
  }
}
```

#### Delete Flow

Deletes a discovery flow and its resources.

```http
DELETE /api/v3/discovery-flow/flows/{flow_id}?force_delete=false
```

### Health Check

#### API Health

Checks the health of V3 API services.

```http
GET /api/v3/discovery-flow/health
```

**Response:**
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "components": {
    "v3_discovery_flow_service": true,
    "v3_data_import_service": true,
    "v3_field_mapping_service": true,
    "v3_asset_service": true,
    "database_connectivity": true
  }
}
```

## Rate Limiting

API requests are rate limited to ensure fair usage:

- **Default limit**: 1000 requests per hour
- **Burst limit**: 100 requests per minute
- **File uploads**: 10 per hour

Rate limit information is included in response headers:
```
X-Rate-Limit-Limit: 1000
X-Rate-Limit-Remaining: 950
X-Rate-Limit-Reset: 1640995200
```

## Pagination

List endpoints support pagination with these parameters:

- `page` - Page number (starts at 1)
- `page_size` - Items per page (max 100)

Paginated responses include:
```json
{
  "data": [...],
  "total": 500,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

## Field Compatibility

During the migration period, the API supports both old and new field names.

### Get Field Mappings

```http
GET /api/v3/data-import/field-mappings
```

**Response:**
```json
{
  "success": true,
  "data": {
    "field_mappings": {
      "filename": "source_filename",
      "file_size": "file_size_bytes",
      "mime_type": "file_type"
    },
    "unit_conversions": {
      "memory_mb -> memory_gb": "Divide by 1024",
      "storage_mb -> storage_gb": "Divide by 1024"
    },
    "deprecated_fields": ["is_mock", "legacy_field"]
  }
}
```

## WebSocket Support

Real-time updates are available via WebSocket for flow progress monitoring:

```javascript
const ws = new WebSocket('wss://api.your-domain.com/ws/v3/flows/{flow_id}');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Flow progress:', update.progress_percentage);
};
```

## SDK Support

Official SDKs are available for:

- **JavaScript/TypeScript**: `npm install @aiforce/api-v3-client`
- **Python**: `pip install aiforce-api-v3`
- **Go**: `go get github.com/aiforce/api-v3-go`

## Changelog

### Version 3.0.0 (January 2025)
- Initial V3 API release
- Database schema consolidation
- Field name standardization
- Backward compatibility layer
- Enhanced error handling
- Improved multi-tenant isolation

---

For additional support, contact the API team at api-support@aiforce.com