# API Specifications for Asset Enrichment

## Overview

This document details the API endpoints, request/response schemas, and integration points required to support the asset enrichment system. All endpoints extend the existing v1 API and integrate seamlessly with the current agent-ui-bridge infrastructure.

## Enhanced Discovery Flow Endpoints

### **Core Enrichment Status**

#### `GET /api/v1/enrichment/flow/{flow_id}/status`

**Purpose:** Get comprehensive enrichment status for a discovery flow

**Headers:**
```
X-Client-Account-ID: {client_account_id}
X-Engagement-ID: {engagement_id}
X-User-ID: {user_id}
```

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "overall_status": {
    "overall_completion": 78,
    "readiness_for_6r": 82,
    "total_assets": 150,
    "enriched_assets": 117,
    "pending_questions": 3,
    "estimated_completion_minutes": 12
  },
  "phase_status": {
    "classification": {
      "completion_percentage": 95,
      "can_proceed": true,
      "total_assets": 150,
      "enriched_assets": 143,
      "pending_questions": 0,
      "blockers": [],
      "critical_fields_complete": true,
      "last_updated": "2025-07-12T14:30:00Z"
    },
    "business_context": {
      "completion_percentage": 82,
      "can_proceed": false,
      "total_assets": 45,
      "enriched_assets": 37,
      "pending_questions": 2,
      "blockers": ["8 applications missing business value scores"],
      "critical_fields_complete": false,
      "last_updated": "2025-07-12T14:25:00Z"
    },
    "risk_assessment": {
      "completion_percentage": 60,
      "can_proceed": false,
      "total_assets": 150,
      "enriched_assets": 90,
      "pending_questions": 1,
      "blockers": ["Compliance requirements needed for 15 assets"],
      "critical_fields_complete": false,
      "last_updated": "2025-07-12T14:20:00Z"
    }
  },
  "assets_needing_attention": [
    {
      "asset_id": "asset_123",
      "asset_name": "CustomerPaymentAPI",
      "asset_type": "application",
      "missing_fields": ["business_value_score", "compliance_requirements"],
      "enrichment_score": 45,
      "priority": "high"
    }
  ]
}
```

#### `GET /api/v1/enrichment/assets/{flow_id}/needing-enrichment`

**Purpose:** Get assets that need enrichment for a specific phase

**Query Parameters:**
- `phase`: `classification` | `business_context` | `risk_assessment`
- `priority`: `critical` | `high` | `medium` | `low`
- `limit`: Maximum number of assets to return (default: 50)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "phase": "business_context",
  "total_count": 23,
  "assets": [
    {
      "id": "asset_123",
      "name": "CustomerPortal",
      "asset_type": "application",
      "asset_subtype": "web_application",
      "hostname": "portal.company.com",
      "missing_critical_fields": [
        "business_value_score",
        "availability_requirement"
      ],
      "enrichment_score": 55,
      "ai_confidence_score": 0.75,
      "priority": "high",
      "suggested_enrichments": {
        "business_value_score": {
          "suggested_value": 8,
          "confidence": 0.78,
          "reasoning": "Customer-facing portal with payment integration"
        },
        "availability_requirement": {
          "suggested_value": "99.9%",
          "confidence": 0.65,
          "reasoning": "High business value suggests high availability needs"
        }
      },
      "detected_patterns": [
        "customer_facing",
        "payment_integration",
        "web_interface"
      ]
    }
  ]
}
```

## Agent Integration Endpoints

### **Enhanced Agent Execution**

#### `POST /api/v1/unified-discovery/agents/{agent_type}/execute-with-enrichment`

**Purpose:** Execute enhanced agent with enrichment capabilities

**Supported Agent Types:**
- `data-cleansing` (Asset Classification)
- `inventory-building` (Business Context)  
- `dependency-analysis` (Risk Assessment)

