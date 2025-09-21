"""
Collection Gaps API Request/Response Models.

These models provide validation and documentation for all collection gaps
Phase 1 endpoints including questionnaires, responses, and vendor catalogs.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# REQUEST MODELS
# =============================================================================


class QuestionnaireGenerationRequest(BaseModel):
    """
    Request model for generating adaptive questionnaires.

    Used with POST /api/v1/collection/flows/{flow_id}/questionnaires/generate
    """

    categories: Optional[List[str]] = Field(
        None,
        description="Optional list of specific categories to generate questions for",
        example=["lifecycle", "resilience", "compliance"],
        max_length=20,
    )
    priority: Optional[Literal["critical", "high", "all"]] = Field(
        "all", description="Priority level for questions to include", example="critical"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categories": ["lifecycle", "resilience"],
                "priority": "critical",
            }
        }
    )


class QuestionnaireResponse(BaseModel):
    """
    Individual questionnaire response item.

    Represents a single answer to a question in the questionnaire.
    """

    question_id: str = Field(
        ...,
        description="Unique identifier for the question (matches field name for simple mapping)",
        example="end_of_life_date",
        min_length=1,
        max_length=100,
    )
    response_value: Union[str, int, float, bool, List[str], Dict[str, Any]] = Field(
        ...,
        description="The answer/value provided for the question",
        example="2025-12-31",
    )
    asset_id: Optional[str] = Field(
        None,
        description="Asset ID if response is asset-specific",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    application_id: Optional[str] = Field(
        None,
        description="Application ID if response is application-specific",
        example="123e4567-e89b-12d3-a456-426614174001",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for complex mappings",
        example={
            "vendor_name": "Microsoft",
            "product_name": "SQL Server",
            "confidence_score": 0.9,
        },
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "end_of_life_date",
                "response_value": "2025-12-31",
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "metadata": {
                    "milestone_type": "end_of_life",
                    "source": "vendor_website",
                },
            }
        }
    )


class ResponsesBatchRequest(BaseModel):
    """
    Request model for bulk response submission.

    Used with POST /api/v1/collection/flows/{flow_id}/responses
    """

    responses: List[QuestionnaireResponse] = Field(
        ...,
        description="List of questionnaire responses to process",
        min_length=1,
        max_length=1000,  # Respects BATCH_CONFIG max_size
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "responses": [
                    {
                        "question_id": "end_of_life_date",
                        "response_value": "2025-12-31",
                        "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                        "metadata": {"milestone_type": "end_of_life"},
                    },
                    {
                        "question_id": "rto_minutes",
                        "response_value": 60,
                        "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                    },
                ]
            }
        }
    )


class CollectionFlowCreateRequest(BaseModel):
    """
    Request model for creating collection flows.

    Used with POST /api/v1/collection/flows
    """

    flow_name: str = Field(
        ...,
        description="Name for the collection flow",
        example="Infrastructure Assessment - Q1 2025",
        min_length=1,
        max_length=255,
    )
    subject: Dict[str, Any] = Field(
        ...,
        description="Subject scope configuration",
        example={
            "scope": "engagement",
            "ids": ["123e4567-e89b-12d3-a456-426614174000"],
            "domain_type": "operations",
        },
    )
    automation_tier: Optional[Literal["tier_1", "tier_2", "tier_3", "tier_4"]] = Field(
        "tier_1", description="Automation tier for the collection flow"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flow_name": "Infrastructure Assessment - Q1 2025",
                "subject": {"scope": "engagement", "domain_type": "operations"},
                "automation_tier": "tier_2",
            }
        }
    )


class MaintenanceWindowRequest(BaseModel):
    """
    Request model for maintenance window operations.
    """

    name: str = Field(
        ...,
        description="Name of the maintenance window",
        example="Monthly Security Patching",
        min_length=1,
        max_length=255,
    )
    start_time: datetime = Field(
        ...,
        description="Start time of the maintenance window",
        example="2025-02-01T02:00:00Z",
    )
    end_time: datetime = Field(
        ...,
        description="End time of the maintenance window",
        example="2025-02-01T06:00:00Z",
    )
    scope_type: Literal["tenant", "application", "asset"] = Field(
        ..., description="Scope of the maintenance window", example="tenant"
    )
    application_id: Optional[str] = Field(
        None, description="Application ID for application-scoped windows"
    )
    asset_id: Optional[str] = Field(
        None, description="Asset ID for asset-scoped windows"
    )
    recurring: bool = Field(False, description="Whether the window is recurring")
    timezone: Optional[str] = Field(
        None, description="Timezone identifier", example="UTC"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Monthly Security Patching",
                "start_time": "2025-02-01T02:00:00Z",
                "end_time": "2025-02-01T06:00:00Z",
                "scope_type": "tenant",
                "recurring": True,
                "timezone": "UTC",
            }
        }
    )


class BlackoutPeriodRequest(BaseModel):
    """
    Request model for blackout period operations.
    """

    start_date: date = Field(
        ..., description="Start date of the blackout period", example="2025-12-20"
    )
    end_date: date = Field(
        ..., description="End date of the blackout period", example="2025-01-05"
    )
    scope_type: Literal["tenant", "application", "asset"] = Field(
        ..., description="Scope of the blackout period", example="tenant"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for the blackout period",
        example="Holiday freeze - no changes allowed",
    )
    application_id: Optional[str] = Field(
        None, description="Application ID for application-scoped blackouts"
    )
    asset_id: Optional[str] = Field(
        None, description="Asset ID for asset-scoped blackouts"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2025-12-20",
                "end_date": "2025-01-05",
                "scope_type": "tenant",
                "reason": "Holiday freeze - no changes allowed",
            }
        }
    )


class VendorProductCreateRequest(BaseModel):
    """
    Request model for creating vendor products.
    """

    vendor_name: str = Field(
        ...,
        description="Vendor name",
        example="Microsoft",
        min_length=1,
        max_length=255,
    )
    product_name: str = Field(
        ...,
        description="Product name",
        example="SQL Server",
        min_length=1,
        max_length=255,
    )
    version_label: Optional[str] = Field(
        None, description="Product version", example="2019 Enterprise", max_length=100
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vendor_name": "Microsoft",
                "product_name": "SQL Server",
                "version_label": "2019 Enterprise",
            }
        }
    )


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class AdaptiveQuestionnaireSection(BaseModel):
    """
    A section within an adaptive questionnaire.
    """

    section_name: str = Field(
        ...,
        description="Name of the questionnaire section",
        example="Product Lifecycle",
    )
    description: Optional[str] = Field(
        None,
        description="Description of the section",
        example="Information about product end-of-life and support dates",
    )
    questions: List[Dict[str, Any]] = Field(
        ..., description="List of questions in this section"
    )
    estimated_time_minutes: Optional[int] = Field(
        None, description="Estimated completion time for this section", example=5
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "section_name": "Product Lifecycle",
                "description": "Information about product end-of-life and support dates",
                "questions": [
                    {
                        "question_id": "end_of_life_date",
                        "question_text": "What is the end-of-life date for this product?",
                        "question_type": "date",
                        "required": True,
                        "validation_rules": {"date_format": "YYYY-MM-DD"},
                    }
                ],
                "estimated_time_minutes": 5,
            }
        }
    )


class AdaptiveQuestionnaire(BaseModel):
    """
    Generated adaptive questionnaire response.
    """

    questionnaire_id: str = Field(
        ...,
        description="Unique identifier for the questionnaire",
        example="quest_123e4567-e89b-12d3-a456-426614174000",
    )
    title: str = Field(
        ...,
        description="Title of the questionnaire",
        example="Infrastructure Data Collection",
    )
    description: Optional[str] = Field(
        None, description="Description of the questionnaire purpose"
    )
    sections: List[AdaptiveQuestionnaireSection] = Field(
        ..., description="List of questionnaire sections"
    )
    estimated_completion_time: int = Field(
        ..., description="Estimated total completion time in minutes", example=15
    )
    target_gaps: List[str] = Field(
        ...,
        description="List of data gaps this questionnaire addresses",
        example=["lifecycle", "resilience"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "questionnaire_id": "quest_123e4567-e89b-12d3-a456-426614174000",
                "title": "Infrastructure Data Collection",
                "sections": [
                    {
                        "section_name": "Product Lifecycle",
                        "questions": [
                            {
                                "question_id": "end_of_life_date",
                                "question_text": "What is the end-of-life date?",
                                "question_type": "date",
                                "required": True,
                            }
                        ],
                    }
                ],
                "estimated_completion_time": 15,
                "target_gaps": ["lifecycle", "resilience"],
            }
        }
    )


class ResponseProcessingResult(BaseModel):
    """
    Result of processing questionnaire responses.
    """

    upserted: int = Field(
        ..., description="Total number of responses processed successfully", example=25
    )
    by_target: Dict[str, int] = Field(
        ...,
        description="Count of updates by target table",
        example={
            "asset_resilience": 5,
            "lifecycle_milestones": 10,
            "tenant_vendor_products": 8,
            "asset_product_links": 2,
        },
    )
    errors: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of errors encountered during processing",
        example=[{"question_id": "invalid_date_field", "error": "Invalid date format"}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "upserted": 25,
                "by_target": {
                    "asset_resilience": 5,
                    "lifecycle_milestones": 10,
                    "tenant_vendor_products": 8,
                },
                "errors": [],
            }
        }
    )


class CollectionGap(BaseModel):
    """
    Individual collection gap item.
    """

    category: str = Field(..., description="Gap category", example="lifecycle")
    field_name: str = Field(
        ..., description="Missing field name", example="end_of_life_date"
    )
    description: str = Field(
        ...,
        description="Human-readable description of the gap",
        example="Product end-of-life date is not available",
    )
    priority: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Priority level of this gap", example="critical"
    )
    affected_assets: Optional[int] = Field(
        None, description="Number of assets affected by this gap", example=25
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "lifecycle",
                "field_name": "end_of_life_date",
                "description": "Product end-of-life date is not available",
                "priority": "critical",
                "affected_assets": 25,
            }
        }
    )


class CollectionGapsResponse(BaseModel):
    """
    Response model for collection gaps analysis.
    """

    critical: List[CollectionGap] = Field(
        ..., description="Critical gaps that must be addressed", example=[]
    )
    high: List[CollectionGap] = Field(..., description="High priority gaps", example=[])
    optional: List[CollectionGap] = Field(
        ..., description="Optional gaps for completeness", example=[]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "critical": [
                    {
                        "category": "lifecycle",
                        "field_name": "end_of_life_date",
                        "description": "Product end-of-life date is not available",
                        "priority": "critical",
                        "affected_assets": 25,
                    }
                ],
                "high": [],
                "optional": [],
            }
        }
    )


class CollectionFlowResponse(BaseModel):
    """
    Response model for collection flow operations.
    """

    id: str = Field(
        ...,
        description="Collection flow ID",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    flow_id: str = Field(
        ...,
        description="Master flow ID",
        example="mfo_123e4567-e89b-12d3-a456-426614174001",
    )
    subject: Dict[str, Any] = Field(
        ...,
        description="Subject configuration",
        example={"scope": "engagement", "domain_type": "operations"},
    )
    collection_config: Dict[str, Any] = Field(
        ...,
        description="Collection configuration settings",
        example={"automation_tier": "tier_2"},
    )
    current_phase: Optional[str] = Field(
        None, description="Current phase of the collection flow", example="gap_analysis"
    )
    progress_percentage: float = Field(
        ..., description="Progress percentage (0.0 to 100.0)", example=45.5
    )
    completeness_by_category: Optional[Dict[str, float]] = Field(
        None,
        description="Data completeness by category",
        example={"lifecycle": 80.0, "resilience": 60.0, "compliance": 90.0},
    )
    pending_gaps: Optional[int] = Field(
        None, description="Number of pending data gaps", example=15
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "flow_id": "mfo_123e4567-e89b-12d3-a456-426614174001",
                "subject": {"scope": "engagement", "domain_type": "operations"},
                "collection_config": {"automation_tier": "tier_2"},
                "current_phase": "gap_analysis",
                "progress_percentage": 45.5,
                "completeness_by_category": {"lifecycle": 80.0, "resilience": 60.0},
                "pending_gaps": 15,
            }
        }
    )


class VendorProductResponse(BaseModel):
    """
    Response model for vendor product operations.
    """

    id: str = Field(
        ...,
        description="Vendor product ID",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    vendor_name: str = Field(..., description="Vendor name", example="Microsoft")
    product_name: str = Field(..., description="Product name", example="SQL Server")
    versions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Available product versions",
        example=[
            {
                "id": "ver_123",
                "version_label": "2019 Enterprise",
                "lifecycle_milestones": [],
            }
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "vendor_name": "Microsoft",
                "product_name": "SQL Server",
                "versions": [{"id": "ver_123", "version_label": "2019 Enterprise"}],
            }
        }
    )


class MaintenanceWindowResponse(BaseModel):
    """
    Response model for maintenance window operations.
    """

    id: str = Field(
        ...,
        description="Maintenance window ID",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    name: str = Field(
        ..., description="Window name", example="Monthly Security Patching"
    )
    start_time: datetime = Field(
        ..., description="Start time", example="2025-02-01T02:00:00Z"
    )
    end_time: datetime = Field(
        ..., description="End time", example="2025-02-01T06:00:00Z"
    )
    scope_type: str = Field(..., description="Scope type", example="tenant")
    is_active: bool = Field(
        ..., description="Whether the window is currently active", example=False
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Monthly Security Patching",
                "start_time": "2025-02-01T02:00:00Z",
                "end_time": "2025-02-01T06:00:00Z",
                "scope_type": "tenant",
                "is_active": False,
            }
        }
    )


class StandardErrorResponse(BaseModel):
    """
    Standard error response for collection gaps endpoints.
    """

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(
        ...,
        description="Error code for programmatic handling",
        example="validation_failed",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="Request validation failed",
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "validation_failed",
                "message": "Request validation failed",
                "details": {
                    "field_errors": {"start_date": "Date must be in the future"}
                },
            }
        }
    )
