# Agent Performance API Documentation

## Overview

The Agent Performance API provides comprehensive observability into individual agent performance metrics, task execution history, and analytics. This API is part of the Agent Observability Enhancement Phase 3.

## Base URL

All endpoints are prefixed with `/api/v1/monitoring`

## Authentication

All endpoints require authentication via Bearer token in the Authorization header.

## Endpoints

### 1. Get Agent Performance

Get comprehensive performance metrics for an individual agent.

**Endpoint:** `GET /api/v1/monitoring/agents/{agent_name}/performance`

**Parameters:**
- `agent_name` (path, required): Name of the agent
- `days` (query, optional): Number of days to analyze (1-90, default: 7)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "agent_name": "DataAnalysisAgent",
    "period_days": 7,
    "summary": {
      "total_tasks": 150,
      "successful_tasks": 142,
      "failed_tasks": 8,
      "success_rate": 94.67,
      "avg_duration_seconds": 12.5,
      "avg_confidence_score": 0.89,
      "total_llm_calls": 450,
      "total_thinking_phases": 300
    },
    "token_usage": {
      "total_input_tokens": 125000,
      "total_output_tokens": 87500,
      "total_tokens": 212500,
      "avg_tokens_per_task": 1416.67
    },
    "error_patterns": [
      {"error_type": "timeout", "count": 5},
      {"error_type": "validation_error", "count": 3}
    ],
    "trends": {
      "dates": ["2025-01-15", "2025-01-16", ...],
      "success_rates": [95.0, 93.5, ...],
      "avg_durations": [11.2, 13.1, ...],
      "task_counts": [20, 22, ...],
      "confidence_scores": [0.88, 0.90, ...]
    },
    "current_status": {
      "is_active": true,
      "active_tasks": [...],
      "last_activity": "2025-01-21T10:29:45Z"
    }
  }
}
```

### 2. Get Agent Task History

Get paginated task execution history for an agent.

**Endpoint:** `GET /api/v1/monitoring/agents/{agent_name}/history`

**Parameters:**
- `agent_name` (path, required): Name of the agent
- `limit` (query, optional): Maximum tasks to return (1-500, default: 50)
- `offset` (query, optional): Pagination offset (default: 0)
- `status_filter` (query, optional): Filter by status (completed, failed, timeout)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "agent_name": "DataAnalysisAgent",
    "total_tasks": 342,
    "limit": 50,
    "offset": 0,
    "tasks": [
      {
        "id": "task-123",
        "agent_name": "DataAnalysisAgent",
        "task_description": "Analyze customer data patterns",
        "status": "completed",
        "success": true,
        "started_at": "2025-01-21T10:15:00Z",
        "completed_at": "2025-01-21T10:15:12Z",
        "duration_seconds": 12,
        "confidence_score": 0.92,
        "llm_calls_count": 3,
        "thinking_phases_count": 2,
        "token_usage": {
          "input_tokens": 850,
          "output_tokens": 620,
          "total_tokens": 1470
        }
      }
      // ... more tasks
    ]
  }
}
```

### 3. Get Agent Analytics

Get detailed analytics for an agent including performance distribution and resource usage.

**Endpoint:** `GET /api/v1/monitoring/agents/{agent_name}/analytics`

**Parameters:**
- `agent_name` (path, required): Name of the agent
- `period_days` (query, optional): Analysis period in days (1-90, default: 7)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "agent_name": "DataAnalysisAgent",
    "period_days": 7,
    "analytics": {
      "performance_distribution": {
        "duration_percentiles": {
          "p25": 8.5,
          "p50": 12.0,
          "p75": 16.2,
          "p90": 22.5,
          "p95": 28.1,
          "p99": 45.3
        },
        "status_distribution": {
          "completed": 142,
          "failed": 5,
          "timeout": 3
        }
      },
      "resource_usage": {
        "avg_memory_usage_mb": 256.4,
        "peak_memory_usage_mb": 512.0,
        "llm_call_distribution": {
          "0-5": 45,
          "5-10": 80,
          "10-15": 20,
          "15-20": 5
        }
      },
      "pattern_discovery": {
        "total_patterns_discovered": 23,
        "pattern_types": {
          "data_anomaly": 12,
          "optimization": 8,
          "error_pattern": 3
        },
        "total_pattern_references": 156,
        "high_confidence_patterns": 18,
        "avg_confidence_score": 0.85
      },
      "task_complexity": {
        "complexity_distribution": {
          "simple": 65,
          "moderate": 55,
          "complex": 25,
          "very_complex": 5
        },
        "avg_thinking_phases_per_task": 2.1
      }
    },
    "performance_trends": {
      // ... daily performance metrics
    }
  }
}
```

### 4. Get Agents Activity Feed

Get real-time activity feed for all agents or specific agent.

**Endpoint:** `GET /api/v1/monitoring/agents/activity-feed`

**Parameters:**
- `limit` (query, optional): Maximum activities (1-500, default: 100)
- `agent_filter` (query, optional): Filter by specific agent name
- `include_completed` (query, optional): Include completed tasks (default: true)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "activities": [
      {
        "id": "act-456",
        "type": "task_active",
        "agent": "DataAnalysisAgent",
        "task": "Processing customer segment data",
        "status": "active",
        "started_at": "2025-01-21T10:29:00Z",
        "duration_seconds": 60,
        "details": {...}
      },
      {
        "id": "task-123",
        "type": "task_completed",
        "agent": "ValidationAgent",
        "task": "Validate data integrity",
        "status": "completed",
        "started_at": "2025-01-21T10:28:00Z",
        "completed_at": "2025-01-21T10:28:45Z",
        "duration_seconds": 45,
        "success": true,
        "confidence_score": 0.95,
        "details": {...}
      }
      // ... more activities
    ],
    "total_activities": 100,
    "monitoring_active": true,
    "filters": {
      "agent": null,
      "include_completed": true,
      "limit": 100
    }
  }
}
```