**Request Body:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "enrichment_config": {
    "batch_size": 20,
    "timeout_seconds": 60,
    "generate_questions": true,
    "max_questions_per_batch": 7,
    "priority_threshold": "medium"
  },
  "context": {
    "current_phase": "business_context",
    "user_preferences": {
      "question_complexity": "simple",
      "batch_processing": true
    }
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_789",
  "agent_type": "inventory-building",
  "status": "completed",
  "results": {
    "core_results": {
      "assets_processed": 45,
      "inventory_items_created": 180,
      "relationships_identified": 67
    },
    "enrichment_results": {
      "assets_analyzed": 45,
      "enrichments_applied": 23,
      "confidence_scores_calculated": 45,
      "questions_generated": 5,
      "auto_enriched_fields": [
        "business_value_score: 12 assets",
        "application_tier: 8 assets",
        "api_maturity_level: 15 assets"
      ]
    },
    "questions_submitted": 5,
    "estimated_user_time": 3
  },
  "execution_time_ms": 4500,
  "next_recommended_action": "review_pending_questions"
}
```

### **Question Management**

#### `GET /api/v1/agents/questions/pending/{flow_id}`

**Purpose:** Get pending enrichment questions for a flow

**Query Parameters:**
- `page_context`: Filter by page context (`asset-classification`, `business-context`, `risk-assessment`)
- `priority`: Filter by priority level
- `batch_size`: Number of questions to return (default: 7)

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "page_context": "business-context",
  "total_pending": 12,
  "current_batch": [
    {
      "id": "question_456",
      "question_type": "business_value_assessment",
      "priority": "high",
      "title": "Application Business Value",
      "question": "How critical is 'PaymentProcessor' to business operations?",
      "options": [
        "Low (1-3) - Internal tools, development systems",
        "Medium (4-6) - Supporting business operations", 
        "High (7-8) - Important business functions",
        "Critical (9-10) - Revenue generating, customer-facing"
      ],
      "context": {
        "asset_id": "asset_789",
        "application_name": "PaymentProcessor",
        "detected_integrations": ["CreditCardGateway", "BankingAPI"],
        "transaction_indicators": true,
        "ai_suggestion": "Critical (9-10) - Revenue generating, customer-facing",
        "confidence": 0.88,
        "reasoning": "Payment processing application with financial integrations"
      },
      "ui_metadata": {
        "estimated_time_seconds": 15,
        "requires_domain_knowledge": true,
        "skip_allowed": false
      }
    }
  ],
  "batch_metadata": {
    "batch_id": "batch_123",
    "estimated_completion_minutes": 3,
    "progress_after_completion": 85
  }
}
```

#### `POST /api/v1/agents/questions/{question_id}/respond`

**Purpose:** Submit user response to enrichment question

**Request Body:**
```json
{
  "response": {
    "selected_option": "Critical (9-10) - Revenue generating, customer-facing",
    "confidence": "high",
    "additional_notes": "Core payment system for e-commerce platform"
  },
  "user_metadata": {
    "time_taken_seconds": 12,
    "page_context": "business-context",
    "ai_suggestion_followed": true
  }
}
```

**Response:**
```json
{
  "question_id": "question_456",
  "status": "processed",
  "enrichment_applied": {
    "asset_id": "asset_789",
    "field_updates": {
      "business_value_score": 10,
      "availability_requirement": "99.99%"
    },
    "confidence_scores": {
      "business_value_score": 0.95,
      "availability_requirement": 0.75
    }
  },
  "learning_recorded": true,
  "next_questions_available": 4,
  "flow_progression_updated": true
}
```

## Enrichment Analytics Endpoints

### **Progress Tracking**

#### `GET /api/v1/enrichment/analytics/flow/{flow_id}/progress`

