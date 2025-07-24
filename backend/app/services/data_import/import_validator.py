"""
Import Validator Module

Handles all data validation logic including:
- Data integrity checks
- Schema validation
- Business rule validation
- Conflict detection
- Import format verification
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from app.core.context import RequestContext
from app.core.exceptions import ValidationError as AppValidationError
from app.core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

# Discovery Flow Services
try:
    from app.services.discovery_flow_service import DiscoveryFlowService

    DISCOVERY_FLOW_AVAILABLE = True
except ImportError:
    DISCOVERY_FLOW_AVAILABLE = False
    DiscoveryFlowService = None

logger = get_logger(__name__)


class ImportValidator:
    """
    Validates data import operations and ensures data integrity.
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id

    def validate_csv_headers(self, data: List[Dict[str, Any]]) -> None:
        """
        Validate that CSV column headers are preserved and not corrupted.

        Args:
            data: The parsed CSV data

        Raises:
            AppValidationError: If headers appear to be corrupted
        """
        if not data:
            return

        headers = list(data[0].keys())
        logger.info(f"🔍 Validating CSV headers: {headers}")

        # Check for numeric-only headers (indicates corruption)
        numeric_headers = [h for h in headers if str(h).isdigit()]

        if len(numeric_headers) > len(headers) * 0.5:  # More than 50% numeric
            logger.error(
                f"❌ CSV headers appear corrupted - {len(numeric_headers)} out of {len(headers)} are numeric indices"
            )
            logger.error(f"❌ Corrupted headers: {numeric_headers}")
            logger.error(f"❌ All headers: {headers}")
            raise AppValidationError(
                f"CSV column names appear corrupted (showing as numeric indices: {numeric_headers}). "
                "This suggests an issue with CSV parsing. Please check the uploaded file format."
            )

        # Check for empty or None headers
        empty_headers = [h for h in headers if not h or str(h).strip() == ""]
        if empty_headers:
            logger.warning(f"⚠️ Found empty header fields: {empty_headers}")

        logger.info(f"✅ CSV headers validation passed for {len(headers)} columns")

    async def validate_import_context(self, context: RequestContext) -> None:
        """
        Validate that the import context is complete and valid.

        Args:
            context: The request context containing client and engagement IDs

        Raises:
            AppValidationError: If context validation fails
        """
        if not context.client_account_id or not context.engagement_id:
            raise AppValidationError(
                message="Client account and engagement context required",
                field="context",
                details={
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id,
                },
            )

        if not context.user_id:
            raise AppValidationError(
                message="User ID is required for data import authentication",
                field="user_id",
                details={"user_id": context.user_id, "context": str(context)},
            )

    async def validate_import_id(self, import_validation_id: str) -> uuid.UUID:
        """
        Validate that the import validation ID is a proper UUID.

        Args:
            import_validation_id: The import ID to validate

        Returns:
            uuid.UUID: The validated UUID object

        Raises:
            AppValidationError: If the UUID format is invalid
        """
        try:
            uuid_obj = uuid.UUID(import_validation_id)
            logger.info(f"Validated import ID: {import_validation_id}")
            return uuid_obj
        except ValueError as e:
            logger.error(
                f"Invalid UUID format for import_validation_id: {import_validation_id}"
            )
            raise AppValidationError(
                message=f"Invalid import ID format. Expected UUID, got: {import_validation_id}",
                field="import_validation_id",
                details={"provided_id": import_validation_id, "error": str(e)},
            )

    async def validate_no_incomplete_discovery_flow(
        self, client_account_id: str, engagement_id: str
    ) -> Dict[str, Any]:
        """
        Validate that no incomplete discovery flow exists for this engagement.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            Dict containing validation results and recommendations
        """
        try:
            # Create proper context for flow state manager
            context = RequestContext(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id="system",  # System validation check
            )

            # Use V2 discovery flow service to check for incomplete flows
            if DISCOVERY_FLOW_AVAILABLE:
                discovery_service = DiscoveryFlowService(self.db, context)
                # Get active flows and filter for incomplete ones
                active_flows = await discovery_service.get_active_flows()
                # Filter for incomplete flows (not completed/cancelled)
                incomplete_flows = [
                    flow
                    for flow in active_flows
                    if flow.status not in ["completed", "cancelled", "deleted"]
                ]
            else:
                incomplete_flows = []

            # Filter out flows that are actually empty or have no real progress
            # Only consider flows with actual phases and meaningful progress
            actual_incomplete_flows = []
            for flow in incomplete_flows:
                # Check if this is a real flow with actual progress
                if (
                    flow.get("current_phase")
                    and flow.get("current_phase") not in ["", "initialization"]
                    and (
                        flow.get("progress_percentage", 0) > 0
                        or flow.get("phase_completion", {})
                        and any(flow.get("phase_completion", {}).values())
                    )
                ):
                    actual_incomplete_flows.append(flow)

            # If we found any actual incomplete flows, prevent new import
            if actual_incomplete_flows:
                first_flow = actual_incomplete_flows[
                    0
                ]  # Use the most recent incomplete flow

                logger.info(
                    f"🚫 Blocking data import due to incomplete discovery flow: {first_flow['flow_id']} in phase {first_flow['current_phase']}"
                )

                return {
                    "can_proceed": False,
                    "message": "An incomplete Discovery Flow exists for this engagement. Please complete the existing flow before importing new data.",
                    "existing_flow": {
                        "flow_id": first_flow["flow_id"],
                        "current_phase": first_flow["current_phase"],
                        "progress_percentage": first_flow["progress_percentage"],
                        "status": first_flow["status"],
                        "last_activity": first_flow.get("updated_at"),
                        "next_steps": self._get_next_steps_for_phase(
                            first_flow["current_phase"]
                        ),
                    },
                    "all_incomplete_flows": actual_incomplete_flows,  # For flow management UI
                    "recommendations": [
                        f"Complete the existing Discovery Flow in the '{first_flow['current_phase']}' phase",
                        "Navigate to the appropriate discovery page to continue the flow",
                        "Or use the flow management tools to delete the incomplete flow",
                    ],
                    "show_flow_manager": True,  # Signal frontend to show flow management UI
                }

            # No actual incomplete flows found - allow import
            logger.info(
                f"✅ No incomplete discovery flows found for context {client_account_id}/{engagement_id} - allowing import"
            )
            return {
                "can_proceed": True,
                "message": "No incomplete discovery flows found - proceeding with import",
            }

        except Exception as e:
            logger.warning(f"Failed to validate discovery flow state: {e}")
            # If validation fails, allow import to proceed (fail-open) to prevent blocking users
            return {
                "can_proceed": True,
                "message": f"Discovery flow validation failed - proceeding with import: {e}",
            }

    def _get_next_steps_for_phase(self, current_phase: str) -> List[str]:
        """Get user-friendly next steps for the current phase."""
        phase_steps = {
            "field_mapping": [
                "Navigate to Attribute Mapping page",
                "Review and approve field mappings",
                "Proceed to Data Cleansing",
            ],
            "data_cleansing": [
                "Navigate to Data Cleansing page",
                "Review data quality issues",
                "Apply cleansing recommendations",
                "Proceed to Inventory Building",
            ],
            "inventory_building": [
                "Navigate to Asset Inventory page",
                "Review asset classifications",
                "Confirm inventory accuracy",
                "Proceed to Dependencies",
            ],
            "app_server_dependencies": [
                "Navigate to Dependencies page",
                "Review app-to-server relationships",
                "Confirm hosting mappings",
                "Proceed to App-App Dependencies",
            ],
            "app_app_dependencies": [
                "Navigate to Dependencies page",
                "Review app-to-app integrations",
                "Confirm communication patterns",
                "Proceed to Technical Debt",
            ],
            "technical_debt": [
                "Navigate to Technical Debt page",
                "Review modernization recommendations",
                "Confirm 6R strategies",
                "Complete Discovery Flow",
            ],
        }

        return phase_steps.get(
            current_phase,
            [
                "Navigate to the Discovery Flow",
                "Complete the current phase",
                "Proceed to next phase",
            ],
        )

    async def validate_import_data(
        self, file_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate the imported data for quality and integrity.

        Args:
            file_data: List of data records to validate

        Returns:
            Dict containing validation results and any issues found
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "record_count": len(file_data) if file_data else 0,
            "field_analysis": {},
        }

        if not file_data:
            validation_results["is_valid"] = False
            validation_results["issues"].append("No data records provided")
            return validation_results

        # Analyze field consistency
        if file_data:
            sample_record = file_data[0]
            expected_fields = set(sample_record.keys())

            for idx, record in enumerate(file_data):
                record_fields = set(record.keys())
                if record_fields != expected_fields:
                    validation_results["warnings"].append(
                        f"Record {idx + 1} has inconsistent fields: {record_fields.symmetric_difference(expected_fields)}"
                    )

        # Store field analysis
        if file_data:
            validation_results["field_analysis"] = {
                "total_fields": len(sample_record.keys()),
                "field_names": list(sample_record.keys()),
                "consistent_schema": len(validation_results["warnings"]) == 0,
            }

        logger.info(
            f"✅ Data validation completed: {validation_results['record_count']} records, {len(validation_results['issues'])} issues, {len(validation_results['warnings'])} warnings"
        )
        return validation_results
