"""
Response mapping service for collection gaps.

This service handles the mapping of questionnaire responses to appropriate
database tables using the QUESTION_TO_TABLE_MAPPING registry.

Modularized to maintain clean separation of concerns while preserving
backward compatibility with existing imports.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.env_flags import is_truthy_env

from .base import QUESTION_TO_TABLE_MAPPING, BATCH_CONFIG, BaseResponseMapper
from .vendor_mappers import VendorProductMappers
from .resilience_mappers import ResilienceMappers
from .operational_mappers import OperationalMappers

logger = logging.getLogger(__name__)


class ResponseMappingService(BaseResponseMapper):
    """Service for mapping questionnaire responses to database tables."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        """Initialize response mapping service with database session and tenant context."""
        super().__init__(db, client_account_id, engagement_id)

        # Initialize mapper components using composition instead of inheritance
        self.vendor_mappers = VendorProductMappers(db, client_account_id, engagement_id)
        self.resilience_mappers = ResilienceMappers(
            db, client_account_id, engagement_id
        )
        self.operational_mappers = OperationalMappers(
            db, client_account_id, engagement_id
        )

        # Initialize feature flags
        self.dry_run_mode = is_truthy_env("RESPONSE_MAPPING_DRY_RUN", default=False)
        self.validation_enabled = is_truthy_env(
            "RESPONSE_MAPPING_VALIDATION", default=True
        )

        logger.info(
            f"ResponseMappingService initialized for client {client_account_id}, "
            f"engagement {engagement_id} "
            f"(dry_run: {self.dry_run_mode}, validation: {self.validation_enabled})"
        )

    async def process_responses_batch(
        self, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a batch of questionnaire responses.

        Args:
            responses: List of response dictionaries to process

        Returns:
            Dictionary with processing results including:
            - upserted: Total number of records created/updated
            - by_target: Breakdown by target table
            - errors: List of any processing errors
        """
        if not responses:
            return {"upserted": 0, "by_target": {}, "errors": []}

        batch_size = min(len(responses), BATCH_CONFIG["max_size"])
        logger.info(
            f"🔄 Processing batch of {len(responses)} responses (batch_size: {batch_size})"
        )

        results = {"upserted": 0, "by_target": {}, "errors": []}

        for i, response in enumerate(responses):
            try:
                # Process single response
                single_result = await self._process_single_response(response)

                # Aggregate results
                results["upserted"] += len(single_result)

                # Track by target table/handler
                for record_id in single_result:
                    table_name = record_id.split(":")[0]
                    if table_name not in results["by_target"]:
                        results["by_target"][table_name] = 0
                    results["by_target"][table_name] += 1

                if (i + 1) % 100 == 0:
                    logger.info(f"   Processed {i + 1}/{len(responses)} responses...")

            except Exception as e:
                error_msg = f"Failed to process response {i}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results["errors"].append(error_msg)

        logger.info(
            f"✅ Batch processing complete: {results['upserted']} records upserted, "
            f"{len(results['errors'])} errors"
        )
        return results

    async def _process_single_response(self, response: Dict[str, Any]) -> List[str]:
        """
        Process a single questionnaire response.

        Args:
            response: Response dictionary to process

        Returns:
            List of record identifiers that were created/updated
        """
        question_type = response.get("question_type")
        if not question_type:
            raise ValueError("Missing question_type in response")

        mapping_config = QUESTION_TO_TABLE_MAPPING.get(question_type)
        if not mapping_config:
            raise ValueError(
                f"No mapping configuration found for question_type: {question_type}"
            )

        handler_name = mapping_config["handler"]

        # Get the handler method
        handler_method = getattr(self, handler_name, None)
        if not handler_method:
            raise ValueError(f"Handler method '{handler_name}' not found")

        if self.dry_run_mode:
            logger.info(
                f"🔍 DRY RUN: Would call {handler_name} with response: {response}"
            )
            return [f"dry_run:{handler_name}"]

        # Call the appropriate handler
        return await handler_method(response)

    # Delegation methods for vendor/product operations
    async def map_vendor_product(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to vendor mappers."""
        return await self.vendor_mappers.map_vendor_product(response)

    async def map_product_version(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to vendor mappers."""
        return await self.vendor_mappers.map_product_version(response)

    async def map_lifecycle_dates(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to vendor mappers."""
        return await self.vendor_mappers.map_lifecycle_dates(response)

    # Delegation methods for resilience operations
    async def map_resilience_metrics(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to resilience mappers."""
        return await self.resilience_mappers.map_resilience_metrics(response)

    async def map_compliance_flags(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to resilience mappers."""
        return await self.resilience_mappers.map_compliance_flags(response)

    async def map_license(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to resilience mappers."""
        return await self.resilience_mappers.map_license(response)

    async def map_vulnerability(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to resilience mappers."""
        return await self.resilience_mappers.map_vulnerability(response)

    # Delegation methods for operational operations
    async def map_maintenance_window(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to operational mappers."""
        return await self.operational_mappers.map_maintenance_window(response)

    async def map_blackout_period(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to operational mappers."""
        return await self.operational_mappers.map_blackout_period(response)

    async def map_dependencies(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to operational mappers."""
        return await self.operational_mappers.map_dependencies(response)

    async def map_exception(self, response: Dict[str, Any]) -> List[str]:
        """Delegate to operational mappers."""
        return await self.operational_mappers.map_exception(response)

    async def _handle_direct_field_mapping(
        self, response: Dict[str, Any], field_name: str, model_field: str
    ) -> str:
        """
        Handle direct field mapping between response and model.

        Args:
            response: Response data dictionary
            field_name: Field name in the response
            model_field: Corresponding field in the database model

        Returns:
            String identifier of created/updated record
        """
        # Implementation depends on specific use case
        # This is a placeholder for direct field mapping logic
        logger.info(f"Direct field mapping: {field_name} -> {model_field}")
        return f"mapped_{field_name}_to_{model_field}"


# Backward compatibility exports
__all__ = [
    "ResponseMappingService",
    "QUESTION_TO_TABLE_MAPPING",
    "BATCH_CONFIG",
]
