# Discovery Flow API v3

## Overview
The v3 API consolidates all discovery flow operations into a unified, RESTful interface. This API provides comprehensive flow management, data import, field mapping, and asset discovery capabilities with multi-tenant support and real-time status updates.

## Base URL
```
https://api.platform.com/api/v3
```

## Authentication
All requests require Bearer token authentication and proper tenant context:
```
Authorization: Bearer <token>
X-Client-Account-ID: <client_account_id>
X-Engagement-ID: <engagement_id>
```

## Core Concepts

### Flow Lifecycle
1. **Create** - Initialize a new discovery flow
2. **Import** - Upload and validate data
3. **Map** - Define field mappings with AI assistance
4. **Execute** - Run discovery phases (inventory, dependencies, tech debt)
5. **Review** - Examine results and approve assets
6. **Promote** - Move approved assets to production tables

### Execution Modes
- **CrewAI**: AI-powered analysis with 17 specialized agents
- **Database**: Fast SQL-based processing for large datasets
- **Hybrid**: Combines AI intelligence with database performance

## API Endpoints

### Discovery Flow Management

#### Create Flow
Creates a new discovery flow with optional data import.

**Endpoint:** `POST /api/v3/discovery-flow/flows`

**Request:**
```json
{
  "name": "Q4 2024 Migration Assessment",
  "description": "Quarterly migration planning discovery",
  "execution_mode": "hybrid",
  "metadata": {
    "source": "manual",
    "tags": ["quarterly", "assessment"],
    "priority": "high"
  },
  "initial_data": [
    {
      "server_name": "web-server-01",
      "ip_address": "10.0.1.100",
      "os": "Ubuntu 20.04",
      "cpu_cores": 4,
      "memory_gb": 16
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Q4 2024 Migration Assessment",
    "status": "initializing",
    "execution_mode": "hybrid",
    "current_phase": null,
    "progress_percentage": 0,
    "created_at": "2024-01-20T10:00:00Z",
    "updated_at": "2024-01-20T10:00:00Z",
    "phases_completed": [],
    "data_import_id": "660e8400-e29b-41d4-a716-446655440001",
    "metadata": {
      "source": "manual",
      "tags": ["quarterly", "assessment"],
      "priority": "high"
    }
  }
}
```

#### Get Flow Status
Retrieves real-time flow status with detailed progress information.

**Endpoint:** `GET /api/v3/discovery-flow/flows/{flow_id}/status`

**Response:**
```json
{
  "success": true,
  "data": {
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "current_phase": "asset_inventory",
    "progress_percentage": 45.5,
    "execution_mode": "hybrid",
    "phases_completed": ["data_import", "field_mapping", "data_cleansing"],
    "active_crews": [
      {
        "crew_name": "asset_inventory_crew",
        "status": "running",
        "progress": 67.5,
        "agent_count": 3,
        "records_processing": 1250
      }
    ],
    "statistics": {
      "records_total": 2500,
      "records_processed": 1138,
      "records_valid": 1095,
      "records_failed": 43,
      "assets_discovered": 847,
      "dependencies_mapped": 312
    },
    "estimated_completion": "2024-01-20T11:45:00Z",
    "last_updated": "2024-01-20T10:15:30Z"
  }
}
```

#### Execute Flow Phase
Executes a specific discovery phase with configurable parameters.

**Endpoint:** `POST /api/v3/discovery-flow/flows/{flow_id}/execute/{phase}`

**Parameters:**
- `phase`: One of `data_import`, `field_mapping`, `data_cleansing`, `asset_inventory`, `dependency_analysis`, `tech_debt_analysis`

**Request:**
```json
{
  "execution_mode": "hybrid",
  "parallel_processing": true,
  "batch_size": 500,
  "ai_confidence_threshold": 0.85,
  "parameters": {
    "discovery_depth": "comprehensive",
    "include_network_scanning": true,
    "analyze_dependencies": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "phase": "asset_inventory",
    "execution_id": "770e8400-e29b-41d4-a716-446655440002",
    "status": "initiated",
    "estimated_duration": "PT15M",
    "crew_assignments": [
      {
        "crew_name": "asset_discovery_crew",
        "agents": ["Asset Intelligence Agent", "CMDB Data Analyst"],
        "records_assigned": 1250
      }
    ]
  }
}
```

