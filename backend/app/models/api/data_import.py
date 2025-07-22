"""
Data Import API Request/Response Models with Comprehensive Documentation.

These models provide detailed documentation and examples for all data import endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FileMetadataRequest(BaseModel):
    """
    File metadata for import requests.
    
    This contains basic information about the uploaded file.
    """
    
    filename: str = Field(
        ...,
        description="Name of the uploaded file",
        example="servers_inventory.csv",
        min_length=1,
        max_length=255
    )
    size: int = Field(
        ...,
        description="File size in bytes",
        example=102400,
        gt=0,
        le=104857600  # 100MB limit
    )
    type: str = Field(
        ...,
        description="MIME type of the file",
        example="text/csv",
        pattern="^(text/csv|application/vnd\\.ms-excel|application/vnd\\.openxmlformats-officedocument\\.spreadsheetml\\.sheet)$"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "servers_inventory.csv",
                "size": 102400,
                "type": "text/csv"
            }
        }
    )


class UploadContextRequest(BaseModel):
    """
    Context information for data upload.
    
    Provides additional context about the upload including flow tracking and import type.
    """
    
    intended_type: str = Field(
        ...,
        description="Type of data being imported",
        example="servers",
        pattern="^(servers|applications|databases|storage|network|security)$"
    )
    validation_flow_id: Optional[str] = Field(
        None,
        description="ID of the validation flow (if pre-validated)",
        example="val_flow_123e4567-e89b-12d3-a456-426614174000"
    )
    upload_timestamp: str = Field(
        ...,
        description="ISO 8601 formatted timestamp of upload",
        example="2025-01-15T10:30:00Z"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intended_type": "servers",
                "validation_flow_id": "val_flow_123e4567-e89b-12d3-a456-426614174000",
                "upload_timestamp": "2025-01-15T10:30:00Z"
            }
        }
    )


class DataImportRequest(BaseModel):
    """
    Main request model for storing import data.
    
    This is the primary request model for the /store-import endpoint.
    It includes the parsed CSV data, metadata, and context information.
    """
    
    file_data: List[Dict[str, Any]] = Field(
        ...,
        description="Parsed CSV data as a list of dictionaries where each dict represents a row",
        min_items=1,
        max_items=10000,
        example=[
            {
                "server_name": "prod-web-01",
                "ip_address": "10.0.1.10",
                "os": "Ubuntu 20.04",
                "cpu_cores": 8,
                "memory_gb": 16,
                "storage_gb": 500
            },
            {
                "server_name": "prod-db-01",
                "ip_address": "10.0.1.20",
                "os": "RHEL 8",
                "cpu_cores": 16,
                "memory_gb": 64,
                "storage_gb": 2000
            }
        ]
    )
    
    metadata: FileMetadataRequest = Field(
        ...,
        description="File metadata including filename, size, and content type"
    )
    
    upload_context: UploadContextRequest = Field(
        ...,
        description="Upload context including flow ID and import type"
    )
    
    client_id: Optional[str] = Field(
        None,
        description="Client identifier (extracted from auth context)",
        example="client_123"
    )
    
    engagement_id: Optional[str] = Field(
        None,
        description="Engagement identifier (extracted from auth context)",
        example="eng_456"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_data": [
                    {
                        "server_name": "prod-web-01",
                        "ip_address": "10.0.1.10",
                        "os": "Ubuntu 20.04",
                        "cpu_cores": 8,
                        "memory_gb": 16,
                        "storage_gb": 500
                    }
                ],
                "metadata": {
                    "filename": "servers_inventory.csv",
                    "size": 102400,
                    "type": "text/csv"
                },
                "upload_context": {
                    "intended_type": "servers",
                    "upload_timestamp": "2025-01-15T10:30:00Z"
                }
            }
        }
    )


class ImportMetadata(BaseModel):
    """
    Metadata about a stored import.
    
    Returned in responses to provide information about the import status and details.
    """
    
    import_id: str = Field(
        ...,
        description="Unique identifier for the import",
        example="imp_789e0123-4567-89ab-cdef-0123456789ab"
    )
    filename: str = Field(
        ...,
        description="Original filename",
        example="servers_inventory.csv"
    )
    import_type: str = Field(
        ...,
        description="Type of data imported",
        example="servers"
    )
    imported_at: datetime = Field(
        ...,
        description="Timestamp when data was imported",
        example="2025-01-15T10:30:00Z"
    )
    total_records: int = Field(
        ...,
        description="Total number of records imported",
        example=150,
        ge=0
    )
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ...,
        description="Current status of the import",
        example="processing"
    )
    flow_id: Optional[str] = Field(
        None,
        description="Associated discovery flow ID",
        example="disc_flow_456e7890-1234-56ab-cdef-0123456789ab"
    )
    client_account_id: int = Field(
        ...,
        description="Client account identifier",
        example=1
    )
    engagement_id: int = Field(
        ...,
        description="Engagement identifier",
        example=1
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
                "filename": "servers_inventory.csv",
                "import_type": "servers",
                "imported_at": "2025-01-15T10:30:00Z",
                "total_records": 150,
                "status": "processing",
                "flow_id": "disc_flow_456e7890-1234-56ab-cdef-0123456789ab",
                "client_account_id": 1,
                "engagement_id": 1
            }
        }
    )


class DataImportResponse(BaseModel):
    """
    Response model for successful data import.
    
    Returned after successfully storing import data.
    """
    
    success: bool = Field(
        ...,
        description="Whether the import was successful",
        example=True
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        example="Data imported successfully and discovery flow triggered"
    )
    data_import_id: str = Field(
        ...,
        description="Unique identifier for the stored import",
        example="imp_789e0123-4567-89ab-cdef-0123456789ab"
    )
    flow_id: str = Field(
        ...,
        description="Discovery flow ID for tracking progress",
        example="disc_flow_456e7890-1234-56ab-cdef-0123456789ab"
    )
    total_records: int = Field(
        ...,
        description="Number of records imported",
        example=150,
        ge=0
    )
    import_type: str = Field(
        ...,
        description="Type of data imported",
        example="servers"
    )
    next_steps: List[str] = Field(
        ...,
        description="Recommended next actions",
        example=[
            "Monitor discovery flow progress",
            "Review field mappings when available",
            "Validate critical attributes"
        ]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Data imported successfully and discovery flow triggered",
                "data_import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
                "flow_id": "disc_flow_456e7890-1234-56ab-cdef-0123456789ab",
                "total_records": 150,
                "import_type": "servers",
                "next_steps": [
                    "Monitor discovery flow progress",
                    "Review field mappings when available",
                    "Validate critical attributes"
                ]
            }
        }
    )


class DataImportErrorResponse(BaseModel):
    """
    Error response model for data import failures.
    
    Provides detailed error information for troubleshooting.
    """
    
    success: bool = Field(
        False,
        description="Always false for error responses"
    )
    error: str = Field(
        ...,
        description="Error code for programmatic handling",
        example="incomplete_discovery_flow_exists"
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="An incomplete discovery flow already exists for this engagement"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details",
        example={
            "existing_flow": {
                "flow_id": "disc_flow_123",
                "status": "processing",
                "created_at": "2025-01-15T09:00:00Z"
            }
        }
    )
    recommendations: Optional[List[str]] = Field(
        None,
        description="Recommended actions to resolve the error",
        example=[
            "Complete or cancel the existing discovery flow",
            "Review the current flow status",
            "Contact support if the flow is stuck"
        ]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "incomplete_discovery_flow_exists",
                "message": "An incomplete discovery flow already exists for this engagement",
                "details": {
                    "existing_flow": {
                        "flow_id": "disc_flow_123",
                        "status": "processing",
                        "created_at": "2025-01-15T09:00:00Z"
                    }
                },
                "recommendations": [
                    "Complete or cancel the existing discovery flow",
                    "Review the current flow status"
                ]
            }
        }
    )


class ImportStatusResponse(BaseModel):
    """
    Response model for import status queries.
    """
    
    success: bool = Field(
        ...,
        description="Whether the status query was successful"
    )
    import_status: Dict[str, Any] = Field(
        ...,
        description="Current import status details",
        example={
            "import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
            "status": "processing",
            "progress": 75,
            "current_phase": "field_mapping",
            "updated_at": "2025-01-15T10:35:00Z"
        }
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "import_status": {
                    "import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
                    "status": "processing",
                    "progress": 75,
                    "current_phase": "field_mapping",
                    "updated_at": "2025-01-15T10:35:00Z"
                }
            }
        }
    )


class ImportDataResponse(BaseModel):
    """
    Response model for retrieving import data.
    """
    
    success: bool = Field(
        ...,
        description="Whether the data retrieval was successful"
    )
    data: List[Dict[str, Any]] = Field(
        ...,
        description="The imported data records",
        example=[
            {
                "server_name": "prod-web-01",
                "ip_address": "10.0.1.10",
                "os": "Ubuntu 20.04"
            }
        ]
    )
    import_metadata: ImportMetadata = Field(
        ...,
        description="Metadata about the import"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": [
                    {
                        "server_name": "prod-web-01",
                        "ip_address": "10.0.1.10",
                        "os": "Ubuntu 20.04"
                    }
                ],
                "import_metadata": {
                    "import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
                    "filename": "servers_inventory.csv",
                    "import_type": "servers",
                    "imported_at": "2025-01-15T10:30:00Z",
                    "total_records": 150,
                    "status": "completed",
                    "client_account_id": 1,
                    "engagement_id": 1
                }
            }
        }
    )