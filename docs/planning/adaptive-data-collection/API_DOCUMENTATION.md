# Collection Flow API Documentation

## Overview

The Collection Flow API provides comprehensive endpoints for managing adaptive data collection workflows. This RESTful API follows OpenAPI 3.0 specifications and integrates seamlessly with the Master Flow Orchestrator system.

## Base Configuration

### Base URL
```
Production: https://api.migration-orchestrator.com/api/v1/collection
Development: http://localhost:8000/api/v1/collection
```

### Authentication
All endpoints require Bearer token authentication:
```http
Authorization: Bearer <access_token>
```

### Content Type
```http
Content-Type: application/json
Accept: application/json
```

## API Structure

The Collection Flow API is organized into specialized endpoint groups:

- **Lifecycle Endpoints**: Flow creation, initialization, and deletion
- **Execution Endpoints**: Flow control, phase management, and monitoring
- **Query Endpoints**: Status retrieval, progress monitoring, and data access
- **Validation Endpoints**: Health checks, configuration validation
- **Data Collection Endpoints**: Automated and manual data operations
- **Integration Endpoints**: Platform adapter and external system operations

## Lifecycle Endpoints

### Create Collection Flow

Create a new Collection Flow instance for data collection.

```http
POST /collection/flows
```

**Request Body:**
```json
{
  "client_id": "uuid",
  "collection_type": "automated|manual|hybrid",
  "platform_type": "aws|azure|gcp|on_premises",
  "configuration": {
    "scope": {
      "regions": ["us-east-1", "us-west-2"],
      "resource_tags": ["Environment:Production"],
      "scan_depth": "comprehensive|standard|basic"
    },
    "automation_preferences": {
      "preferred_tier": 1,
      "fallback_strategy": "manual|skip|partial",
      "quality_threshold": 0.85
    },
    "collection_options": {
      "include_dependencies": true,
      "include_configuration": true,
      "include_performance_data": false,
      "parallel_execution": true
    }
  }
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "master_flow_id": "uuid",
  "client_id": "uuid",
  "collection_type": "automated",
  "automation_tier": 1,
  "platform_type": "aws",
  "status": "pending",
  "created_at": "2025-07-19T10:30:00Z",
  "estimated_duration": "2-4 hours",
  "capabilities": {
    "automated_discovery": true,
    "dependency_mapping": true,
    "configuration_analysis": true,
    "api_access": true
  }
}
```

### Initialize Collection Flow

Initialize an existing Collection Flow and begin environment assessment.

```http
POST /collection/flows/{flow_id}/initialize
```

**Path Parameters:**
- `flow_id` (string, required): Unique identifier for the Collection Flow

**Request Body:**
```json
{
  "credentials": {
    "aws": {
      "access_key_id": "string",
      "secret_access_key": "string",
      "session_token": "string",
      "region": "us-east-1"
    },
    "azure": {
      "subscription_id": "string",
      "client_id": "string",
      "client_secret": "string",
      "tenant_id": "string"
    }
  },
  "validation_options": {
    "test_connectivity": true,
    "validate_permissions": true,
    "estimate_scope": true
  }
}
```

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "status": "initialized",
  "automation_tier": 1,
  "environment_assessment": {
    "platforms_detected": ["aws", "azure"],
    "estimated_resources": 1500,
    "api_availability": {
      "aws": {
        "ec2": true,
        "rds": true,
        "lambda": true,
        "iam": false
      }
    },
    "estimated_completion": "2025-07-19T14:30:00Z"
  },
  "next_phase": "collection_execution"
}
```

### Delete Collection Flow

Delete a Collection Flow and all associated data.

```http
DELETE /collection/flows/{flow_id}
```

**Response (204 No Content)**

## Execution Endpoints

### Start Collection Execution

Begin the data collection process for an initialized flow.

```http
POST /collection/flows/{flow_id}/execute
```

**Request Body:**
```json
{
  "execution_options": {
    "parallel_collection": true,
    "max_concurrent_operations": 10,
    "timeout_settings": {
      "per_operation": 300,
      "total_execution": 7200
    },
    "retry_configuration": {
      "max_retries": 3,
      "backoff_strategy": "exponential"
    }
  },
  "quality_preferences": {
    "minimum_quality_score": 0.8,
    "require_validation": true,
    "auto_gap_resolution": true
  }
}
```

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "execution_id": "uuid",
  "status": "executing",
  "started_at": "2025-07-19T10:30:00Z",
  "estimated_completion": "2025-07-19T14:30:00Z",
  "current_phase": "platform_discovery",
  "progress": {
    "overall_percentage": 15,
    "phases": {
      "environment_assessment": "completed",
      "platform_discovery": "in_progress",
      "dependency_mapping": "pending",
      "quality_validation": "pending",
      "data_normalization": "pending"
    }
  }
}
```