**Purpose:** Get detailed progress analytics for enrichment

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress_analytics": {
    "enrichment_velocity": {
      "assets_per_hour": 15,
      "questions_per_hour": 8,
      "estimated_completion": "2025-07-12T16:45:00Z"
    },
    "user_engagement": {
      "response_time_avg_seconds": 18,
      "ai_suggestion_acceptance_rate": 0.78,
      "question_skip_rate": 0.02
    },
    "quality_metrics": {
      "avg_confidence_score": 0.82,
      "manual_corrections": 3,
      "auto_enrichment_success_rate": 0.85
    }
  },
  "phase_breakdown": {
    "classification": {
      "completion_rate": 0.95,
      "avg_confidence": 0.89,
      "user_questions_needed": 2
    },
    "business_context": {
      "completion_rate": 0.67,
      "avg_confidence": 0.73,
      "user_questions_needed": 8
    },
    "risk_assessment": {
      "completion_rate": 0.34,
      "avg_confidence": 0.68,
      "user_questions_needed": 12
    }
  }
}
```

### **Enrichment Patterns**

#### `GET /api/v1/enrichment/patterns/learning-insights`

**Purpose:** Get insights from enrichment pattern learning

**Response:**
```json
{
  "pattern_insights": {
    "most_effective_patterns": [
      {
        "pattern_type": "hostname_analysis",
        "pattern": "app%",
        "success_rate": 0.92,
        "applications": 234
      },
      {
        "pattern_type": "business_name_analysis", 
        "pattern": "%payment%",
        "confidence": 0.88,
        "business_value_accuracy": 0.95
      }
    ],
    "learning_improvements": {
      "confidence_score_improvement": 0.15,
      "question_reduction": 0.23,
      "auto_enrichment_increase": 0.18
    },
    "user_correction_patterns": [
      {
        "field": "business_value_score",
        "ai_suggestion_avg": 7.2,
        "user_correction_avg": 8.1,
        "pattern": "AI tends to under-estimate customer-facing applications"
      }
    ]
  }
}
```

## Flow Progression Control

### **Gating Logic**

#### `GET /api/v1/enrichment/flow/{flow_id}/progression-requirements`

**Purpose:** Check if flow can proceed to next phase

**Query Parameters:**
- `current_phase`: Current phase name
- `target_phase`: Target phase to progress to

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "business_context",
  "target_phase": "risk_assessment",
  "can_proceed": false,
  "requirements": {
    "critical_requirements": [
      {
        "requirement": "All applications must have business_value_score",
        "status": "incomplete",
        "progress": "37/45 (82%)",
        "missing_assets": ["CustomerPortal", "ReportingEngine", "BackupService"]
      },
      {
        "requirement": "High-value applications need availability_requirement",
        "status": "incomplete", 
        "progress": "12/15 (80%)",
        "missing_assets": ["PaymentAPI", "CustomerDB", "OrderSystem"]
      }
    ],
    "optional_requirements": [
      {
        "requirement": "API maturity assessment",
        "status": "partial",
        "progress": "28/45 (62%)",
        "impact": "6R strategy recommendations will be less accurate"
      }
    ]
  },
  "estimated_completion": {
    "required_questions": 8,
    "estimated_minutes": 5,
    "can_auto_enrich": 2
  },
  "progression_blocker_summary": "8 applications need business context before proceeding to risk assessment"
}
```

#### `POST /api/v1/enrichment/flow/{flow_id}/force-progression`

**Purpose:** Force progression despite incomplete enrichment (admin override)

**Request Body:**
```json
{
  "target_phase": "risk_assessment",
  "override_reason": "Business timeline requirement",
  "accept_reduced_accuracy": true,
  "skip_optional_enrichments": true
}
```

**Response:**
```json
{
  "progression_allowed": true,
  "accuracy_impact": {
    "6r_strategy_confidence": 0.72,
    "recommendation_quality": "reduced",
    "missing_enrichments_impact": "Recommendations may be less precise for 8 applications"
  },
  "flow_updated": true
}
```

## Bulk Operations

### **Batch Enrichment**

#### `POST /api/v1/enrichment/assets/batch-enrich`

