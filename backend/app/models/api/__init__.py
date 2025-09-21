"""
API Request/Response Models Package.

This package contains all Pydantic models used for API documentation and validation.
"""

from .data_import import (  # Request Models; Response Models
    DataImportErrorResponse,
    DataImportRequest,
    DataImportResponse,
    FileMetadataRequest,
    ImportDataResponse,
    ImportMetadata,
    ImportStatusResponse,
    UploadContextRequest,
)
from .collection_gaps import (
    # Request Models
    QuestionnaireGenerationRequest,
    QuestionnaireResponse,
    ResponsesBatchRequest,
    CollectionFlowCreateRequest,
    MaintenanceWindowRequest,
    BlackoutPeriodRequest,
    VendorProductCreateRequest,
    # Response Models
    AdaptiveQuestionnaire,
    AdaptiveQuestionnaireSection,
    ResponseProcessingResult,
    CollectionGap,
    CollectionGapsResponse,
    CollectionFlowResponse,
    VendorProductResponse,
    MaintenanceWindowResponse,
    StandardErrorResponse,
)

__all__ = [
    # Data Import Request Models
    "FileMetadataRequest",
    "UploadContextRequest",
    "DataImportRequest",
    # Data Import Response Models
    "ImportMetadata",
    "DataImportResponse",
    "DataImportErrorResponse",
    "ImportStatusResponse",
    "ImportDataResponse",
    # Collection Gaps Request Models
    "QuestionnaireGenerationRequest",
    "QuestionnaireResponse",
    "ResponsesBatchRequest",
    "CollectionFlowCreateRequest",
    "MaintenanceWindowRequest",
    "BlackoutPeriodRequest",
    "VendorProductCreateRequest",
    # Collection Gaps Response Models
    "AdaptiveQuestionnaire",
    "AdaptiveQuestionnaireSection",
    "ResponseProcessingResult",
    "CollectionGap",
    "CollectionGapsResponse",
    "CollectionFlowResponse",
    "VendorProductResponse",
    "MaintenanceWindowResponse",
    "StandardErrorResponse",
]