### Pause Collection Flow

Pause an executing Collection Flow while preserving current state.

```http
POST /collection/flows/{flow_id}/pause
```

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "status": "paused",
  "paused_at": "2025-07-19T12:15:00Z",
  "pause_point": {
    "current_phase": "dependency_mapping",
    "completed_operations": 150,
    "pending_operations": 85
  },
  "resume_options": {
    "can_resume": true,
    "estimated_resume_duration": "1.5 hours"
  }
}
```

### Resume Collection Flow

Resume a paused Collection Flow from the last checkpoint.

```http
POST /collection/flows/{flow_id}/resume
```

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "status": "executing",
  "resumed_at": "2025-07-19T13:00:00Z",
  "resume_point": {
    "phase": "dependency_mapping",
    "operations_remaining": 85
  }
}
```

### Complete Collection Flow

Mark a Collection Flow as complete and prepare for handoff.

```http
POST /collection/flows/{flow_id}/complete
```

**Request Body:**
```json
{
  "completion_options": {
    "validate_data_quality": true,
    "generate_summary": true,
    "prepare_handoff": true
  },
  "quality_acceptance": {
    "accept_gaps": true,
    "minimum_completeness": 0.85,
    "stakeholder_approval": true
  }
}
```

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "status": "completed",
  "completed_at": "2025-07-19T14:30:00Z",
  "collection_summary": {
    "total_assets_discovered": 1247,
    "data_quality_score": 0.92,
    "completeness_percentage": 89,
    "confidence_level": "high",
    "gaps_identified": 23,
    "critical_gaps": 2
  },
  "handoff_data": {
    "discovery_flow_id": "uuid",
    "data_package_id": "uuid",
    "handoff_status": "ready"
  }
}
```

## Query Endpoints

### Get Collection Flow Status

Retrieve current status and progress information for a Collection Flow.

```http
GET /collection/flows/{flow_id}/status
```

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "status": "executing",
  "current_phase": "dependency_mapping",
  "overall_progress": {
    "percentage_complete": 65,
    "estimated_remaining": "1.2 hours",
    "current_operation": "Analyzing application dependencies"
  },
  "phase_progress": {
    "environment_assessment": {
      "status": "completed",
      "duration": "15 minutes",
      "quality_score": 0.95
    },
    "platform_discovery": {
      "status": "completed", 
      "duration": "2.5 hours",
      "resources_discovered": 1247,
      "quality_score": 0.91
    },
    "dependency_mapping": {
      "status": "in_progress",
      "progress_percentage": 75,
      "dependencies_mapped": 89,
      "estimated_remaining": "30 minutes"
    }
  },
  "real_time_metrics": {
    "operations_per_minute": 12,
    "success_rate": 0.94,
    "error_count": 7,
    "retry_count": 15
  }
}
```

### List Collection Flows

Retrieve a paginated list of Collection Flows for a client.

```http
GET /collection/flows?client_id={client_id}&status={status}&limit={limit}&offset={offset}
```

