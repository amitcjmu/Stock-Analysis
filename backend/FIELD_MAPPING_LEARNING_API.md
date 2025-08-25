# Field Mapping Learning API Documentation

## Overview

The Field Mapping Learning API provides endpoints for creating a feedback loop that improves field mapping intelligence over time. Users can approve or reject mapping suggestions, and the system learns from these decisions to make better suggestions in the future.

## Base URL

All endpoints are available under the base path:
```
/api/v1/field-mapping/
```

## Authentication

All endpoints require:
- Valid JWT authentication token
- Client account context (automatically injected via RequestContext)
- Engagement scope for multi-tenant security

## Endpoints

### 1. Approve Field Mapping with Learning

**POST** `/api/v1/field-mapping/{mapping_id}/approve`

Approve a field mapping and learn from the approval to improve future suggestions.

#### Parameters
- `mapping_id` (path): UUID of the field mapping to approve

#### Request Body
```json
{
  "confidence_adjustment": 0.95,
  "metadata": {
    "reason": "User confirmed mapping is correct",
    "context": "Asset import workflow"
  },
  "learn_from_approval": true,
  "approval_note": "Mapping looks correct based on data sample review"
}
```

#### Response
```json
{
  "mapping_id": "123e4567-e89b-12d3-a456-426614174000",
  "action": "approve",
  "success": true,
  "learned_pattern_id": "456e7890-e89b-12d3-a456-426614174001",
  "confidence_score": 0.95,
  "patterns_created": 1,
  "patterns_updated": 0
}
```

#### Learning Behavior
- Creates positive patterns for the approved mapping
- Adjusts confidence scores based on user feedback
- Stores metadata about why the mapping was approved
- Updates mapping status to 'approved'

---

### 2. Reject Field Mapping with Learning

**POST** `/api/v1/field-mapping/{mapping_id}/reject`

Reject a field mapping and learn from the rejection to avoid similar mistakes.

#### Parameters
- `mapping_id` (path): UUID of the field mapping to reject

#### Request Body
```json
{
  "rejection_reason": "Source field maps to wrong target - should be customer info not asset data",
  "alternative_suggestion": "customer_name",
  "metadata": {
    "confidence_before_rejection": 0.8,
    "user_expertise": "domain_expert"
  },
  "learn_from_rejection": true
}
```

#### Response
```json
{
  "mapping_id": "123e4567-e89b-12d3-a456-426614174000",
  "action": "reject",
  "success": true,
  "confidence_score": 0.1,
  "patterns_created": 2,
  "patterns_updated": 0
}
```

#### Learning Behavior
- Creates negative patterns for the rejected mapping
- Creates positive patterns for alternative suggestions (if provided)
- Stores rejection reason for future reference
- Updates mapping status to 'rejected'

---

### 3. Bulk Learning from Multiple Mappings

**POST** `/api/v1/field-mapping/learn`

Learn from multiple field mappings in a single operation for efficient batch processing.

#### Request Body
```json
{
  "actions": [
    {
      "mapping_id": "123e4567-e89b-12d3-a456-426614174000",
      "action": "approve",
      "confidence_adjustment": 0.9,
      "metadata": {"batch_review": true}
    },
    {
      "mapping_id": "123e4567-e89b-12d3-a456-426614174001",
      "action": "reject",
      "rejection_reason": "Incorrect field mapping",
      "alternative_suggestion": "asset_type"
    }
  ],
  "learn_globally": true,
  "context_metadata": {
    "batch_id": "batch_2024_001",
    "reviewer": "data_analyst_jane"
  }
}
```

#### Response
```json
{
  "total_actions": 2,
  "successful_actions": 2,
  "failed_actions": 0,
  "results": [
    {
      "mapping_id": "123e4567-e89b-12d3-a456-426614174000",
      "action": "approve",
      "success": true,
      "patterns_created": 1,
      "patterns_updated": 0
    },
    {
      "mapping_id": "123e4567-e89b-12d3-a456-426614174001",
      "action": "reject",
      "success": true,
      "patterns_created": 2,
      "patterns_updated": 0
    }
  ],
  "global_patterns_created": 3,
  "global_patterns_updated": 0
}
```

---

### 4. Get Learned Patterns

**GET** `/api/v1/field-mapping/learned`

Retrieve learned patterns for the current context to understand what the system has learned.

#### Query Parameters
- `pattern_type` (optional): Filter by pattern type (`field_mapping_approval`, `field_mapping_rejection`, etc.)
- `insight_type` (optional): Filter by insight type (`field_mapping_suggestion`)
- `limit` (optional): Maximum patterns to return (1-1000, default: 100)