#### List Flows
Retrieves paginated list of flows with filtering and sorting.

**Endpoint:** `GET /api/v3/discovery-flow/flows`

**Query Parameters:**
- `status`: Filter by flow status (`running`, `completed`, `failed`, `paused`)
- `execution_mode`: Filter by execution mode (`crewai`, `database`, `hybrid`)
- `created_after`: ISO datetime for date filtering
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `sort`: Sort field (`created_at`, `updated_at`, `name`)
- `order`: Sort order (`asc`, `desc`)

**Response:**
```json
{
  "success": true,
  "data": {
    "flows": [
      {
        "flow_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Q4 2024 Migration Assessment",
        "status": "completed",
        "execution_mode": "hybrid",
        "progress_percentage": 100,
        "created_at": "2024-01-20T10:00:00Z",
        "completed_at": "2024-01-20T11:42:15Z",
        "assets_discovered": 847,
        "dependencies_mapped": 312
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 47,
      "items_per_page": 20,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

### Data Import Management

#### Create Data Import
Creates a new data import for a discovery flow.

**Endpoint:** `POST /api/v3/data-import/imports`

**Request:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_type": "csv",
  "filename": "server_inventory.csv",
  "data": [
    {
      "Server Name": "web-server-01",
      "IP Address": "10.0.1.100",
      "Operating System": "Ubuntu 20.04",
      "CPU Cores": "4",
      "Memory (GB)": "16"
    }
  ],
  "auto_detect_fields": true,
  "validation_rules": {
    "required_fields": ["Server Name", "IP Address"],
    "ip_validation": true,
    "duplicate_detection": true
  }
}
```

#### Upload Data File
Uploads a data file (CSV, Excel, JSON) for import.

**Endpoint:** `POST /api/v3/data-import/imports/upload`

**Request:** Multipart form data
- `file`: Data file (CSV, XLSX, JSON)
- `flow_id`: Target flow ID
- `auto_detect_fields`: Boolean for automatic field detection
- `sheet_name`: For Excel files (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "import_id": "660e8400-e29b-41d4-a716-446655440001",
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "server_inventory.csv",
    "records_detected": 2500,
    "fields_detected": [
      {
        "name": "Server Name",
        "type": "string",
        "sample_values": ["web-server-01", "app-server-02", "db-server-01"],
        "null_count": 0,
        "confidence": 0.98
      },
      {
        "name": "IP Address",
        "type": "ip_address",
        "sample_values": ["10.0.1.100", "10.0.1.101", "10.0.2.50"],
        "null_count": 0,
        "confidence": 0.95
      }
    ],
    "validation_summary": {
      "total_records": 2500,
      "valid_records": 2456,
      "invalid_records": 44,
      "warnings": 12,
      "errors": [
        {
          "row": 127,
          "field": "IP Address",
          "value": "invalid-ip",
          "error": "Invalid IP address format"
        }
      ]
    }
  }
}
```

### Field Mapping Management

#### Create Field Mappings
Creates field mappings with AI-powered suggestions.

**Endpoint:** `POST /api/v3/field-mapping/mappings`

**Request:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_schema": "standard_asset_schema",
  "auto_map": true,
  "confidence_threshold": 0.75,
  "custom_mappings": [
    {
      "source_field": "Server Name",
      "target_field": "asset_name",
      "transformation": "trim_whitespace",
      "required": true
    },
    {
      "source_field": "IP Address",
      "target_field": "primary_ip",
      "transformation": "validate_ip",
      "required": true
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "mapping_id": "880e8400-e29b-41d4-a716-446655440003",
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_schema": "standard_asset_schema",
    "mappings": [
      {
        "id": "map_001",
        "source_field": "Server Name",
        "target_field": "asset_name",
        "confidence": 0.98,
        "transformation": "trim_whitespace",
        "status": "approved",
        "validation_rules": ["required", "unique"]
      },
      {
        "id": "map_002",
        "source_field": "Memory (GB)",
        "target_field": "memory_gb",
        "confidence": 0.85,
        "transformation": "parse_numeric",
        "status": "suggested",
        "validation_rules": ["numeric", "positive"]
      }
    ],
    "statistics": {
      "total_mappings": 12,
      "approved_mappings": 8,
      "suggested_mappings": 4,
      "average_confidence": 0.89
    }
  }
}
```