**Query Parameters:**
- `client_id` (string, optional): Filter by client ID
- `status` (string, optional): Filter by status (pending|executing|paused|completed|failed)
- `platform_type` (string, optional): Filter by platform type
- `limit` (integer, optional): Number of results per page (default: 20, max: 100)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Response (200 OK):**
```json
{
  "flows": [
    {
      "id": "uuid",
      "client_id": "uuid",
      "collection_type": "automated",
      "platform_type": "aws",
      "status": "completed",
      "created_at": "2025-07-19T10:30:00Z",
      "completed_at": "2025-07-19T14:30:00Z",
      "summary": {
        "assets_discovered": 1247,
        "quality_score": 0.92,
        "automation_tier": 1
      }
    }
  ],
  "pagination": {
    "total_count": 45,
    "limit": 20,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  }
}
```

### Get Collection Data

Retrieve collected data from a completed Collection Flow.

```http
GET /collection/flows/{flow_id}/data?category={category}&format={format}
```

**Query Parameters:**
- `category` (string, optional): Data category (applications|infrastructure|dependencies|all)
- `format` (string, optional): Response format (json|csv|excel)
- `include_metadata` (boolean, optional): Include collection metadata (default: false)

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "collection_metadata": {
    "collected_at": "2025-07-19T14:30:00Z",
    "collection_method": "automated",
    "quality_score": 0.92,
    "data_completeness": 89
  },
  "applications": [
    {
      "id": "uuid",
      "name": "CustomerPortal",
      "type": "web_application",
      "platform": "aws",
      "instance_details": {
        "instance_id": "i-1234567890abcdef0",
        "instance_type": "t3.large",
        "vpc_id": "vpc-12345678"
      },
      "dependencies": [
        {
          "target_application": "UserService",
          "connection_type": "api",
          "protocol": "https",
          "port": 443
        }
      ],
      "quality_metadata": {
        "confidence_level": "high",
        "data_sources": ["aws_api", "configuration_analysis"],
        "last_validated": "2025-07-19T14:15:00Z"
      }
    }
  ],
  "infrastructure": [],
  "dependencies": []
}
```

## Data Collection Endpoints

### Submit Manual Data

Submit manually collected data for a Collection Flow.

```http
POST /collection/flows/{flow_id}/manual-data
```

**Request Body:**
```json
{
  "data_category": "applications|infrastructure|dependencies",
  "submission_method": "form|bulk_upload|api",
  "data": {
    "applications": [
      {
        "name": "LegacyPaymentSystem",
        "type": "mainframe_application",
        "business_criticality": "high",
        "user_count": 1500,
        "technology_stack": {
          "language": "COBOL",
          "database": "DB2",
          "middleware": "CICS"
        },
        "operational_details": {
          "availability_requirement": "99.9%",
          "backup_frequency": "daily",
          "maintenance_window": "Sunday 2-6 AM"
        }
      }
    ]
  },
  "validation_options": {
    "require_approval": true,
    "validate_against_existing": true,
    "check_completeness": true
  }
}
```

**Response (201 Created):**
```json
{
  "submission_id": "uuid",
  "flow_id": "uuid",
  "status": "submitted",
  "submitted_at": "2025-07-19T15:30:00Z",
  "validation_results": {
    "passed_validation": true,
    "completeness_score": 0.87,
    "identified_issues": [],
    "suggestions": [
      "Consider adding performance metrics data",
      "Dependency information would improve analysis quality"
    ]
  },
  "next_steps": {
    "requires_approval": true,
    "estimated_processing_time": "30 minutes",
    "reviewer_assigned": "john.doe@company.com"
  }
}
```

### Upload Bulk Data

Upload structured data files for batch processing.

```http
POST /collection/flows/{flow_id}/bulk-upload
Content-Type: multipart/form-data
```

**Form Data:**
- `file` (file, required): CSV, Excel, or JSON file containing structured data
- `data_type` (string, required): Type of data being uploaded
- `template_id` (string, optional): ID of template used for data structure
- `validation_level` (string, optional): Validation strictness (strict|standard|lenient)

**Response (202 Accepted):**
```json
{
  "upload_id": "uuid",
  "flow_id": "uuid",
  "filename": "application_inventory.xlsx",
  "file_size": 2048576,
  "status": "processing",
  "upload_metadata": {
    "records_detected": 247,
    "columns_mapped": 18,
    "validation_level": "standard"
  },
  "processing_info": {
    "estimated_completion": "2025-07-19T16:00:00Z",
    "webhook_url": "/collection/flows/{flow_id}/bulk-upload/{upload_id}/status"
  }
}
```

### Get Bulk Upload Status

Check the status of a bulk data upload operation.

```http
GET /collection/flows/{flow_id}/bulk-upload/{upload_id}/status
```

**Response (200 OK):**
```json
{
  "upload_id": "uuid",
  "status": "completed",
  "processed_at": "2025-07-19T15:45:00Z",
  "processing_results": {
    "total_records": 247,
    "successful_imports": 239,
    "failed_imports": 8,
    "warnings": 15
  },
  "quality_assessment": {
    "overall_quality_score": 0.88,
    "completeness_percentage": 91,
    "data_consistency_score": 0.85
  },
  "validation_report": {
    "critical_errors": 0,
    "warnings": [
      "Missing technology stack for 8 applications",
      "Incomplete dependency information for 15 applications"
    ],
    "suggestions": [
      "Consider using application discovery template for missing fields",
      "Validate dependency mappings with network team"
    ]
  }
}
```

## Platform Adapter Endpoints

### List Available Adapters

Get list of available platform adapters and their capabilities.

```http
GET /collection/adapters
```

**Response (200 OK):**
```json
{
  "adapters": [
    {
      "id": "aws_ec2_adapter",
      "name": "AWS EC2 Adapter",
      "platform": "aws",
      "version": "2.1.0",
      "capabilities": {
        "resource_discovery": true,
        "configuration_analysis": true,
        "dependency_mapping": true,
        "performance_metrics": false
      },
      "supported_services": [
        "ec2", "rds", "lambda", "s3", "vpc", "iam"
      ],
      "requirements": {
        "credentials": ["access_key", "secret_key"],
        "permissions": ["ec2:Describe*", "rds:Describe*"],
        "network_access": ["https://ec2.amazonaws.com"]
      }
    }
  ]
}
```

### Test Adapter Connectivity

Test connectivity and permissions for a specific adapter.

```http
POST /collection/adapters/{adapter_id}/test
```

**Request Body:**
```json
{
  "credentials": {
    "access_key_id": "string",
    "secret_access_key": "string",
    "region": "us-east-1"
  },
  "test_scope": {
    "test_authentication": true,
    "test_permissions": true,
    "test_connectivity": true,
    "estimate_resources": true
  }
}
```

**Response (200 OK):**
```json
{
  "adapter_id": "aws_ec2_adapter",
  "test_results": {
    "authentication": {
      "status": "success",
      "message": "Credentials validated successfully"
    },
    "permissions": {
      "status": "partial",
      "message": "Missing IAM permissions for some operations",
      "missing_permissions": ["iam:GetRole", "iam:ListPolicies"]
    },
    "connectivity": {
      "status": "success",
      "response_time": "150ms"
    },
    "resource_estimation": {
      "estimated_instances": 125,
      "estimated_databases": 15,
      "estimated_load_balancers": 8,
      "estimated_collection_time": "45 minutes"
    }
  },
  "recommendations": [
    "Add IAM permissions for complete role analysis",
    "Consider running discovery during off-peak hours"
  ]
}
```

## Quality Assurance Endpoints

### Get Quality Assessment

Retrieve detailed quality assessment for collected data.

```http
GET /collection/flows/{flow_id}/quality-assessment
```

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "overall_quality": {
    "score": 0.92,
    "grade": "A",
    "completeness": 89,
    "accuracy": 95,
    "consistency": 88,
    "freshness": 96
  },
  "category_scores": {
    "applications": {
      "score": 0.94,
      "total_records": 247,
      "complete_records": 239,
      "missing_critical_fields": 8
    },
    "infrastructure": {
      "score": 0.89,
      "total_records": 156,
      "complete_records": 148,
      "missing_critical_fields": 12
    },
    "dependencies": {
      "score": 0.85,
      "total_relationships": 445,
      "verified_relationships": 389,
      "uncertain_relationships": 56
    }
  },
  "identified_gaps": [
    {
      "id": "uuid",
      "type": "missing_field",
      "severity": "medium",
      "description": "Missing technology stack information for 8 applications",
      "impact": "May affect modernization strategy recommendations",
      "suggested_action": "Conduct technical interviews for affected applications",
      "estimated_effort": "2-3 hours"
    }
  ]
}
```

