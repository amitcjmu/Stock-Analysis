"""
Field Mapping Schemas
Enhanced Pydantic models for field mapping management with type safety
Extracted from discovery_flow_schemas.py for better modularity
"""

import math
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


# === FIELD MAPPING ENUMS ===


class FieldMappingStatus(str, Enum):
    """Field mapping status enumeration - matches TypeScript frontend types"""

    SUGGESTED = "suggested"  # AI-suggested mapping (SQLAlchemy default)
    APPROVED = "approved"  # User-approved mapping
    REJECTED = "rejected"  # User-rejected mapping
    PENDING = "pending"  # Awaiting user review
    UNMAPPED = "unmapped"  # No target field assigned


class FieldMappingType(str, Enum):
    """Field mapping type enumeration - matches TypeScript frontend types"""

    AUTO = "auto"  # Automatically detected (default)
    MANUAL = "manual"  # Manually created by user
    SUGGESTED = "suggested"  # AI-suggested mapping
    DIRECT = "direct"  # Direct field mapping (SQLAlchemy default)
    INFERRED = "inferred"  # Inferred from context
    TRANSFORMED = "transformed"  # Requires transformation


class MappingSuggestionSource(str, Enum):
    """Mapping suggestion source - matches SQLAlchemy suggested_by field"""

    AI_MAPPER = "ai_mapper"  # AI-based mapping (SQLAlchemy default)
    USER = "user"  # User-created
    SYSTEM = "system"  # System-generated
    IMPORT = "import"  # From import process


# === FIELD MAPPING SCHEMAS ===


class FieldMappingItem(BaseModel):
    """
    Individual field mapping item with comprehensive validation.

    This model EXACTLY matches the frontend TypeScript FieldMappingItem interface
    for consistent type safety across the stack. All field names use snake_case
    as per Python conventions, with frontend transformation to camelCase.

    Field transformations:
    - source_field (backend) -> sourceField (frontend)
    - target_field (backend) -> targetField (frontend)
    - confidence_score (backend) -> confidenceScore (frontend)
    - mapping_type (backend) -> mappingType (frontend)
    """

    source_field: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Source field name from CSV/import file",
        examples=["customer_name", "device_id", "asset_location"],
    )
    target_field: Optional[str] = Field(
        None,
        max_length=255,
        description="Target field in system schema (null for unmapped fields)",
        examples=["asset.name", "device.identifier", "location.address"],
    )
    confidence_score: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="AI confidence score for the mapping [0.0-1.0]",
        examples=[0.95, 0.73, 0.42],
    )
    mapping_type: FieldMappingType = Field(
        FieldMappingType.AUTO,
        description="Type of mapping indicating how it was created",
    )
    transformation: Optional[str] = Field(
        None,
        max_length=1000,
        description="Transformation rule or logic if field requires processing",
        examples=[
            "UPPER()",
            "DATE_FORMAT('%Y-%m-%d')",
            "CONCAT(first_name, ' ', last_name)",
        ],
    )
    validation_rules: Optional[str] = Field(
        None,
        max_length=1000,
        description="Validation rules for the field mapping",
        examples=["NOT_NULL", "LENGTH > 5", "REGEX('^[A-Z]{3}-\\d{4}$')"],
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def validate_confidence(cls, v):
        """
        Ensure confidence score is JSON-safe and within valid range.

        Handles NaN, Infinity, and out-of-range values by clamping to valid range.
        This prevents JSON serialization errors and ensures consistent validation.
        """
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            return 0.5  # Default to medium confidence
        return max(0.0, min(1.0, float(v)))  # Clamp to [0, 1]

    @field_validator("source_field", mode="before")
    @classmethod
    def validate_source_field(cls, v):
        """
        Validate and sanitize source field name.

        Ensures source field is a non-empty string and filters out test data
        that might contaminate production environments.
        """
        if not v or not isinstance(v, str):
            raise ValueError("source_field must be a non-empty string")

        # Clean the field name
        cleaned = str(v).strip()
        if not cleaned:
            raise ValueError("source_field cannot be empty or whitespace")

        # Filter out test data patterns
        test_patterns = ["Device_", "Device_ID", "Device_Name", "Device_Type"]
        if any(
            cleaned == pattern or cleaned.startswith(pattern)
            for pattern in test_patterns
        ):
            raise ValueError(
                f"Test data field detected: {cleaned}. Test data not allowed in production."
            )

        return cleaned

    @field_validator("target_field", mode="before")
    @classmethod
    def validate_target_field(cls, v):
        """Validate target field name if provided"""
        if v is None:
            return None
        if not isinstance(v, str):
            return None
        cleaned = str(v).strip()
        return cleaned if cleaned and cleaned != "UNMAPPED" else None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "source_field": "customer_name",
                "target_field": "asset.name",
                "confidence_score": 0.87,
                "mapping_type": "auto",
                "transformation": None,
                "validation_rules": "NOT_NULL",
            }
        },
    )


