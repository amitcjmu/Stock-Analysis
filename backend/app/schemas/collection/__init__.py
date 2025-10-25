"""
Collection Flow Bulk Operations Schemas.
"""

from .bulk_answer_schemas import (
    AnswerInput,
    BulkAnswerPreviewRequest,
    BulkAnswerPreviewResponse,
    BulkAnswerSubmitRequest,
    BulkAnswerSubmitResponse,
    ChunkError,
    ConflictDetail,
    ConflictResolutionStrategy,
)
from .bulk_import_schemas import (
    ConfirmedMapping,
    FieldMappingSuggestion,
    ImportAnalysisResponse,
    ImportExecutionRequest,
    ImportTaskDetailResponse,
    ImportTaskResponse,
    ImportTaskStatusRequest,
)
from .dynamic_questions_schemas import (
    DependencyChangeRequest,
    DependencyChangeResponse,
    DynamicQuestionsRequest,
    DynamicQuestionsResponse,
    QuestionDetail,
)
from .gap_analysis_schemas import (
    GapAnalysisResponse,
    GapDetail,
    ProgressMetrics,
)

__all__ = [
    # Bulk Answer
    "AnswerInput",
    "BulkAnswerPreviewRequest",
    "BulkAnswerPreviewResponse",
    "BulkAnswerSubmitRequest",
    "BulkAnswerSubmitResponse",
    "ChunkError",
    "ConflictDetail",
    "ConflictResolutionStrategy",
    # Dynamic Questions
    "QuestionDetail",
    "DynamicQuestionsRequest",
    "DynamicQuestionsResponse",
    "DependencyChangeRequest",
    "DependencyChangeResponse",
    # Bulk Import
    "FieldMappingSuggestion",
    "ImportAnalysisResponse",
    "ConfirmedMapping",
    "ImportExecutionRequest",
    "ImportTaskResponse",
    "ImportTaskStatusRequest",
    "ImportTaskDetailResponse",
    # Gap Analysis
    "GapAnalysisResponse",
    "GapDetail",
    "ProgressMetrics",
]
