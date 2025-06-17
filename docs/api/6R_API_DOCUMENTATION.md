# 6R Treatment Analysis - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URLs and Versioning](#base-urls-and-versioning)
4. [Common Schemas](#common-schemas)
5. [Analysis Endpoints](#analysis-endpoints)
6. [WebSocket API](#websocket-api)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [SDK and Client Libraries](#sdk-and-client-libraries)
10. [Examples](#examples)

## Overview

The 6R Treatment Analysis API provides programmatic access to the AI-powered cloud migration strategy recommendation system. The API follows REST principles and supports real-time updates via WebSocket connections.

### Key Features
- **RESTful Design**: Standard HTTP methods and status codes
- **JSON API**: All requests and responses use JSON format
- **Real-time Updates**: WebSocket support for live progress tracking
- **Bulk Operations**: Support for analyzing multiple applications
- **Comprehensive Error Handling**: Detailed error messages and codes
- **Rate Limiting**: Built-in protection against abuse
- **OpenAPI Specification**: Complete API specification available

### API Capabilities
- Create and manage 6R analyses
- Configure analysis parameters
- Submit qualifying questions and responses
- Monitor analysis progress in real-time
- Retrieve recommendations and detailed results
- Manage analysis history and comparisons
- Execute bulk analysis operations
- Export results in multiple formats

## Authentication

### Bearer Token Authentication
All API requests require authentication using Bearer tokens in the Authorization header.

```http
Authorization: Bearer <your-access-token>
```

### Obtaining Access Tokens
Access tokens are obtained through the organization's authentication system (OAuth 2.0, SAML, etc.).

```http
POST /auth/token
Content-Type: application/json

{
  "username": "user@company.com",
  "password": "password",
  "grant_type": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Token Refresh
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "grant_type": "refresh_token"
}
```

## Base URLs and Versioning

### Base URL
```
https://api.migration-orchestrator.company.com
```

### API Versioning
The API uses URL path versioning:
```
/api/v1/sixr/...
```

### Environment URLs
- **Production**: `https://api.migration-orchestrator.company.com`
- **Staging**: `https://staging-api.migration-orchestrator.company.com`
- **Development**: `https://dev-api.migration-orchestrator.company.com`

## Common Schemas

### SixRParameters
```json
{
  "business_value": 7,
  "technical_complexity": 5,
  "migration_urgency": 6,
  "compliance_requirements": 4,
  "cost_sensitivity": 5,
  "risk_tolerance": 6,
  "innovation_priority": 8,
  "application_type": "custom"
}
```

### QualifyingQuestion
```json
{
  "id": "app_type",
  "question": "What type of application is this?",
  "question_type": "select",
  "category": "Application Classification",
  "priority": 1,
  "required": true,
  "options": [
    {
      "value": "custom",
      "label": "Custom Application",
      "description": "Built in-house"
    }
  ],
  "help_text": "This affects which migration strategies are available"
}
```

### QuestionResponse
```json
{
  "question_id": "app_type",
  "response": "custom",
  "confidence": 0.9,
  "source": "user_input",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### SixRRecommendation
```json
{
  "recommended_strategy": "refactor",
  "confidence_score": 0.82,
  "strategy_scores": [
    {
      "strategy": "refactor",
      "score": 8.2,
      "confidence": 0.82,
      "rationale": ["High business value", "Moderate complexity"],
      "risk_factors": ["Requires skilled resources"],
      "benefits": ["Improved performance", "Better maintainability"]
    }
  ],
  "key_factors": [
    "Application type: Custom",
    "Business value: High"
  ],
  "assumptions": [
    "Development team has Java expertise"
  ],
  "next_steps": [
    "Conduct detailed code analysis"
  ],
  "estimated_effort": "high",
  "estimated_timeline": "4-6 months",
  "estimated_cost_impact": "moderate"
}
```

### AnalysisProgress
```json
{
  "analysisId": 123,
  "status": "in_progress",
  "overallProgress": 45,
  "currentStep": "processing",
  "estimatedTimeRemaining": 180,
  "steps": [
    {
      "id": "discovery",
      "name": "Data Discovery",
      "status": "completed",
      "progress": 100,
      "startTime": "2024-01-15T10:00:00Z",
      "endTime": "2024-01-15T10:05:00Z"
    }
  ]
}
```

## Analysis Endpoints

### Create Analysis
Create a new 6R analysis for one or more applications.

```http
POST /api/v1/sixr/analyze
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "application_ids": [1, 2, 3],
  "parameters": {
    "business_value": 7,
    "technical_complexity": 5,
    "migration_urgency": 6,
    "compliance_requirements": 4,
    "cost_sensitivity": 5,
    "risk_tolerance": 6,
    "innovation_priority": 8,
    "application_type": "custom"
  },
  "options": {
    "auto_generate_questions": true,
    "include_code_analysis": false,
    "priority": "medium"
  }
}
```

**Response (201 Created):**
```json
{
  "analysis_id": 123,
  "status": "created",
  "estimated_duration": 300,
  "message": "Analysis created successfully"
}
```

### Get Analysis Status
Retrieve the current status and progress of an analysis.

```http
GET /api/v1/sixr/analysis/{analysis_id}
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "analysisId": 123,
  "status": "in_progress",
  "overallProgress": 45,
  "currentStep": "processing",
  "estimatedTimeRemaining": 180,
  "steps": [
    {
      "id": "discovery",
      "name": "Data Discovery",
      "status": "completed",
      "progress": 100
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:15:00Z"
}
```

### Update Analysis Parameters
Update parameters for an existing analysis.

```http
PUT /api/v1/sixr/analysis/{analysis_id}/parameters
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "parameters": {
    "business_value": 8,
    "innovation_priority": 9
  },
  "trigger_reanalysis": true,
  "reason": "Updated business priorities"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Parameters updated successfully",
  "iteration_number": 2
}
```

### Submit Question Responses
Submit responses to qualifying questions.

```http
POST /api/v1/sixr/analysis/{analysis_id}/questions
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "responses": [
    {
      "question_id": "app_type",
      "response": "custom",
      "confidence": 0.9,
      "source": "user_input"
    },
    {
      "question_id": "user_count",
      "response": 1500,
      "confidence": 0.8,
      "source": "user_input"
    }
  ],
  "is_partial": false,
  "submitted_by": "user@company.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Questions submitted successfully",
  "processed_count": 2,
  "validation_errors": []
}
```

### Iterate Analysis
Start a new iteration of the analysis with updated parameters or responses.

```http
POST /api/v1/sixr/analysis/{analysis_id}/iterate
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "reason": "Refining based on stakeholder feedback",
  "changes": {
    "parameters": {
      "risk_tolerance": 8
    },
    "additional_context": "Updated risk assessment from security team"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "iteration_number": 2,
  "message": "Analysis iteration started"
}
```

### Get Recommendation
Retrieve the final recommendation for a completed analysis.

```http
GET /api/v1/sixr/analysis/{analysis_id}/recommendation
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "recommended_strategy": "refactor",
  "confidence_score": 0.82,
  "strategy_scores": [
    {
      "strategy": "refactor",
      "score": 8.2,
      "confidence": 0.82,
      "rationale": ["High business value", "Moderate complexity"],
      "risk_factors": ["Requires skilled resources"],
      "benefits": ["Improved performance", "Better maintainability"]
    }
  ],
  "key_factors": [
    "Application type: Custom",
    "Business value: High",
    "Innovation priority: High"
  ],
  "assumptions": [
    "Development team has Java expertise",
    "Testing environment available"
  ],
  "next_steps": [
    "Conduct detailed code analysis",
    "Define refactoring scope",
    "Establish development timeline"
  ],
  "estimated_effort": "high",
  "estimated_timeline": "4-6 months",
  "estimated_cost_impact": "moderate",
  "iteration_number": 1,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### List Analyses
Retrieve a list of analyses with filtering and pagination.

```http
GET /api/v1/sixr/analyses?page=1&limit=20&status=completed&strategy=refactor
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (created, in_progress, completed, failed)
- `strategy` (string): Filter by recommended strategy
- `confidence_min` (float): Minimum confidence score
- `confidence_max` (float): Maximum confidence score
- `date_from` (string): Start date (ISO 8601)
- `date_to` (string): End date (ISO 8601)
- `application_id` (integer): Filter by application ID
- `analyst` (string): Filter by analyst email

**Response (200 OK):**
```json
{
  "analyses": [
    {
      "id": 123,
      "application_name": "Customer Portal",
      "application_id": 1,
      "department": "Finance",
      "analysis_date": "2024-01-15T10:30:00Z",
      "analyst": "user@company.com",
      "status": "completed",
      "recommended_strategy": "refactor",
      "confidence_score": 0.82,
      "iteration_count": 1
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Delete Analysis
Delete an analysis and all associated data.

```http
DELETE /api/v1/sixr/analysis/{analysis_id}
Authorization: Bearer <token>
```

**Response (204 No Content)**

### Archive Analysis
Archive an analysis (soft delete).

```http
POST /api/v1/sixr/analysis/{analysis_id}/archive
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "reason": "Analysis superseded by newer version"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Analysis archived successfully"
}
```

### Export Analysis
Export analysis results in various formats.

```http
GET /api/v1/sixr/analysis/{analysis_id}/export?format=pdf
Authorization: Bearer <token>
```

**Query Parameters:**
- `format` (string): Export format (pdf, csv, json, excel)
- `include_details` (boolean): Include detailed analysis data
- `template` (string): Report template name

**Response (200 OK):**
Returns file content with appropriate Content-Type header.

## Bulk Analysis Endpoints

### Create Bulk Analysis Job
Create a bulk analysis job for multiple applications.

```http
POST /api/v1/sixr/bulk/analyze
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Q1 Portfolio Analysis",
  "description": "Quarterly analysis of all customer-facing applications",
  "application_ids": [1, 2, 3, 4, 5],
  "priority": "medium",
  "parameters": {
    "business_value": 7,
    "technical_complexity": 5,
    "migration_urgency": 6,
    "compliance_requirements": 4,
    "cost_sensitivity": 5,
    "risk_tolerance": 6,
    "innovation_priority": 8,
    "application_type": "custom"
  },
  "options": {
    "parallel_limit": 3,
    "retry_failed": true,
    "auto_approve_high_confidence": false,
    "confidence_threshold": 0.8,
    "notification_email": "analyst@company.com"
  }
}
```

**Response (201 Created):**
```json
{
  "job_id": "bulk-job-456",
  "message": "Bulk analysis job created successfully",
  "estimated_duration": 1800
}
```

### Get Bulk Job Status
Retrieve the status of a bulk analysis job.

```http
GET /api/v1/sixr/bulk/job/{job_id}
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "bulk-job-456",
  "name": "Q1 Portfolio Analysis",
  "status": "running",
  "priority": "medium",
  "created_at": "2024-01-15T09:00:00Z",
  "started_at": "2024-01-15T09:05:00Z",
  "progress": {
    "total": 5,
    "completed": 2,
    "failed": 0,
    "in_progress": 1,
    "pending": 2
  },
  "estimated_completion": "2024-01-15T09:35:00Z",
  "application_ids": [1, 2, 3, 4, 5]
}
```

### List Bulk Jobs
Retrieve a list of bulk analysis jobs.

```http
GET /api/v1/sixr/bulk/jobs?status=running&page=1&limit=10
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "id": "bulk-job-456",
      "name": "Q1 Portfolio Analysis",
      "status": "running",
      "created_at": "2024-01-15T09:00:00Z",
      "progress": {
        "total": 5,
        "completed": 2,
        "failed": 0,
        "in_progress": 1,
        "pending": 2
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
```

### Control Bulk Job
Start, stop, pause, or resume a bulk analysis job.

```http
POST /api/v1/sixr/bulk/job/{job_id}/control
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "action": "pause",
  "reason": "System maintenance required"
}
```

**Actions:**
- `start`: Start a created job
- `stop`: Stop a running job
- `pause`: Pause a running job
- `resume`: Resume a paused job
- `cancel`: Cancel a job (cannot be resumed)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Job paused successfully",
  "new_status": "paused"
}
```

### Delete Bulk Job
Delete a bulk analysis job and all associated data.

```http
DELETE /api/v1/sixr/bulk/job/{job_id}
Authorization: Bearer <token>
```

**Response (204 No Content)**

### Export Bulk Results
Export results from a bulk analysis job.

```http
GET /api/v1/sixr/bulk/job/{job_id}/export?format=excel
Authorization: Bearer <token>
```

**Response (200 OK):**
Returns file content with appropriate Content-Type header.

### Get Bulk Summary
Get summary statistics for bulk analysis operations.

```http
GET /api/v1/sixr/bulk/summary?date_from=2024-01-01&date_to=2024-01-31
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "total_jobs": 15,
  "active_jobs": 2,
  "completed_jobs": 12,
  "failed_jobs": 1,
  "total_applications_processed": 450,
  "average_confidence": 0.78,
  "strategy_distribution": {
    "rehost": 120,
    "replatform": 95,
    "refactor": 180,
    "rearchitect": 35,
    "rewrite": 15,
    "retire": 5
  },
  "processing_time_stats": {
    "min": 45,
    "max": 320,
    "average": 125,
    "total": 56250
  }
}
```

## WebSocket API

### Connection
Connect to the WebSocket endpoint for real-time updates.

```javascript
const ws = new WebSocket('wss://api.migration-orchestrator.company.com/ws/sixr');
```

### Authentication
Send authentication message after connection.

```json
{
  "type": "auth",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Subscribe to Analysis Updates
Subscribe to updates for a specific analysis.

```json
{
  "type": "subscribe",
  "analysis_id": 123
}
```

### Message Types

#### Analysis Progress Update
```json
{
  "type": "analysis_progress",
  "analysis_id": 123,
  "data": {
    "progress": 45,
    "step": "processing",
    "status": "in_progress",
    "estimated_time_remaining": 180
  }
}
```

#### Analysis Complete
```json
{
  "type": "analysis_complete",
  "analysis_id": 123,
  "data": {
    "recommendation": {
      "recommended_strategy": "refactor",
      "confidence_score": 0.82
    },
    "application_name": "Customer Portal",
    "application_id": 1,
    "department": "Finance"
  }
}
```

#### Analysis Error
```json
{
  "type": "analysis_error",
  "analysis_id": 123,
  "data": {
    "error_code": "INSUFFICIENT_DATA",
    "error_message": "Insufficient application data for analysis",
    "retry_possible": true
  }
}
```

#### Bulk Job Update
```json
{
  "type": "bulk_job_update",
  "job_id": "bulk-job-456",
  "data": {
    "status": "running",
    "progress": {
      "total": 5,
      "completed": 3,
      "failed": 0,
      "in_progress": 1,
      "pending": 1
    }
  }
}
```

### Unsubscribe
Unsubscribe from updates.

```json
{
  "type": "unsubscribe",
  "analysis_id": 123
}
```

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content returned
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameter values",
    "details": [
      {
        "field": "business_value",
        "message": "Value must be between 1 and 10"
      }
    ],
    "request_id": "req-123456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `RESOURCE_CONFLICT`: Resource already exists or in conflicting state
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INSUFFICIENT_DATA`: Insufficient data for analysis
- `ANALYSIS_FAILED`: Analysis execution failed
- `SYSTEM_ERROR`: Internal system error

## Rate Limiting

### Rate Limits
- **Analysis Creation**: 10 requests per minute per user
- **Bulk Operations**: 5 requests per hour per user
- **General API**: 1000 requests per hour per user
- **WebSocket Connections**: 10 concurrent connections per user

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded Response
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

## SDK and Client Libraries

### Official SDKs
- **Python**: `pip install sixr-analysis-sdk`
- **JavaScript/Node.js**: `npm install @company/sixr-analysis-sdk`
- **Java**: Maven/Gradle dependency available
- **C#**: NuGet package available

### Python SDK Example
```python
from sixr_analysis_sdk import SixRClient

client = SixRClient(
    base_url="https://api.migration-orchestrator.company.com",
    token="your-access-token"
)

# Create analysis
analysis = client.create_analysis(
    application_ids=[1, 2, 3],
    parameters={
        "business_value": 7,
        "technical_complexity": 5,
        "migration_urgency": 6,
        "compliance_requirements": 4,
        "cost_sensitivity": 5,
        "risk_tolerance": 6,
        "innovation_priority": 8,
        "application_type": "custom"
    }
)

# Monitor progress
for update in client.monitor_analysis(analysis.id):
    print(f"Progress: {update.progress}%")
    if update.status == "completed":
        break

# Get recommendation
recommendation = client.get_recommendation(analysis.id)
print(f"Recommended strategy: {recommendation.recommended_strategy}")
```

### JavaScript SDK Example
```javascript
import { SixRClient } from '@company/sixr-analysis-sdk';

const client = new SixRClient({
  baseUrl: 'https://api.migration-orchestrator.company.com',
  token: 'your-access-token'
});

// Create analysis
const analysis = await client.createAnalysis({
  applicationIds: [1, 2, 3],
  parameters: {
    businessValue: 7,
    technicalComplexity: 5,
    migrationUrgency: 6,
    complianceRequirements: 4,
    costSensitivity: 5,
    riskTolerance: 6,
    innovationPriority: 8,
    applicationType: 'custom'
  }
});

// Subscribe to real-time updates
client.subscribeToAnalysis(analysis.id, (update) => {
  console.log(`Progress: ${update.progress}%`);
  if (update.status === 'completed') {
    client.getRecommendation(analysis.id).then(recommendation => {
      console.log(`Recommended strategy: ${recommendation.recommendedStrategy}`);
    });
  }
});
```

## Examples

### Complete Analysis Workflow
```bash
# 1. Create analysis
curl -X POST "https://api.migration-orchestrator.company.com/api/v1/sixr/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "application_ids": [1],
    "parameters": {
      "business_value": 7,
      "technical_complexity": 5,
      "migration_urgency": 6,
      "compliance_requirements": 4,
      "cost_sensitivity": 5,
      "risk_tolerance": 6,
      "innovation_priority": 8,
      "application_type": "custom"
    }
  }'

# Response: {"analysis_id": 123, "status": "created"}

# 2. Monitor progress
curl -X GET "https://api.migration-orchestrator.company.com/api/v1/sixr/analysis/123" \
  -H "Authorization: Bearer $TOKEN"

# 3. Submit questions (when prompted)
curl -X POST "https://api.migration-orchestrator.company.com/api/v1/sixr/analysis/123/questions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "responses": [
      {
        "question_id": "app_type",
        "response": "custom",
        "confidence": 0.9,
        "source": "user_input"
      }
    ],
    "is_partial": false
  }'

# 4. Get final recommendation
curl -X GET "https://api.migration-orchestrator.company.com/api/v1/sixr/analysis/123/recommendation" \
  -H "Authorization: Bearer $TOKEN"
```

### Bulk Analysis Example
```bash
# Create bulk job
curl -X POST "https://api.migration-orchestrator.company.com/api/v1/sixr/bulk/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Portfolio Analysis",
    "application_ids": [1, 2, 3, 4, 5],
    "priority": "medium",
    "parameters": {
      "business_value": 7,
      "technical_complexity": 5,
      "migration_urgency": 6,
      "compliance_requirements": 4,
      "cost_sensitivity": 5,
      "risk_tolerance": 6,
      "innovation_priority": 8,
      "application_type": "custom"
    },
    "options": {
      "parallel_limit": 3,
      "retry_failed": true
    }
  }'

