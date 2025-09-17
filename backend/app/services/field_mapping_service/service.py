"""
Main field mapping service implementation.

This module contains the FieldMappingService class which orchestrates
all field mapping operations and maintains session management.
"""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.base_service import ServiceBase

from .base import (
    MappingAnalysis,
    MappingRule,
    BASE_MAPPINGS,
    REQUIRED_FIELDS,
)
from .business_logic import FieldMappingBusinessLogic
from .business_logic_extended import get_field_mappings, validate_mapping
from .mappers import FieldMappingAnalyzer
from .repository import FieldMappingRepository


class FieldMappingService(ServiceBase):
    """
    Service for managing field mappings in the discovery flow.

    This service:
    - Manages field mapping rules and transformations
    - Learns from user feedback and AI analysis
    - Provides mapping suggestions and validation
    - Maintains multi-tenant context for mappings
    - Never commits or closes the database session
    """

    # Base mappings for common field variations
    BASE_MAPPINGS = BASE_MAPPINGS

    # Required fields for different asset types
    REQUIRED_FIELDS = REQUIRED_FIELDS

    def __init__(self, session: AsyncSession, context: RequestContext):
        """
        Initialize FieldMappingService.

        Args:
            session: Database session from orchestrator
            context: Request context with tenant information
        """
        super().__init__(session, context)

        # Initialize repository
        self.repository = FieldMappingRepository(session, context)

        # Initialize mapping caches
        self._learned_mappings_cache: Optional[Dict[str, List[MappingRule]]] = None
        self._negative_mappings_cache: Set[tuple] = set()

        # Initialize analyzer
        self._analyzer = FieldMappingAnalyzer(
            learned_mappings_cache=self._learned_mappings_cache,
            negative_mappings_cache=self._negative_mappings_cache,
        )

        # Initialize business logic
        self.business_logic = FieldMappingBusinessLogic(
            repository=self.repository,
            analyzer=self._analyzer,
            context=context,
            service_base=self,
        )

        self.logger.debug(
            f"Initialized FieldMappingService for client {context.client_account_id}"
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for FieldMappingService.

        Returns:
            Health status and metrics
        """
        try:
            # Count mappings in database
            mapping_count = await self.repository.get_mapping_count()

            return {
                "status": "healthy",
                "service": "FieldMappingService",
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id,
                "mapping_count": mapping_count,
                "base_mappings": len(self.BASE_MAPPINGS),
                "cached_learned_mappings": (
                    len(self._learned_mappings_cache)
                    if self._learned_mappings_cache
                    else 0
                ),
            }
        except Exception as e:
            await self.record_failure(
                operation="health_check",
                error=e,
                context_data={"service": "FieldMappingService"},
            )
            return {
                "status": "unhealthy",
                "service": "FieldMappingService",
                "error": str(e),
            }

    async def analyze_columns(
        self,
        columns: List[str],
        data_import_id: Optional[UUID] = None,
        master_flow_id: Optional[UUID] = None,
        asset_type: str = "server",
        sample_data: Optional[List[List[Any]]] = None,
    ) -> MappingAnalysis:
        """
        Analyze columns and provide mapping insights.

        Args:
            columns: List of column names to analyze
            data_import_id: Optional data import ID for context
            master_flow_id: Optional master flow ID for context
            asset_type: Type of asset being analyzed
            sample_data: Optional sample data for context

        Returns:
            Mapping analysis with suggestions
        """
        return await self.business_logic.analyze_columns(
            columns, data_import_id, master_flow_id, asset_type, sample_data
        )

    async def learn_field_mapping(
        self,
        source_field: str,
        target_field: str,
        data_import_id: UUID,
        master_flow_id: Optional[UUID] = None,
        confidence: float = 0.9,
        source: str = "user",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Learn a new field mapping.

        Args:
            source_field: Source field name
            target_field: Target canonical field name
            data_import_id: Required data import ID
            master_flow_id: Optional master flow ID
            confidence: Confidence score (0-1)
            source: Source of the mapping (user, ai, system)
            context: Optional context information

        Returns:
            Result of learning operation
        """
        return await self.business_logic.learn_field_mapping(
            source_field,
            target_field,
            data_import_id,
            master_flow_id,
            confidence,
            source,
            context,
        )

    async def learn_negative_mapping(
        self,
        source_field: str,
        target_field: str,
        data_import_id: UUID,
        master_flow_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Learn that a field mapping should NOT be made.

        Args:
            source_field: Source field that should not map
            target_field: Target field to avoid
            data_import_id: Required data import ID
            master_flow_id: Optional master flow ID
            reason: Optional reason for rejection

        Returns:
            Result of negative learning
        """
        return await self.business_logic.learn_negative_mapping(
            source_field, target_field, data_import_id, master_flow_id, reason
        )

    async def get_field_mappings(
        self,
        data_import_id: Optional[UUID] = None,
        master_flow_id: Optional[UUID] = None,
        asset_type: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """
        Get all field mappings for the current context.

        Args:
            data_import_id: Optional data import ID filter
            master_flow_id: Optional master flow ID filter
            asset_type: Optional asset type filter

        Returns:
            Dictionary of canonical fields to their variations
        """
        return await get_field_mappings(
            self._analyzer,
            self.repository,
            self,
            data_import_id,
            master_flow_id,
            asset_type,
        )

    async def validate_mapping(
        self,
        source_field: str,
        target_field: str,
        data_import_id: Optional[UUID] = None,
        master_flow_id: Optional[UUID] = None,
        sample_values: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a field mapping with optional content analysis.

        Args:
            source_field: Source field name
            target_field: Target field name
            data_import_id: Optional data import ID for context
            master_flow_id: Optional master flow ID for context
            sample_values: Optional sample values for validation

        Returns:
            Validation result with confidence and issues
        """
        return await validate_mapping(
            self.repository,
            self._analyzer,
            self,
            source_field,
            target_field,
            data_import_id,
            master_flow_id,
            sample_values,
        )