### Get Data Gaps

Retrieve identified data gaps and recommendations for resolution.

```http
GET /collection/flows/{flow_id}/gaps?severity={severity}&category={category}
```

**Query Parameters:**
- `severity` (string, optional): Filter by severity (critical|high|medium|low)
- `category` (string, optional): Filter by data category
- `status` (string, optional): Filter by gap status (open|addressed|accepted)

**Response (200 OK):**
```json
{
  "flow_id": "uuid",
  "gaps": [
    {
      "id": "uuid",
      "type": "missing_dependency",
      "severity": "high",
      "category": "dependencies",
      "description": "Database connections not mapped for CustomerPortal application",
      "impact_assessment": {
        "affects_6r_analysis": true,
        "migration_complexity": "increased",
        "confidence_reduction": 0.15
      },
      "resolution_options": [
        {
          "method": "automated_network_analysis",
          "estimated_effort": "1 hour",
          "success_probability": 0.8,
          "prerequisites": ["network_monitoring_access"]
        },
        {
          "method": "manual_documentation_review",
          "estimated_effort": "3 hours", 
          "success_probability": 0.95,
          "prerequisites": ["application_documentation"]
        }
      ],
      "status": "open",
      "created_at": "2025-07-19T14:15:00Z"
    }
  ],
  "summary": {
    "total_gaps": 23,
    "critical": 2,
    "high": 8,
    "medium": 10,
    "low": 3
  }
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "COLLECTION_FLOW_ERROR",
    "message": "Human-readable error description",
    "details": {
      "field": "Specific field or parameter causing error",
      "constraint": "Business rule or constraint violated"
    },
    "trace_id": "uuid",
    "timestamp": "2025-07-19T15:30:00Z"
  }
}
```

