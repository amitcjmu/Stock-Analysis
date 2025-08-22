"""
Bulk Data Upload and Processing Service

Handles bulk data entry, CSV/Excel uploads, template-based data entry,
and batch processing for manual collection workflows.

Agent Team B3 - Task B3.2
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from ..collection_flow.data_transformation import DataTransformationService
from ..collection_flow.quality_scoring import QualityAssessmentService

from .bulk_data_models import (
    BulkDataProcessingResult,
    BulkTemplate,
    GridDataEntry,
    ProcessingStatus,
)
from .bulk_data_parser import BulkDataParser
from .bulk_data_validator import BulkDataValidator
from .bulk_template_service import BulkTemplateService

logger = logging.getLogger(__name__)


class BulkDataService:
    """Service for handling bulk data upload and processing operations"""

    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # Maximum number of rows to process
    MAX_ROWS = 1000

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        context: Optional[RequestContext] = None,
    ):
        self.logger = logging.getLogger(__name__)

        # Initialize modular components
        self.parser = BulkDataParser()
        self.validator = BulkDataValidator()
        self.template_service = BulkTemplateService()

        # Initialize optional dependencies
        if db_session and context:
            self.data_transformation_service = DataTransformationService(
                db_session, context
            )
            self.quality_service = QualityAssessmentService(db_session, context)
        else:
            self.data_transformation_service = None
            self.quality_service = None

        self._processing_jobs = {}  # In-memory store for demo purposes

    async def upload_bulk_data(
        self,
        file_content: bytes,
        filename: str,
        template_id: Optional[str] = None,
        mapping_overrides: Optional[Dict[str, str]] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> BulkDataProcessingResult:
        """
        Upload and process bulk data file with validation and transformation.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename with extension
            template_id: Optional template ID for validation
            mapping_overrides: Column name mappings override
            context_metadata: Additional processing context

        Returns:
            BulkDataProcessingResult with processing status and validation issues
        """
        start_time = datetime.utcnow()
        upload_id = str(uuid4())

        try:
            # Validate file
            self.parser.validate_file(file_content, filename)

            # Detect format and parse
            format_type = self.parser.detect_format(filename)
            parsed_data = await self.parser.parse_file_content(
                file_content, format_type
            )

            if len(parsed_data) > self.MAX_ROWS:
                raise ValueError(f"File exceeds maximum row limit of {self.MAX_ROWS}")

            # Get template if specified
            template = None
            if template_id:
                template = await self.template_service.get_template(template_id)

            # Apply template mapping if available
            if template:
                parsed_data = self._apply_template_mapping(
                    parsed_data, template, mapping_overrides
                )

            # Validate data
            validation_issues = await self.validator.validate_bulk_data(
                parsed_data, template.attributes if template else None
            )

            # Transform data
            transformed_data = await self._transform_bulk_data(parsed_data, template)

            # Calculate quality score
            await self._calculate_bulk_quality_score(
                transformed_data, validation_issues
            )

            # Create processing result
            error_count = len(
                [i for i in validation_issues if i.severity.value == "error"]
            )

            result = BulkDataProcessingResult(
                processing_id=upload_id,
                status=(
                    ProcessingStatus.COMPLETED
                    if error_count == 0
                    else ProcessingStatus.PARTIALLY_COMPLETED
                ),
                total_rows=len(parsed_data),
                processed_rows=len(transformed_data),
                failed_rows=error_count,
                validation_issues=validation_issues,
                processed_data=transformed_data,
                created_at=start_time,
                completed_at=datetime.utcnow(),
            )

            # Store result
            self._processing_jobs[upload_id] = result

            return result

        except Exception as e:
            self.logger.error(f"Bulk data processing failed: {e}")

            error_result = BulkDataProcessingResult(
                processing_id=upload_id,
                status=ProcessingStatus.FAILED,
                total_rows=0,
                processed_rows=0,
                failed_rows=0,
                validation_issues=[],
                processed_data=[],
                created_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e),
            )

            self._processing_jobs[upload_id] = error_result
            return error_result

    async def process_grid_data(
        self,
        grid_entries: List[GridDataEntry],
        template_id: Optional[str] = None,
        batch_size: int = 50,
    ) -> BulkDataProcessingResult:
        """Process grid-based data entries in batches"""
        start_time = datetime.utcnow()
        processing_id = str(uuid4())

        try:
            # Convert grid entries to standard format
            data_rows = []
            for entry in grid_entries:
                data_rows.append(entry.data)

            # Get template
            template = None
            if template_id:
                template = await self.template_service.get_template(template_id)

            # Validate
            validation_issues = await self.validator.validate_bulk_data(
                data_rows, template.attributes if template else None
            )

            # Transform
            transformed_data = await self._transform_bulk_data(data_rows, template)

            # Calculate quality
            await self._calculate_bulk_quality_score(
                transformed_data, validation_issues
            )

            result = BulkDataProcessingResult(
                processing_id=processing_id,
                status=ProcessingStatus.COMPLETED,
                total_rows=len(data_rows),
                processed_rows=len(transformed_data),
                failed_rows=len(
                    [i for i in validation_issues if i.severity.value == "error"]
                ),
                validation_issues=validation_issues,
                processed_data=transformed_data,
                created_at=start_time,
                completed_at=datetime.utcnow(),
            )

            self._processing_jobs[processing_id] = result
            return result

        except Exception as e:
            self.logger.error(f"Grid data processing failed: {e}")
            return self._create_error_result(processing_id, start_time, str(e))

    async def generate_bulk_template(
        self,
        template_type: str,
        questionnaire_data: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> BulkTemplate:
        """Generate a bulk data template"""
        return await self.template_service.generate_bulk_template(
            template_type, questionnaire_data, context
        )

    async def export_template_csv(self, template: BulkTemplate) -> str:
        """Export template as CSV"""
        return await self.template_service.export_template_csv(template)

    async def get_processing_status(
        self, processing_id: str
    ) -> Optional[BulkDataProcessingResult]:
        """Get status of a processing job"""
        return self._processing_jobs.get(processing_id)

    async def get_processed_data(self, processing_id: str) -> List[Dict[str, Any]]:
        """Get processed data from a completed job"""
        result = self._processing_jobs.get(processing_id)
        return result.processed_data if result else []

    def _apply_template_mapping(
        self,
        data: List[Dict[str, Any]],
        template: BulkTemplate,
        mapping_overrides: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Apply template column mappings to data"""
        if not template.attributes:
            return data

        # Create mapping from template
        template_mappings = {attr["name"]: attr["name"] for attr in template.attributes}
        if mapping_overrides:
            template_mappings.update(mapping_overrides)

        # Apply mappings
        mapped_data = []
        for row in data:
            mapped_row = {}
            for source_col, target_col in template_mappings.items():
                if source_col in row:
                    mapped_row[target_col] = row[source_col]
            mapped_data.append(mapped_row)

        return mapped_data

    async def _transform_bulk_data(
        self,
        data: List[Dict[str, Any]],
        template: Optional[BulkTemplate] = None,
    ) -> List[Dict[str, Any]]:
        """Transform and normalize bulk data"""
        if not self.data_transformation_service:
            return data  # Return as-is if no transformation service

        transformed_data = []
        for row in data:
            try:
                # Apply transformations if service is available
                transformed_row = (
                    await self.data_transformation_service.transform_data_entry(
                        row, template.attributes if template else None
                    )
                )
                transformed_data.append(transformed_row)
            except Exception as e:
                self.logger.warning(f"Failed to transform row: {e}")
                transformed_data.append(row)  # Keep original on transformation failure

        return transformed_data

    async def _calculate_bulk_quality_score(
        self,
        data: List[Dict[str, Any]],
        validation_issues: List[Any],
    ) -> float:
        """Calculate overall quality score for bulk data"""
        if not data:
            return 0.0

        # Calculate based on validation issues
        total_fields = sum(len(row) for row in data)
        error_fields = len(
            [i for i in validation_issues if i.severity.value == "error"]
        )
        warning_fields = len(
            [i for i in validation_issues if i.severity.value == "warning"]
        )

        if total_fields == 0:
            return 100.0

        # Quality score calculation
        error_penalty = (error_fields / total_fields) * 0.5
        warning_penalty = (warning_fields / total_fields) * 0.2

        quality_score = max(0.0, 100.0 - (error_penalty + warning_penalty) * 100)

        return round(quality_score, 2)

    def _create_error_result(
        self, processing_id: str, start_time: datetime, error_message: str
    ) -> BulkDataProcessingResult:
        """Create error result for failed processing"""
        return BulkDataProcessingResult(
            processing_id=processing_id,
            status=ProcessingStatus.FAILED,
            total_rows=0,
            processed_rows=0,
            failed_rows=0,
            validation_issues=[],
            processed_data=[],
            created_at=start_time,
            completed_at=datetime.utcnow(),
            error_message=error_message,
        )
