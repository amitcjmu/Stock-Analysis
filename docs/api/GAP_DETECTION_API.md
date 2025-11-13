
# Gap Detection API Documentation

**Version:** 1.0
**Issue:** #980
**Author:** CC (Claude Code)
**Date:** November 2025

## Overview

The Gap Detection API provides real-time, multi-layer analysis of asset data completeness, enabling intelligent questionnaire generation and assessment readiness determination.

## Base URL

```
/api/v1/gap-detection
```

## Authentication

All endpoints require authentication via JWT token:
```
Authorization: Bearer <token>
```

## Tenant Scoping

All endpoints automatically scope data by:
- `client_account_id` (from JWT context)
- `engagement_id` (from query parameter or request body)

---

## Endpoints

### 1. Analyze Single Asset

**GET** `/api/v1/gap-detection/analyze/{asset_id}`

Perform comprehensive gap analysis on a single asset across all 5 inspection layers.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `asset_id` | UUID | Yes | Asset UUID to analyze |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `engagement_id` | UUID | Yes | Engagement UUID for tenant scoping |

#### Response

**Status:** 200 OK

```json
{
  "asset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "asset_name": "prod-app-01",
  "overall_completeness": 0.73,
  "assessment_ready": false,
  "all_gaps": [
    {
      "field_name": "database_version",
      "gap_type": "missing",
      "priority": "critical",
      "reason": "Required for migration planning and compatibility analysis",
      "inspector": "enrichment_inspector",
      "remediation_hint": "Provide the database version (e.g., PostgreSQL 14.2)"
    },
    {
      "field_name": "compliance_requirements",
      "gap_type": "missing",
      "priority": "high",
      "reason": "Required for regulatory compliance validation",
      "inspector": "enrichment_inspector",
      "remediation_hint": "Specify compliance standards (e.g., PCI-DSS, HIPAA)"
    }
  ],
  "blocking_gaps": [
    {
      "field_name": "database_version",
      "gap_type": "missing",
      "priority": "critical",
      "reason": "Required for migration planning and compatibility analysis",
      "inspector": "enrichment_inspector",
      "remediation_hint": "Provide the database version (e.g., PostgreSQL 14.2)"
    }
  ],
  "gap_summary": {
    "total_gaps": 12,
    "critical_gaps": 1,
    "high_gaps": 2,
    "medium_gaps": 5,
    "low_gaps": 4
  }
}
```

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Asset not found or access denied"
}
```

**422 Unprocessable Entity**
```json
{
  "detail": "Invalid asset_id format"
}
```

---

### 2. Batch Asset Analysis

**POST** `/api/v1/gap-detection/analyze-batch`

Analyze multiple assets in a single request. Optimized for performance with parallel processing.

#### Request Body

```json
{
  "asset_ids": [
    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "7gb96g75-6828-5673-c4gd-3d074g77bgb7"
  ],
  "engagement_id": "1ab23c45-6789-0def-1234-56789abcdef0"
}
```

#### Response

**Status:** 200 OK

```json
{
  "reports": [
    {
      "asset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "asset_name": "prod-app-01",
      "overall_completeness": 0.85,
      "assessment_ready": true,
      "gap_summary": {
        "total_gaps": 3,
        "critical_gaps": 0,
        "high_gaps": 1,
        "medium_gaps": 2,
        "low_gaps": 0
      }
    },
    {
      "asset_id": "7gb96g75-6828-5673-c4gd-3d074g77bgb7",
      "asset_name": "prod-app-02",
      "overall_completeness": 0.60,
      "assessment_ready": false,
      "gap_summary": {
        "total_gaps": 15,
        "critical_gaps": 3,
        "high_gaps": 5,
        "medium_gaps": 4,
        "low_gaps": 3
      }
    }
  ],
  "summary": {
    "total_assets": 2,
    "assessment_ready_count": 1,
    "not_ready_count": 1,
    "average_completeness": 0.725,
    "total_gaps": 18,
    "total_critical_gaps": 3,
    "total_high_gaps": 6
  }
}
```

#### Performance

- Target: <200ms for 10 assets
- Maximum: 1000 assets per request

---

### 3. Assessment Readiness Summary

**GET** `/api/v1/gap-detection/readiness-summary`

Get engagement-level summary of assessment readiness across all assets.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `engagement_id` | UUID | Yes | Engagement UUID |

#### Response

**Status:** 200 OK

```json
{
  "engagement_id": "1ab23c45-6789-0def-1234-56789abcdef0",
  "total_assets": 50,
  "assessment_ready": 35,
  "not_ready": 15,
  "average_completeness": 0.78,
  "completeness_distribution": {
    "0.0-0.2": 2,
    "0.2-0.4": 3,
    "0.4-0.6": 5,
    "0.6-0.8": 15,
    "0.8-1.0": 25
  },
  "top_blocking_gaps": [
    {
      "field_name": "database_version",
      "asset_count": 12,
      "priority": "critical"
    },
    {
      "field_name": "compliance_requirements",
      "asset_count": 8,
      "priority": "high"
    },
    {
      "field_name": "backup_frequency",
      "asset_count": 6,
      "priority": "high"
    }
  ],
  "inspector_summary": {
    "column_inspector": {
      "gaps_found": 45
    },
    "enrichment_inspector": {
      "gaps_found": 78
    },
    "jsonb_inspector": {
      "gaps_found": 12
    },
    "requirements_inspector": {
      "gaps_found": 34
    },
    "standards_inspector": {
      "gaps_found": 23
    }
  }
}
```

---

### 4. Gap Details by Field

**GET** `/api/v1/gap-detection/field-analysis/{field_name}`

Analyze a specific field across all assets in an engagement to identify patterns.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `field_name` | string | Yes | Field name to analyze (e.g., "database_version") |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `engagement_id` | UUID | Yes | Engagement UUID |

#### Response

**Status:** 200 OK

```json
{
  "field_name": "database_version",
  "engagement_id": "1ab23c45-6789-0def-1234-56789abcdef0",
  "total_assets": 50,
  "missing_count": 12,
  "present_count": 38,
  "completion_rate": 0.76,
  "priority": "critical",
  "assets_with_gap": [
    {
      "asset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "asset_name": "prod-app-01",
      "gap_reason": "Required for migration planning"
    }
  ],
  "value_distribution": {
    "PostgreSQL 14": 15,
    "PostgreSQL 13": 10,
    "MySQL 8.0": 8,
    "SQL Server 2019": 5
  }
}
```

---

### 5. Questionnaire Generation from Gaps

**POST** `/api/v1/gap-detection/generate-questionnaire`

Generate targeted questionnaires based on gap analysis results.

#### Request Body

```json
{
  "asset_ids": [
    "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  ],
  "engagement_id": "1ab23c45-6789-0def-1234-56789abcdef0",
  "collection_flow_id": "8cd45e67-8901-2fgh-3456-78901ijklmno",
  "priority_filter": ["critical", "high"]
}
```

#### Response

**Status:** 200 OK

```json
{
  "status": "success",
  "questionnaires": [
    {
      "section_id": "database_information",
      "section_title": "Database Information",
      "section_description": "Please provide information about your database systems",
      "questions": [
        {
          "question_id": "q_database_version_001",
          "question_text": "What is the version of your database system for prod-app-01?",
          "question_type": "text",
          "required": true,
          "validation_rules": {
            "pattern": "^[a-zA-Z0-9\\s\\.]+$",
            "max_length": 100
          },
          "remediation_hint": "Provide the database version (e.g., PostgreSQL 14.2)",
          "gap_context": {
            "field_name": "database_version",
            "priority": "critical",
            "inspector": "enrichment_inspector"
          }
        }
      ]
    }
  ],
  "metadata": {
    "total_sections": 1,
    "total_questions": 1,
    "assets_analyzed": 1,
    "gaps_processed": 1
  }
}
```

---

## Data Models

### FieldGap

```typescript
interface FieldGap {
  field_name: string;
  gap_type: "missing" | "invalid" | "incomplete";
  priority: "critical" | "high" | "medium" | "low";
  reason: string;
  inspector: string;
  remediation_hint?: string;
}
```

### ComprehensiveGapReport

```typescript
interface ComprehensiveGapReport {
  asset_id: string;
  asset_name?: string;
  overall_completeness: number;  // 0.0 to 1.0
  assessment_ready: boolean;
  all_gaps: FieldGap[];
  blocking_gaps: FieldGap[];
  gap_summary: {
    total_gaps: number;
    critical_gaps: number;
    high_gaps: number;
    medium_gaps: number;
    low_gaps: number;
  };
}
```

### GapPriority

```typescript
enum GapPriority {
  CRITICAL = "critical",  // Blocks assessment
  HIGH = "high",          // Important but not blocking
  MEDIUM = "medium",      // Nice-to-have
  LOW = "low"            // Optional enhancement
}
```

### GapType

```typescript
enum GapType {
  MISSING = "missing",      // Field is null/empty
  INVALID = "invalid",      // Field value doesn't meet requirements
  INCOMPLETE = "incomplete" // Field partially filled
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "GAP_001",
  "request_id": "req_abc123"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `GAP_001` | Asset not found |
| `GAP_002` | Invalid engagement_id |
| `GAP_003` | Analysis failed |
| `GAP_004` | Questionnaire generation failed |
| `GAP_005` | Batch limit exceeded (>1000 assets) |

---

## Rate Limiting

- **Single Asset Analysis:** 100 requests/minute per user
- **Batch Analysis:** 10 requests/minute per user
- **Readiness Summary:** 30 requests/minute per user

Exceeded rate limits return **429 Too Many Requests**.

---

## Performance Guidelines

### Response Times

| Endpoint | Target | Maximum |
|----------|--------|---------|
| Single Asset | <50ms | 100ms |
| Batch (10 assets) | <200ms | 500ms |
| Batch (100 assets) | <2s | 5s |
| Readiness Summary | <500ms | 1s |

### Optimization Tips

1. **Use Batch Endpoint**: Analyzing 10 assets in batch is 5x faster than 10 individual calls
2. **Cache Results**: Gap reports can be cached for 5 minutes without data staleness
3. **Filter Priority**: Use `priority_filter` to reduce response size
4. **Pagination**: For engagements with 100+ assets, use pagination on readiness summary

---

## Examples

### Example 1: Analyze Single Asset (cURL)

```bash
curl -X GET \
  "https://api.example.com/api/v1/gap-detection/analyze/3fa85f64-5717-4562-b3fc-2c963f66afa6?engagement_id=1ab23c45-6789-0def-1234-56789abcdef0" \
  -H "Authorization: Bearer {YOUR_API_TOKEN}"
```

### Example 2: Batch Analysis (Python)

```python
import requests

url = "https://api.example.com/api/v1/gap-detection/analyze-batch"
headers = {"Authorization": "Bearer {YOUR_API_TOKEN}"}
payload = {
    "asset_ids": [
        "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "7gb96g75-6828-5673-c4gd-3d074g77bgb7"
    ],
    "engagement_id": "1ab23c45-6789-0def-1234-56789abcdef0"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

for report in data["reports"]:
    print(f"{report['asset_name']}: {report['overall_completeness']:.1%} complete")
```

### Example 3: Generate Questionnaire (TypeScript)

```typescript
const response = await fetch(
  'https://api.example.com/api/v1/gap-detection/generate-questionnaire',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      asset_ids: ['3fa85f64-5717-4562-b3fc-2c963f66afa6'],
      engagement_id: '1ab23c45-6789-0def-1234-56789abcdef0',
      collection_flow_id: '8cd45e67-8901-2fgh-3456-78901ijklmno',
      priority_filter: ['critical', 'high'],
    }),
  }
);

const { questionnaires } = await response.json();
console.log(`Generated ${questionnaires.length} sections`);
```

---

## Changelog

### Version 1.0 (November 2025)
- Initial release
- 5-layer gap detection
- Batch analysis support
- Questionnaire generation integration

---

## Support

For API support, contact:
- **Engineering:** support@example.com
- **Documentation:** https://docs.example.com/gap-detection
- **Status Page:** https://status.example.com