### Common Error Codes

#### 400 Bad Request
- `INVALID_COLLECTION_TYPE`: Invalid collection type specified
- `MISSING_CREDENTIALS`: Required platform credentials not provided
- `INVALID_CONFIGURATION`: Collection configuration validation failed

#### 401 Unauthorized
- `AUTHENTICATION_FAILED`: Invalid or expired authentication token
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions

#### 404 Not Found
- `COLLECTION_FLOW_NOT_FOUND`: Specified Collection Flow does not exist
- `ADAPTER_NOT_FOUND`: Requested platform adapter not available

#### 409 Conflict
- `FLOW_ALREADY_EXECUTING`: Cannot start flow that is already executing
- `CONCURRENT_OPERATION`: Conflicting operation in progress

#### 422 Unprocessable Entity
- `PLATFORM_ACCESS_DENIED`: Platform credentials insufficient or expired
- `RESOURCE_LIMIT_EXCEEDED`: Collection scope exceeds platform limits

#### 500 Internal Server Error
- `ADAPTER_FAILURE`: Platform adapter encountered unexpected error
- `DATA_PROCESSING_ERROR`: Error during data transformation or storage

## Rate Limiting

### Rate Limit Headers

All responses include rate limiting information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1642694400
X-RateLimit-Window: 3600
```

### Rate Limits by Endpoint Category

- **Query Endpoints**: 100 requests per hour
- **Execution Endpoints**: 50 requests per hour
- **Data Upload Endpoints**: 20 requests per hour
- **Adapter Test Endpoints**: 10 requests per hour

## Webhooks

### Webhook Events

Collection Flows can send webhook notifications for key events:

#### Flow Status Changes
```json
{
  "event": "collection_flow.status_changed",
  "data": {
    "flow_id": "uuid",
    "previous_status": "executing",
    "current_status": "completed",
    "timestamp": "2025-07-19T14:30:00Z"
  }
}
```

#### Quality Threshold Violations
```json
{
  "event": "collection_flow.quality_threshold_violated",
  "data": {
    "flow_id": "uuid",
    "quality_score": 0.75,
    "threshold": 0.8,
    "affected_categories": ["dependencies"],
    "timestamp": "2025-07-19T13:45:00Z"
  }
}
```

#### Critical Errors
```json
{
  "event": "collection_flow.critical_error",
  "data": {
    "flow_id": "uuid",
    "error_type": "platform_access_denied",
    "error_message": "AWS credentials expired",
    "requires_intervention": true,
    "timestamp": "2025-07-19T12:30:00Z"
  }
}
```

## SDK and Integration Examples

### Python SDK Example

```python
from migration_orchestrator import CollectionFlowClient