#### Response
```json
{
  "total_patterns": 25,
  "patterns": [
    {
      "pattern_id": "789e0123-e89b-12d3-a456-426614174002",
      "pattern_type": "field_mapping_approval",
      "pattern_name": "Approved mapping: device_name → asset_name",
      "confidence_score": 0.9,
      "evidence_count": 3,
      "times_referenced": 12,
      "effectiveness_score": 0.85,
      "insight_type": "field_mapping_suggestion",
      "created_at": "2024-08-24T10:30:00Z",
      "last_used_at": "2024-08-24T14:20:00Z"
    }
  ],
  "context_type": "field_mapping",
  "engagement_id": "abc12345-e89b-12d3-a456-426614174003"
}
```

---

### 5. Refresh Learned Patterns Cache

**POST** `/api/v1/field-mapping/learned/refresh`

Refresh the learned patterns cache when patterns are updated externally.

#### Response
```json
{
  "status": "success",
  "message": "Learned patterns cache refreshed successfully"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (validation errors, invalid parameters)
- **404**: Not Found (mapping doesn't exist or access denied)
- **500**: Internal Server Error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Schema Definitions

### LearningApprovalRequest
```json
{
  "confidence_adjustment": 0.95,        // Optional: 0.0-1.0
  "metadata": {...},                    // Optional: additional metadata
  "learn_from_approval": true,          // Default: true
  "approval_note": "string"             // Optional: max 500 chars
}
```

### LearningRejectionRequest
```json
{
  "rejection_reason": "string",         // Required: 1-500 chars
  "alternative_suggestion": "string",   // Optional: max 255 chars
  "metadata": {...},                    // Optional: additional metadata
  "learn_from_rejection": true          // Default: true
}
```

### MappingLearningAction
```json
{
  "mapping_id": "uuid",                 // Required
  "action": "approve|reject",           // Required
  "confidence_adjustment": 0.9,         // Optional: 0.0-1.0
  "rejection_reason": "string",         // Optional: for reject actions
  "alternative_suggestion": "string",   // Optional: for reject actions
  "metadata": {...}                     // Optional: additional metadata
}
```

## Multi-Tenant Security

- All operations are scoped to the authenticated user's client account
- Patterns are isolated by engagement for proper multi-tenant data separation
- Cross-tenant data access is prevented through database-level filtering

## Pattern Types Created

### Approval Patterns
- **field_mapping_approval**: Positive patterns for approved mappings
- Evidence includes original confidence, adjusted confidence, approval metadata
- High confidence scores (typically 0.8-1.0)

### Rejection Patterns
- **field_mapping_rejection**: Negative patterns for rejected mappings
- Evidence includes rejection reason and original mapping details
- Low confidence scores (typically 0.0-0.2)

### Alternative Patterns
- **field_mapping_alternative**: Positive patterns for user-suggested alternatives
- Created when rejections include alternative suggestions
- High confidence scores (typically 0.9+)

## Usage Examples

### Approve a mapping after manual review
```bash
curl -X POST "/api/v1/field-mapping/123e4567-e89b-12d3-a456-426614174000/approve" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "confidence_adjustment": 0.95,
    "approval_note": "Confirmed correct after data sample review",
    "metadata": {"reviewer": "domain_expert"}
  }'
```

### Reject a mapping with alternative suggestion
```bash
curl -X POST "/api/v1/field-mapping/123e4567-e89b-12d3-a456-426614174001/reject" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "Maps to wrong field type - should be text not numeric",
    "alternative_suggestion": "description_text",
    "metadata": {"issue_type": "data_type_mismatch"}
  }'
```

### Bulk learn from batch review
```bash
curl -X POST "/api/v1/field-mapping/learn" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "actions": [
      {
        "mapping_id": "uuid1",
        "action": "approve",
        "confidence_adjustment": 0.9
      },
      {
        "mapping_id": "uuid2",
        "action": "reject",
        "rejection_reason": "Incorrect mapping"
      }
    ],
    "context_metadata": {"batch_review": "weekly_cleanup"}
  }'
```

## Integration with AI System

The learned patterns are automatically used by the field mapping AI system to:

1. **Improve Suggestions**: Higher confidence for patterns similar to approved mappings
2. **Avoid Mistakes**: Lower confidence for patterns similar to rejected mappings
3. **Suggest Alternatives**: Recommend user-suggested alternatives for similar source fields
4. **Calibrate Confidence**: Adjust confidence scores based on historical feedback

This creates a continuous improvement loop where the system gets smarter over time based on real user feedback.
