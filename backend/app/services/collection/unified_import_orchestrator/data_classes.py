"""
Data classes for unified import orchestrator.
"""

from typing import Any, Dict, List
from uuid import UUID


class FieldMapping:
    """Suggested mapping from CSV column to database field."""

    def __init__(
        self,
        csv_column: str,
        suggested_field: str | None,
        confidence: float,
        suggestions: List[Dict[str, Any]],
    ):
        self.csv_column = csv_column
        self.suggested_field = suggested_field
        self.confidence = confidence
        self.suggestions = suggestions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "csv_column": self.csv_column,
            "suggested_field": self.suggested_field,
            "confidence": self.confidence,
            "suggestions": self.suggestions,
        }


class ImportAnalysis:
    """Analysis result from import file preview."""

    def __init__(
        self,
        file_name: str,
        total_rows: int,
        detected_columns: List[str],
        suggested_mappings: List[FieldMapping],
        unmapped_columns: List[str],
        validation_warnings: List[str],
        import_batch_id: UUID,
    ):
        self.file_name = file_name
        self.total_rows = total_rows
        self.detected_columns = detected_columns
        self.suggested_mappings = suggested_mappings
        self.unmapped_columns = unmapped_columns
        self.validation_warnings = validation_warnings
        self.import_batch_id = import_batch_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_name": self.file_name,
            "total_rows": self.total_rows,
            "detected_columns": self.detected_columns,
            "suggested_mappings": [m.to_dict() for m in self.suggested_mappings],
            "unmapped_columns": self.unmapped_columns,
            "validation_warnings": self.validation_warnings,
            "import_batch_id": str(self.import_batch_id),
        }


class ImportTask:
    """Background import task status."""

    def __init__(
        self,
        id: UUID,
        status: str,
        progress_percent: int,
        current_stage: str,
    ):
        self.id = id
        self.status = status
        self.progress_percent = progress_percent
        self.current_stage = current_stage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "status": self.status,
            "progress_percent": self.progress_percent,
            "current_stage": self.current_stage,
        }