### 5. Get Discovered Patterns

Get patterns discovered by agents during task execution.

**Endpoint:** `GET /api/v1/monitoring/agents/discovered-patterns`

**Parameters:**
- `agent_name` (query, optional): Filter by agent name
- `pattern_type` (query, optional): Filter by pattern type
- `min_confidence` (query, optional): Minimum confidence score (0.0-1.0, default: 0.0)
- `limit` (query, optional): Maximum patterns (1-500, default: 100)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "patterns": [
      {
        "id": "pattern-789",
        "pattern_type": "data_anomaly",
        "pattern_name": "Seasonal Purchase Pattern",
        "description": "Detected seasonal variation in purchase behavior",
        "metadata": {
          "season": "winter",
          "variance": 0.35
        },
        "confidence_score": 0.92,
        "times_referenced": 12,
        "discovered_by_agent": "DataAnalysisAgent",
        "discovered_at": "2025-01-20T14:30:00Z",
        "created_at": "2025-01-20T14:30:00Z"
      }
      // ... more patterns
    ],
    "total_patterns": 23,
    "filters": {
      "agent_name": null,
      "pattern_type": null,
      "min_confidence": 0.0
    }
  }
}
```

### 6. Get All Agents Summary

Get performance summary for all agents in the current context.

**Endpoint:** `GET /api/v1/monitoring/agents/summary`

**Parameters:**
- `days` (query, optional): Number of days to analyze (1-90, default: 7)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "period_days": 7,
    "agents": [
      {
        "agent_name": "DataAnalysisAgent",
        "total_tasks": 150,
        "total_completed": 142,
        "avg_success_rate": 94.67,
        "avg_duration_seconds": 12.5,
        "total_llm_calls": 450,
        "is_active": true
      },
      {
        "agent_name": "ValidationAgent",
        "total_tasks": 120,
        "total_completed": 118,
        "avg_success_rate": 98.33,
        "avg_duration_seconds": 8.2,
        "total_llm_calls": 240,
        "is_active": false
      }
      // ... more agents
    ],
    "total_agents": 12,
    "active_agents": 3
  }
}
```

### 7. Trigger Performance Aggregation

Manually trigger performance aggregation for a specific date.

**Endpoint:** `POST /api/v1/monitoring/agents/performance/aggregate`

**Parameters:**
- `target_date` (query, optional): Target date YYYY-MM-DD (defaults to yesterday)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-21T10:30:00Z",
  "message": "Performance aggregation triggered for 2025-01-20",
  "target_date": "2025-01-20"
}
```

## Enhanced Monitoring Status Endpoint

The existing `/api/v1/monitoring/status` endpoint has been enhanced with individual agent performance data.

**Endpoint:** `GET /api/v1/monitoring/status`

**New Parameter:**
- `include_individual_agents` (query, optional): Include individual agent performance data (default: false)

When `include_individual_agents=true`, the response includes:
```json
{
  // ... existing response fields ...
  "individual_agent_performance": {
    "period_days": 7,
    "agents": [
      {
        "agent_name": "DataAnalysisAgent",
        "total_tasks": 150,
        "total_completed": 142,
        "avg_success_rate": 94.67,
        "avg_duration_seconds": 12.5,
        "total_llm_calls": 450,
        "is_active": true
      }
      // ... more agents
    ],
    "data_source": "agent_performance_daily"
  }
}
```

## Error Handling

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized
- `404`: Not Found (agent not found)
- `500`: Internal Server Error

## Rate Limiting

These endpoints are subject to the platform's standard rate limiting policies.

## Data Retention

- Task history is retained for 90 days
- Daily performance aggregations are retained for 1 year
- Discovered patterns are retained indefinitely

## Performance Considerations

- Use pagination for large result sets
- Consider caching frequently accessed agent performance data
- Activity feed queries are optimized for recent data
- Analytics endpoints may have higher latency for large date ranges