# Monitor bulk job
curl -X GET "https://api.migration-orchestrator.company.com/api/v1/sixr/bulk/job/bulk-job-456" \
  -H "Authorization: Bearer $TOKEN"

# Export results
curl -X GET "https://api.migration-orchestrator.company.com/api/v1/sixr/bulk/job/bulk-job-456/export?format=excel" \
  -H "Authorization: Bearer $TOKEN" \
  -o "portfolio_analysis.xlsx"
```

### WebSocket Integration Example
```javascript
const ws = new WebSocket('wss://api.migration-orchestrator.company.com/ws/sixr');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your-access-token'
  }));
  
  // Subscribe to analysis updates
  ws.send(JSON.stringify({
    type: 'subscribe',
    analysis_id: 123
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'analysis_progress':
      console.log(`Progress: ${message.data.progress}%`);
      break;
    case 'analysis_complete':
      console.log('Analysis completed!');
      console.log(`Recommendation: ${message.data.recommendation.recommended_strategy}`);
      break;
    case 'analysis_error':
      console.error(`Analysis failed: ${message.data.error_message}`);
      break;
  }
};
```

---

## Support and Resources

### Documentation
- **API Reference**: Complete OpenAPI specification
- **SDK Documentation**: Language-specific SDK guides
- **Integration Examples**: Sample applications and code
- **Best Practices**: Recommended usage patterns

### Support Channels
- **Developer Portal**: https://developers.migration-orchestrator.company.com
- **API Support**: api-support@company.com
- **Community Forum**: https://community.migration-orchestrator.company.com
- **Status Page**: https://status.migration-orchestrator.company.com

### Changelog
- **v1.0**: Initial API release
- **v1.1**: Added bulk analysis endpoints
- **v1.2**: Enhanced WebSocket support
- **v1.3**: Added export functionality
- **v2.0**: Major API improvements and new features

---

*This API documentation is maintained by the Migration UI Orchestrator team. For the latest updates and additional resources, visit the developer portal.* 