**Purpose:** Apply bulk enrichment to multiple assets

**Request Body:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "asset_ids": ["asset_123", "asset_456", "asset_789"],
  "enrichment_operations": [
    {
      "field": "business_value_score",
      "value": 7,
      "apply_to_similar": true,
      "similarity_criteria": "asset_type = 'application' AND asset_subtype = 'web_application'"
    },
    {
      "field": "availability_requirement", 
      "value": "99.9%",
      "apply_to_assets": ["asset_123", "asset_456"]
    }
  ],
  "user_metadata": {
    "batch_operation_reason": "Standard web applications baseline",
    "confidence": "high"
  }
}
```

**Response:**
```json
{
  "batch_id": "batch_456",
  "operations_performed": {
    "total_assets_updated": 15,
    "fields_updated": {
      "business_value_score": 12,
      "availability_requirement": 3
    },
    "similar_assets_found": 9,
    "auto_applied_count": 9
  },
  "validation_results": {
    "conflicts": [],
    "warnings": [
      "3 assets already had higher business_value_score - kept existing values"
    ]
  },
  "enrichment_impact": {
    "overall_completion_increase": 12,
    "questions_avoided": 8,
    "progression_unblocked": true
  }
}
```

## Error Handling and Validation

### **Error Response Schema**

```json
{
  "error": {
    "code": "ENRICHMENT_VALIDATION_FAILED",
    "message": "Business value score must be between 1 and 10",
    "details": {
      "field": "business_value_score",
      "provided_value": 15,
      "valid_range": "1-10",
      "asset_id": "asset_123"
    },
    "suggestion": "Please provide a business value score between 1 and 10"
  },
  "request_id": "req_789",
  "timestamp": "2025-07-12T14:30:00Z"
}
```

### **Common Error Codes**

- `ENRICHMENT_TIMEOUT` - Agent enrichment analysis timed out
- `INSUFFICIENT_CONFIDENCE` - AI confidence too low for auto-enrichment
- `MISSING_CRITICAL_CONTEXT` - Required context missing for enrichment
- `VALIDATION_FAILED` - Field validation failed
- `FLOW_PROGRESSION_BLOCKED` - Cannot proceed due to incomplete enrichment
- `QUESTION_BATCH_LIMIT_EXCEEDED` - Too many questions requested
- `PATTERN_LEARNING_FAILED` - Error updating learning patterns

## Integration Examples

### **Frontend Integration Pattern**

```typescript
// React hook for enrichment integration
const useAssetEnrichment = (flowId: string, phase: string) => {
  const [enrichmentStatus, setEnrichmentStatus] = useState<EnrichmentStatus>();
  const [pendingQuestions, setPendingQuestions] = useState<AgentQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const triggerEnrichment = async (agentType: string) => {
    setIsLoading(true);
    try {
      const response = await apiCall(`/api/v1/unified-discovery/agents/${agentType}/execute-with-enrichment`, {
        method: 'POST',
        body: JSON.stringify({
          flow_id: flowId,
          enrichment_config: {
            batch_size: 20,
            generate_questions: true,
            max_questions_per_batch: 7
          },
          context: { current_phase: phase }
        })
      });
      
      // Poll for updated status and questions
      await refreshStatus();
      await refreshQuestions();
      
    } catch (error) {
      console.error('Enrichment failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const submitResponse = async (questionId: string, response: any) => {
    await apiCall(`/api/v1/agents/questions/${questionId}/respond`, {
      method: 'POST',
      body: JSON.stringify({ response })
    });
    
    // Refresh questions after response
    await refreshQuestions();
    await refreshStatus();
  };

  return {
    enrichmentStatus,
    pendingQuestions,
    isLoading,
    triggerEnrichment,
    submitResponse,
    refreshStatus,
    refreshQuestions
  };
};
```

---

*Next: [07_implementation_plan.md](07_implementation_plan.md)*