class FieldMappingsResponse(BaseModel):
    """
    Response model for field mappings endpoint.

    This model provides a consistent API response structure for field mappings
    with proper validation and type safety. The response includes the mappings
    data along with metadata for frontend consumption.

    Frontend transformation:
    - flow_id (backend) -> flowId (frontend)
    - field_mappings (backend) -> fieldMappings (frontend)
    """

    success: bool = Field(True, description="Operation success status")
    flow_id: str = Field(
        ...,
        min_length=1,
        description="Discovery flow ID (UUID format)",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    field_mappings: List[FieldMappingItem] = Field(
        default_factory=list, description="List of field mappings for the flow"
    )
    count: int = Field(..., ge=0, description="Total number of field mappings")

    @field_validator("field_mappings", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """Ensure field_mappings is always a list for consistent API responses"""
        if v is None:
            return []
        if not isinstance(v, list):
            return [v]
        return v

    @field_validator("count", mode="before")
    @classmethod
    def validate_count(cls, v, info):
        """Ensure count matches the actual number of field mappings"""
        # Get field_mappings from the values being validated
        field_mappings = info.data.get("field_mappings", [])
        if isinstance(field_mappings, list):
            return len(field_mappings)
        return v if isinstance(v, int) and v >= 0 else 0

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "success": True,
                "flow_id": "123e4567-e89b-12d3-a456-426614174000",
                "field_mappings": [
                    {
                        "source_field": "customer_name",
                        "target_field": "asset.name",
                        "confidence_score": 0.87,
                        "mapping_type": "auto",
                        "transformation": None,
                        "validation_rules": "NOT_NULL",
                    }
                ],
                "count": 1,
            }
        },
    )


# === ADDITIONAL FIELD MAPPING SCHEMAS ===


class FieldMappingStatistics(BaseModel):
    """Statistics for field mappings within a flow"""

    total: int = Field(ge=0, description="Total number of mappings")
    mapped: int = Field(ge=0, description="Number of mapped fields")
    unmapped: int = Field(ge=0, description="Number of unmapped fields")
    approved: int = Field(ge=0, description="Number of approved mappings")
    pending: int = Field(ge=0, description="Number of pending mappings")
    average_confidence: float = Field(
        ge=0.0, le=1.0, description="Average confidence score"
    )


class FieldMappingValidationResult(BaseModel):
    """Validation result for field mappings"""

    mapping_id: str = Field(..., description="Field mapping ID")
    is_valid: bool = Field(..., description="Whether mapping is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Validation confidence")


class BulkFieldMappingRequest(BaseModel):
    """Request for bulk field mapping operations"""

    flow_id: str = Field(..., description="Flow ID for bulk operations")
    operations: List[Dict[str, Any]] = Field(
        ..., description="List of operations to perform"
    )
    continue_on_error: bool = Field(
        False, description="Continue processing on individual errors"
    )


class BulkFieldMappingResponse(BaseModel):
    """Response for bulk field mapping operations"""

    success: bool = Field(..., description="Overall operation success")
    flow_id: str = Field(..., description="Flow ID")
    total_operations: int = Field(ge=0, description="Total operations requested")
    successful_operations: int = Field(ge=0, description="Successful operations")
    failed_operations: int = Field(ge=0, description="Failed operations")
    results: List[FieldMappingValidationResult] = Field(
        default_factory=list, description="Detailed results for each operation"
    )