# Initialize client
client = CollectionFlowClient(
    base_url="https://api.migration-orchestrator.com",
    access_token="your_access_token"
)

# Create and execute collection flow
flow = client.create_collection_flow(
    client_id="uuid",
    collection_type="automated",
    platform_type="aws",
    configuration={
        "scope": {
            "regions": ["us-east-1"],
            "scan_depth": "comprehensive"
        }
    }
)

# Initialize with credentials
client.initialize_flow(
    flow_id=flow.id,
    credentials={
        "aws": {
            "access_key_id": "your_key",
            "secret_access_key": "your_secret"
        }
    }
)

# Execute flow
execution = client.execute_flow(flow.id)

# Monitor progress
while execution.status in ["executing", "paused"]:
    status = client.get_status(flow.id)
    print(f"Progress: {status.overall_progress.percentage_complete}%")
    time.sleep(30)

# Retrieve collected data
data = client.get_collection_data(flow.id, format="json")
```

### JavaScript/Node.js Example

```javascript
const { CollectionFlowClient } = require('@migration-orchestrator/sdk');

const client = new CollectionFlowClient({
  baseUrl: 'https://api.migration-orchestrator.com',
  accessToken: process.env.ACCESS_TOKEN
});

async function runCollectionFlow() {
  try {
    // Create flow
    const flow = await client.createCollectionFlow({
      clientId: 'uuid',
      collectionType: 'automated',
      platformType: 'aws',
      configuration: {
        scope: {
          regions: ['us-east-1'],
          scanDepth: 'comprehensive'
        }
      }
    });

    // Initialize and execute
    await client.initializeFlow(flow.id, {
      credentials: {
        aws: {
          accessKeyId: process.env.AWS_ACCESS_KEY,
          secretAccessKey: process.env.AWS_SECRET_KEY
        }
      }
    });

    const execution = await client.executeFlow(flow.id);
    
    // Monitor with events
    client.onStatusChange(flow.id, (status) => {
      console.log(`Flow ${flow.id}: ${status.overall_progress.percentage_complete}% complete`);
    });

    // Wait for completion
    const result = await client.waitForCompletion(flow.id);
    const data = await client.getCollectionData(flow.id);
    
    return data;
  } catch (error) {
    console.error('Collection flow failed:', error);
    throw error;
  }
}
```

This comprehensive API documentation provides developers with all necessary information to integrate with the Collection Flow system, enabling efficient automation of data collection workflows across diverse cloud and on-premises environments.