"""
Core field mapping service - orchestrates retrieval, CRUD, and validation operations.
Enhanced to use CrewAI agents for intelligent field mapping.

This service delegates to specialized services for different operations.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

# Import canonical FieldMappingService for agent-driven mapping intelligence
from app.services.field_mapping_service import FieldMappingService

from ..models.mapping_schemas import (
    FieldMappingCreate,
    FieldMappingResponse,
    FieldMappingUpdate,
    MappingValidationRequest,
    MappingValidationResponse,
)

# Import specialized services
from .mapping_retrieval import MappingRetrievalService
from .mapping_crud import MappingCRUDService

logger = logging.getLogger(__name__)


class MappingService:
    """
    Orchestrates field mapping operations by delegating to specialized services.

    This service coordinates retrieval, CRUD, and validation operations
    and delegates mapping intelligence to the canonical FieldMappingService.
    Follows ADR-015 by using agent-driven logic instead of hardcoded heuristics.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

        # Initialize specialized services
        self._retrieval_service = MappingRetrievalService(db, context)
        self._crud_service = MappingCRUDService(db, context)
        self._field_mapping_service: FieldMappingService = None

    @property
    def field_mapping_service(self) -> FieldMappingService:
        """Lazy initialization of canonical FieldMappingService."""
        if self._field_mapping_service is None:
            self._field_mapping_service = FieldMappingService(self.db, self.context)
        return self._field_mapping_service

    async def get_field_mappings(self, import_id: str) -> List[FieldMappingResponse]:
        """Get all field mappings for an import - delegates to retrieval service."""
        return await self._retrieval_service.get_field_mappings(import_id)

    async def create_field_mapping(
        self, import_id: str, mapping_data: FieldMappingCreate
    ) -> FieldMappingResponse:
        """Create a new field mapping - delegates to CRUD service."""
        return await self._crud_service.create_field_mapping(import_id, mapping_data)

    async def update_field_mapping(
        self, mapping_id: str, update_data: FieldMappingUpdate
    ) -> FieldMappingResponse:
        """Update an existing field mapping - delegates to CRUD service."""
        return await self._crud_service.update_field_mapping(mapping_id, update_data)

    async def delete_field_mapping(self, mapping_id: str) -> bool:
        """Delete a field mapping - delegates to CRUD service."""
        return await self._crud_service.delete_field_mapping(mapping_id)

    async def bulk_update_field_mappings(
        self, mapping_ids: List[str], update_data: FieldMappingUpdate
    ) -> Dict[str, Any]:
        """Update multiple field mappings - delegates to CRUD service."""
        return await self._crud_service.bulk_update_field_mappings(
            mapping_ids, update_data
        )

    async def generate_mappings_for_import(self, import_id: str) -> Dict[str, Any]:
        """Generate field mappings for an entire import."""
        from ..utils.mapping_generator import MappingGenerator

        generator = MappingGenerator(self.db, self.context)
        return await generator.generate_mappings_for_import(import_id)

    async def validate_mappings(
        self, request: MappingValidationRequest
    ) -> MappingValidationResponse:
        """Validate a set of field mappings."""
        from ..utils.validation_helper import ValidationHelper

        validation_helper = ValidationHelper()
        return await validation_helper.validate_mappings(request)

    # Helper methods moved to utility modules for better organization

    # All field mapping logic has been moved to the discovery flow's field mapping phase
    # The real CrewAI field mapping crew handles all intelligent mapping
    # This service should only retrieve existing mappings, not generate them