#### Get Mapping Suggestions
Gets AI-powered field mapping suggestions.

**Endpoint:** `GET /api/v3/field-mapping/suggestions/{flow_id}`

**Query Parameters:**
- `target_schema`: Target schema name
- `min_confidence`: Minimum confidence threshold (0.0-1.0)

**Response:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "source_field": "OS Version",
        "suggested_mappings": [
          {
            "target_field": "operating_system",
            "confidence": 0.92,
            "reasoning": "Field name and sample values match OS pattern",
            "transformation": "standardize_os_name"
          },
          {
            "target_field": "software_version",
            "confidence": 0.45,
            "reasoning": "Contains version information",
            "transformation": "extract_version"
          }
        ]
      }
    ],
    "schema_info": {
      "name": "standard_asset_schema",
      "version": "2.1.0",
      "required_fields": ["asset_name", "asset_type", "primary_ip"],
      "optional_fields": ["operating_system", "memory_gb", "cpu_cores"]
    }
  }
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field mapping validation failed",
    "details": {
      "field": "primary_ip",
      "reason": "Invalid IP address format",
      "received_value": "not-an-ip"
    },
    "timestamp": "2024-01-20T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Request validation failed
- `FLOW_NOT_FOUND`: Specified flow doesn't exist
- `UNAUTHORIZED`: Authentication failed or insufficient permissions
- `CONCURRENT_MODIFICATION`: Resource modified by another request
- `EXECUTION_FAILED`: Flow execution encountered an error
- `QUOTA_EXCEEDED`: Rate limit or quota exceeded
- `INTERNAL_ERROR`: Unexpected server error

## Rate Limits
- **Standard requests**: 1000 requests per hour
- **File uploads**: 50 uploads per hour (max 100MB per file)
- **Flow executions**: 20 concurrent flows per tenant
- **WebSocket connections**: 10 concurrent connections per user

## WebSocket Real-time Updates

### Flow Status Updates
Connect to WebSocket endpoint for real-time flow progress:

**Endpoint:** `wss://api.platform.com/api/v3/ws/flows/{flow_id}/status`

**Message Format:**
```json
{
  "type": "flow_status_update",
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "current_phase": "asset_inventory",
  "progress_percentage": 67.5,
  "records_processed": 1688,
  "timestamp": "2024-01-20T10:45:15Z"
}
```

## Migration from v1/v2

### URL Mapping
| v1/v2 Endpoint | v3 Endpoint | Notes |
|----------------|-------------|-------|
| `/api/v1/unified-discovery/flow/initialize` | `/api/v3/discovery-flow/flows` | POST method |
| `/api/v1/discovery/session/{id}/status` | `/api/v3/discovery-flow/flows/{id}/status` | Flow ID instead of session ID |
| `/api/v2/discovery-flows/flows/active` | `/api/v3/discovery-flow/flows?status=running` | Query parameter filtering |

### Key Changes
- **Flow ID Primary**: All operations use `flow_id` instead of `session_id`
- **Standardized Responses**: Consistent success/error response format
- **Enhanced Context**: Multi-tenant context required in headers
- **Real-time Updates**: WebSocket support for live progress tracking
- **Execution Modes**: Support for CrewAI, Database, and Hybrid modes

## OpenAPI Specification

The complete OpenAPI specification is available at:
- **Interactive Docs**: `https://api.platform.com/docs`
- **ReDoc**: `https://api.platform.com/redoc`
- **Raw Spec**: `https://api.platform.com/api/v3/openapi-spec`

## Health and Monitoring

### Health Check
**Endpoint:** `GET /api/v3/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00Z",
  "services": {
    "database": "healthy",
    "crewai": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  },
  "metrics": {
    "active_flows": 15,
    "total_flows_today": 47,
    "average_response_time": "125ms",
    "success_rate": "99.2%"
  }
}
```

### Performance Metrics
**Endpoint:** `GET /api/v3/metrics`

Returns detailed performance metrics for monitoring and observability.