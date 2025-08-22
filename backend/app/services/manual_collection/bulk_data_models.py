"""
Bulk Data Models

Data models and enums for bulk data processing.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class BulkDataFormat(str, Enum):
    """Supported bulk data formats"""

    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    TSV = "tsv"


class ProcessingStatus(str, Enum):
    """Bulk processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class ValidationSeverity(str, Enum):
    """Validation issue severity levels"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class BulkDataValidationIssue:
    """Represents a validation issue in bulk data"""

    row_index: int
    column: str
    message: str
    severity: ValidationSeverity
    suggested_value: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class BulkDataProcessingResult:
    """Result of bulk data processing"""

    processing_id: str
    status: ProcessingStatus
    total_rows: int
    processed_rows: int
    failed_rows: int
    validation_issues: List[BulkDataValidationIssue]
    processed_data: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class BulkTemplate:
    """Template for bulk data entry"""

    template_id: str
    name: str
    description: str
    attributes: List[Dict[str, Any]]
    validation_rules: Dict[str, Any]
    example_data: List[Dict[str, Any]]
    created_at: datetime


@dataclass
class GridDataEntry:
    """Single entry in grid-based data input"""

    row_id: str
    data: Dict[str, Any]
    validation_status: str
    created_at: datetime
