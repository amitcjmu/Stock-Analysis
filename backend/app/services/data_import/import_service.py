"""
Data Import Service Module

Consolidated service for handling data imports and triggering discovery flows.
This service replaces FlowTriggerService and directly orchestrates the import process.
"""

import json
import traceback
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError, DataImportError
from app.core.logging import get_logger
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.discovery_flow_service import DiscoveryFlowService
from app.services.data_import.storage_manager import ImportStorageManager
from app.models.data_import import DataImport

logger = get_logger(__name__)


def convert_uuids_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings for JSON serialization.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return type(obj)(convert_uuids_to_str(item) for item in obj)
    return obj


class DataImportService:
    """
    Orchestrates the data import process, including storage and flow creation.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.storage_manager = ImportStorageManager(db, context.client_account_id)

    def _detect_columns_from_data(self, parsed_data: Any, sample_size: int = 5) -> list:
        """
        Extract column names from parsed data using multi-row sampling for robustness.

        Args:
            parsed_data: The parsed JSON data structure
            sample_size: Number of rows to sample for column detection

        Returns:
            List of detected column names, sorted for consistency
        """
        try:
            detected_columns = []
            # Default to at least 1 row; refine per-branch using real lengths
            actual_sample_size = 1

            if isinstance(parsed_data, list) and parsed_data:
                # Sample multiple rows for more robust column detection
                actual_sample_size = min(sample_size, len(parsed_data))
                rows_to_sample = parsed_data[:actual_sample_size]
                column_set = set()

                for row in rows_to_sample:
                    if isinstance(row, dict):
                        for k in row.keys():
                            # SECURITY FIX: Add null check before string operations
                            if k is not None and str(k).strip():
                                column_set.add(str(k).strip())

                detected_columns = sorted(list(column_set))  # Sort for consistency

            elif isinstance(parsed_data, dict) and "data" in parsed_data:
                data_list = parsed_data.get("data", [])
                if isinstance(data_list, list) and data_list:
                    # Sample multiple rows for more robust column detection
                    actual_sample_size = min(sample_size, len(data_list))
                    rows_to_sample = data_list[:actual_sample_size]
                    column_set = set()

                    for row in rows_to_sample:
                        if isinstance(row, dict):
                            for k in row.keys():
                                # SECURITY FIX: Add null check before string operations
                                if k is not None and str(k).strip():
                                    column_set.add(str(k).strip())

                    detected_columns = sorted(list(column_set))  # Sort for consistency

            if detected_columns:
                logger.info(
                    f"🔍 Detected {len(detected_columns)} columns from {actual_sample_size} sample row(s)"
                )

            return detected_columns

        except Exception as e:
            # Non-fatal; return empty list if parsing fails
            # SECURITY FIX: Use secure formatting for column detection errors
            from app.core.security.secure_logging import safe_log_format

            logger.warning(
                safe_log_format(
                    "Column detection failed: {error_type}",
                    error_type=type(e).__name__,
                )
            )
            return []

    def _calculate_record_count(self, data: Any) -> int:
        """
        Calculate the actual number of records in data, handling nested structures.

        Args:
            data: Parsed JSON data that could be a list or dict with nested data

        Returns:
            int: The actual number of records
        """
        try:
            # SECURITY FIX: Handle generators/iterables properly for counting
            if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
                # Convert generator to list for counting, but be memory conscious
                try:
                    if hasattr(data, "__len__"):
                        return len(data)
                    else:
                        # For generators, count without consuming all memory
                        count = sum(1 for _ in data)
                        return count
                except Exception:
                    # Fallback if iteration fails
                    return 0

            # If data is already a list, return its length
            if isinstance(data, list):
                return len(data)

            # If data is a dict, check for common nested structures
            if isinstance(data, dict):
                # Check for {"data": [...]} structure
                if "data" in data and isinstance(data["data"], list):
                    return len(data["data"])

                # Check for other possible keys that might contain the records
                for key in ["records", "items", "results", "rows"]:
                    if key in data and isinstance(data[key], list):
                        return len(data[key])

                # If it's a dict but no recognizable structure, treat as single record
                return 1

            # For any other type, count as 1 record if not None/empty
            if data is not None and data != "":
                return 1

            # Empty or None data
            return 0

        except Exception as e:
            # SECURITY FIX: Use secure formatting for errors - log exception type only
            from app.core.security.secure_logging import safe_log_format

            logger.error(
                safe_log_format(
                    "Error calculating record count: {error_type}",
                    error_type=type(e).__name__,
                )
            )
            # Fallback: assume no records
            return 0

    async def process_import_and_trigger_flow(
        self,
        file_content: bytes,
        filename: str,
        file_content_type: str,
        import_type: str,
    ) -> DataImport:
        """
        Stores imported data and triggers the discovery flow within a single transaction.

        Args:
            file_content: The raw byte content of the file.
            filename: The name of the imported file.
            file_content_type: The MIME type of the file.
            import_type: The type of import (e.g., 'cmdb', 'applications').

        Returns:
            The created DataImport record.
        """
        try:
            logger.info(f"🚀 Starting data import process for file: {filename}")

            # 1. Store the imported file and create DataImport record
            logger.info(f"🔍 DEBUG: Context user_id = {self.context.user_id}")
            logger.info(
                f"🔍 DEBUG: Context engagement_id = {self.context.engagement_id}"
            )
            data_import = await self.storage_manager.store_import_data(
                file_content=file_content,
                filename=filename,
                file_content_type=file_content_type,
                import_type=import_type,
                status="processing",
                engagement_id=self.context.engagement_id,
                imported_by=self.context.user_id,
            )
            logger.info(f"🗳️ Data import record created: {data_import.id}")

            # Parse the JSON data directly since it's already available
            parsed_data = json.loads(file_content.decode("utf-8"))

            # Calculate actual record count, handling nested structures
            actual_record_count = self._calculate_record_count(parsed_data)

            file_data = {
                "data": parsed_data,
                "import_metadata": {
                    "import_id": str(data_import.id),
                    "filename": filename,
                    "import_type": import_type,
                    "total_records": actual_record_count,
                },
                "success": True,
            }

            # 2. Trigger the Discovery Flow
            logger.info(
                f"🔍 Triggering Discovery Flow for data import: {data_import.id}"
            )
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            configuration = {
                "source": "data_import",
                "import_id": str(data_import.id),
                "filename": filename,
                "import_timestamp": datetime.utcnow().isoformat(),
            }
            initial_state = {
                "raw_data": parsed_data,  # ✅ Pass actual CSV data, not metadata wrapper
                "data_import_id": str(data_import.id),
            }

            try:
                flow_result = await orchestrator.create_flow(
                    flow_type="discovery",
                    flow_name=f"Discovery Import {data_import.id}",
                    configuration=convert_uuids_to_str(configuration),
                    initial_state=convert_uuids_to_str(initial_state),
                    atomic=True,  # Ensure it runs within the existing transaction
                )

                logger.info(
                    f"🔍 Flow creation result: {flow_result}, type: {type(flow_result)}"
                )

                master_flow_id = (
                    flow_result[0] if isinstance(flow_result, tuple) else None
                )
                if not master_flow_id:
                    logger.error(
                        f"❌ Master flow creation returned None or invalid result: {flow_result}"
                    )
                    raise FlowError(
                        "Failed to create master flow - no flow ID returned"
                    )
            except Exception as flow_error:
                # SECURITY FIX: Use secure formatting for flow creation errors
                from app.core.security.secure_logging import safe_log_format

                logger.error(
                    safe_log_format(
                        "❌ Exception during flow creation: {error_type}",
                        error_type=type(flow_error).__name__,
                    ),
                    exc_info=True,
                )
                raise FlowError(
                    f"Failed to create master flow: {type(flow_error).__name__}"
                )

            logger.info(f"✅ Master flow created successfully: {master_flow_id}")

            # 3. Create the linked DiscoveryFlow record
            discovery_service = DiscoveryFlowService(self.db, self.context)
            metadata = {
                "source": "data_import",
                "import_id": str(data_import.id),
                "master_flow_id": master_flow_id,
                "import_timestamp": datetime.utcnow().isoformat(),
            }

            # Derive detected columns early to remove timing/race conditions
            # ROBUSTNESS FIX: Enhanced column detection with null checks and multi-row sampling
            detected_columns = self._detect_columns_from_data(
                parsed_data, sample_size=5
            )
            if detected_columns:
                metadata["detected_columns"] = detected_columns
            await discovery_service.create_discovery_flow(
                flow_id=str(master_flow_id),
                # Store the actual list of records in raw_data for downstream phases
                # SECURITY FIX: Use safe dictionary access with fallback
                raw_data=file_data.get("data", []),
                metadata=convert_uuids_to_str(metadata),
                data_import_id=str(data_import.id),
                user_id=str(self.context.user_id),
                master_flow_id=str(master_flow_id),
            )
            logger.info(
                f"✅ Discovery flow child record created and linked: {master_flow_id}"
            )

            # 4. Update the DataImport record with the flow_id
            await self.storage_manager.update_import_with_flow_id(
                data_import_id=data_import.id, flow_id=master_flow_id
            )
            logger.info(
                f"✅ Linked flow {master_flow_id} to data import {data_import.id}"
            )

            # IMPORTANT: Set the master_flow_id on the in-memory object
            # The update_import_with_flow_id only updates the database record,
            # not the in-memory object, so we need to set it here for the response
            data_import.master_flow_id = master_flow_id

            # Store flow execution data for later background processing
            # NOTE: Background execution must be started AFTER transaction commits
            # to avoid race conditions where the flow isn't visible to status queries
            data_import.flow_execution_data = {
                "flow_id": str(master_flow_id),
                "file_data": file_data.get("data", []),
            }
            logger.info(
                f"📦 Prepared background flow execution data for {master_flow_id}"
            )

            # The transaction will be committed by the calling service (e.g., in transaction_manager)

            return data_import

        except Exception as e:
            # SECURITY FIX: Use secure formatting for final error logging
            from app.core.security.secure_logging import safe_log_format

            logger.error(
                safe_log_format(
                    "❌ Data import and flow trigger failed: {error_type}",
                    error_type=type(e).__name__,
                )
            )
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # The exception will be caught by the transaction manager, which will rollback.
            raise DataImportError(
                f"Failed to process import and trigger flow: {type(e).__name__}"
            )
