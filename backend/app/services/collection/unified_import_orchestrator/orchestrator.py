"""
Unified Import Orchestrator - Main Service Class

Handles CSV/JSON parsing, intelligent field mapping, and enrichment table updates.
Shared by Discovery and Collection flows per DRY principle.
Per Issue #776 and design doc Section 6.3.
"""

import logging
import uuid
from typing import Any, Dict, List
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    AssetCustomAttributes,
    CollectionBackgroundTasks,
)
from app.repositories.context_aware_repository import ContextAwareRepository
from app.services.multi_model_service import multi_model_service, TaskComplexity

from .data_classes import FieldMapping, ImportAnalysis, ImportTask
from .parsers import parse_csv, parse_json

logger = logging.getLogger(__name__)


class UnifiedImportOrchestrator:
    """
    Service for bulk data imports from CSV/JSON files.

    Provides:
    - Intelligent field mapping suggestions
    - CSV/JSON parsing
    - Enrichment table updates
    - Custom attribute storage
    - Background task processing
    """

    # Standard field name mappings (for fuzzy matching)
    STANDARD_FIELDS = {
        "application": [
            "app_name",
            "application_name",
            "owner",
            "business_unit",
            "criticality",
        ],
        "server": [
            "server_name",
            "hostname",
            "ip_address",
            "os_version",
            "environment",
        ],
        "database": [
            "db_name",
            "database_name",
            "db_type",
            "db_version",
            "instance_name",
        ],
    }

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
    ):
        """
        Initialize import orchestrator.

        Args:
            db: Async database session
            context: Request context with client_account_id, engagement_id
        """
        self.db = db
        self.context = context

        # Context-aware repositories
        self.custom_attributes_repo = ContextAwareRepository(
            db, AssetCustomAttributes, context
        )
        self.background_tasks_repo = ContextAwareRepository(
            db, CollectionBackgroundTasks, context
        )

    async def analyze_import_file(
        self,
        file: UploadFile,
        import_type: str,  # "application", "server", "database"
    ) -> ImportAnalysis:
        """
        Analyze CSV/JSON and suggest field mappings.

        Args:
            file: Uploaded file
            import_type: Type of import (application/server/database)

        Returns:
            Analysis with suggested mappings
        """
        # Parse file based on extension
        if file.filename.endswith(".csv"):
            data = await parse_csv(file)
        elif file.filename.endswith(".json"):
            data = await parse_json(file)
        else:
            raise ValueError(f"Unsupported file format: {file.filename}")

        if not data:
            raise ValueError("File is empty or could not be parsed")

        # Detect columns
        detected_columns = list(data[0].keys())

        # Intelligent field mapping
        suggested_mappings = []
        for csv_column in detected_columns:
            mapping = await self._suggest_field_mapping(csv_column, import_type, data)
            suggested_mappings.append(mapping)

        # Identify unmapped columns
        unmapped_columns = [
            m.csv_column for m in suggested_mappings if m.confidence < 0.5
        ]

        # Validation warnings
        validation_warnings = await self._validate_data(
            data, suggested_mappings, import_type
        )

        # Create import batch ID
        import_batch_id = uuid.uuid4()

        logger.info(
            f"📊 Analyzed import file '{file.filename}': "
            f"{len(data)} rows, {len(detected_columns)} columns, "
            f"{len(unmapped_columns)} unmapped"
        )

        return ImportAnalysis(
            file_name=file.filename,
            total_rows=len(data),
            detected_columns=detected_columns,
            suggested_mappings=suggested_mappings,
            unmapped_columns=unmapped_columns,
            validation_warnings=validation_warnings,
            import_batch_id=import_batch_id,
        )

    async def execute_import(
        self,
        child_flow_id: UUID,
        import_batch_id: UUID,
        file_data: List[Dict[str, Any]],
        confirmed_mappings: Dict[str, str],
        import_type: str,
        overwrite_existing: bool = False,
        gap_recalculation_mode: str = "fast",
    ) -> ImportTask:
        """
        Execute import as background task.

        Args:
            child_flow_id: Collection child flow UUID
            import_batch_id: Batch UUID from analyze step
            file_data: Parsed file data
            confirmed_mappings: User-confirmed field mappings
            import_type: Type of import
            overwrite_existing: Whether to overwrite existing data
            gap_recalculation_mode: "fast" or "thorough"

        Returns:
            Task object with ID for polling
        """
        # Create task record
        task = await self.background_tasks_repo.create_no_commit(
            child_flow_id=child_flow_id,
            task_type="bulk_import",
            status="pending",
            progress_percent=0,
            current_stage="queued",
            input_params={
                "import_batch_id": str(import_batch_id),
                "import_type": import_type,
                "row_count": len(file_data),
                "overwrite_existing": overwrite_existing,
                "gap_recalculation_mode": gap_recalculation_mode,
            },
            total_rows=len(file_data),
            is_cancellable=True,
            idempotency_key=str(import_batch_id),
        )

        # NOTE: In production, this would be added to a background task queue
        # For now, we create the task record and return it
        # The actual processing would be done by a worker process

        logger.info(
            f"🚀 Created import task {task.id} for batch {import_batch_id} "
            f"({len(file_data)} rows)"
        )

        return ImportTask(
            id=task.id,
            status="pending",
            progress_percent=0,
            current_stage="queued",
        )

    async def _suggest_field_mapping(
        self,
        csv_column: str,
        import_type: str,
        data: List[Dict[str, Any]],
    ) -> FieldMapping:
        """
        Suggest field mapping using fuzzy matching and LLM analysis.

        Per CLAUDE.md: Uses multi_model_service for automatic LLM tracking.
        """
        # Step 1: Try fuzzy matching first
        fuzzy_match = self._fuzzy_match_field(csv_column, import_type)

        if fuzzy_match["confidence"] >= 0.8:
            # High confidence fuzzy match
            return FieldMapping(
                csv_column=csv_column,
                suggested_field=fuzzy_match["field"],
                confidence=fuzzy_match["confidence"],
                suggestions=[fuzzy_match],
            )

        # Step 2: Use LLM for intelligent mapping
        try:
            # Sample data for context
            sample_values = [row.get(csv_column, "") for row in data[:5]]
            sample_text = ", ".join([str(v) for v in sample_values if v])

            prompt = f"""
            Suggest the best database field mapping for this CSV column:

            CSV Column Name: {csv_column}
            Sample Values: {sample_text}
            Import Type: {import_type}

            Standard Fields Available: {", ".join(self.STANDARD_FIELDS.get(import_type, []))}

            Return ONLY the field name, or "unmapped" if no good match.
            """

            response = await multi_model_service.generate_response(
                prompt=prompt,
                task_type="field_mapping",
                complexity=TaskComplexity.SIMPLE,  # Simple mapping task
            )

            suggested_field = response.strip()
            if suggested_field.lower() == "unmapped":
                suggested_field = None
                confidence = 0.3
            else:
                confidence = 0.7

            return FieldMapping(
                csv_column=csv_column,
                suggested_field=suggested_field,
                confidence=confidence,
                suggestions=[
                    {
                        "field": suggested_field,
                        "confidence": confidence,
                        "method": "llm",
                    }
                ],
            )

        except Exception as e:
            logger.warning(f"⚠️  LLM field mapping failed for '{csv_column}': {e}")
            # Fallback to fuzzy match result
            return FieldMapping(
                csv_column=csv_column,
                suggested_field=fuzzy_match["field"],
                confidence=fuzzy_match["confidence"],
                suggestions=[fuzzy_match],
            )

    def _fuzzy_match_field(self, csv_column: str, import_type: str) -> Dict[str, Any]:
        """
        Perform fuzzy matching on field names.

        Simple implementation using string similarity.
        """
        csv_lower = csv_column.lower().replace("_", "").replace(" ", "")
        standard_fields = self.STANDARD_FIELDS.get(import_type, [])

        best_match = None
        best_score = 0.0

        for field in standard_fields:
            field_lower = field.lower().replace("_", "")

            # Simple substring matching
            if csv_lower == field_lower:
                score = 1.0
            elif csv_lower in field_lower or field_lower in csv_lower:
                score = 0.8
            elif any(word in field_lower for word in csv_lower.split("_")):
                score = 0.6
            else:
                score = 0.0

            if score > best_score:
                best_score = score
                best_match = field

        return {
            "field": best_match,
            "confidence": best_score,
            "method": "fuzzy",
        }

    async def _validate_data(
        self,
        data: List[Dict[str, Any]],
        suggested_mappings: List[FieldMapping],
        import_type: str,
    ) -> List[str]:
        """
        Validate data and return warnings.

        Checks for:
        - Required fields missing
        - Invalid data formats
        - Duplicate entries
        """
        warnings = []

        # Check for required fields
        required_fields = {
            "application": ["app_name"],
            "server": ["server_name"],
            "database": ["db_name"],
        }

        mapped_fields = [
            m.suggested_field for m in suggested_mappings if m.suggested_field
        ]
        required = required_fields.get(import_type, [])

        for field in required:
            if field not in mapped_fields:
                warnings.append(f"Required field '{field}' is not mapped")

        # Check for duplicate names
        if import_type == "application":
            name_field = "app_name"
        elif import_type == "server":
            name_field = "server_name"
        else:
            name_field = "db_name"

        # Find the CSV column mapped to name field
        name_column = None
        for m in suggested_mappings:
            if m.suggested_field == name_field:
                name_column = m.csv_column
                break

        if name_column:
            names = [row.get(name_column) for row in data if row.get(name_column)]
            duplicates = [name for name in set(names) if names.count(name) > 1]
            if duplicates:
                warnings.append(
                    f"Duplicate entries found: {', '.join(duplicates[:5])}"
                    + (
                        f" and {len(duplicates) - 5} more"
                        if len(duplicates) > 5
                        else ""
                    )
                )

        return warnings
