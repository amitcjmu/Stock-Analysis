"""
Core field mapping route handlers.
Thin controllers that delegate to service layer.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db

from ..models.mapping_schemas import (
    FieldMappingCreate,
    FieldMappingResponse,
    FieldMappingUpdate,
    MappingValidationRequest,
    MappingValidationResponse,
)
from ..services.mapping_service import MappingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/field-mappings", tags=["field-mappings"])


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


@router.get("/imports/{import_id}/mappings", response_model=List[FieldMappingResponse])
async def get_field_mappings(
    import_id: str,
    service: MappingService = Depends(get_mapping_service)
):
    """Get all field mappings for a specific import."""
    try:
        mappings = await service.get_field_mappings(import_id)
        
        # Debug logging to check the response format
        logger.info(f"🔍 DEBUG: Retrieved {len(mappings)} mappings for import {import_id}")
        if mappings:
            first_mapping = mappings[0]
            logger.info(f"🔍 DEBUG: First mapping - source_field: {first_mapping.source_field} (type: {type(first_mapping.source_field)})")
            logger.info(f"🔍 DEBUG: First mapping dict representation: {first_mapping.dict()}")
        
        return mappings
    except Exception as e:
        logger.error(f"Error retrieving field mappings for import {import_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve field mappings")


@router.post("/imports/{import_id}/mappings", response_model=FieldMappingResponse)
async def create_field_mapping(
    import_id: str,
    mapping_data: FieldMappingCreate,
    service: MappingService = Depends(get_mapping_service)
):
    """Create a new field mapping."""
    try:
        mapping = await service.create_field_mapping(import_id, mapping_data)
        return mapping
    except ValueError as e:
        logger.warning(f"Validation error creating field mapping: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating field mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to create field mapping")


@router.put("/mappings/{mapping_id}", response_model=FieldMappingResponse)
async def update_field_mapping(
    mapping_id: str,
    update_data: FieldMappingUpdate,
    service: MappingService = Depends(get_mapping_service)
):
    """Update an existing field mapping."""
    try:
        mapping = await service.update_field_mapping(mapping_id, update_data)
        return mapping
    except ValueError as e:
        logger.warning(f"Validation error updating field mapping {mapping_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating field mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update field mapping")



@router.delete("/mappings/{mapping_id}")
async def delete_field_mapping(
    mapping_id: str,
    service: MappingService = Depends(get_mapping_service)
):
    """Delete a field mapping."""
    try:
        deleted = await service.delete_field_mapping(mapping_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Field mapping not found")
        return {"status": "success", "message": "Field mapping deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting field mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete field mapping")


@router.post("/imports/{import_id}/reanalyze")
async def trigger_field_mapping_reanalysis(
    import_id: str,
    service: MappingService = Depends(get_mapping_service),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Trigger re-analysis of field mappings using CrewAI agents.
    This will regenerate field mappings with the latest logic.
    """
    try:
        logger.info(f"🔄 Triggering field mapping re-analysis for import: {import_id}")
        
        # Get the data import
        from uuid import UUID

        from sqlalchemy import select

        from app.models.data_import import DataImport
        
        # Convert string UUID to UUID object if needed
        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid UUID format for import_id: {import_id}")
        
        import_query = select(DataImport).where(DataImport.id == import_uuid)
        import_result = await db.execute(import_query)
        data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            raise HTTPException(status_code=404, detail=f"Data import {import_id} not found")
        
        # Trigger re-analysis via critical attributes module
        from app.api.v1.endpoints.data_import.critical_attributes import _trigger_field_mapping_reanalysis
        
        await _trigger_field_mapping_reanalysis(context, data_import, db)
        
        return {
            "status": "success",
            "message": "Field mapping re-analysis triggered successfully",
            "import_id": import_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering field mapping re-analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger field mapping re-analysis")


@router.post("/imports/{import_id}/generate")
async def generate_field_mappings(
    import_id: str,
    force_regenerate: bool = False,
    service: MappingService = Depends(get_mapping_service)
):
    """Generate field mappings for an entire import."""
    try:
        # If force_regenerate is True, delete existing mappings first
        if force_regenerate:
            logger.info(f"🔄 Force regenerating field mappings for import {import_id}")
            # Delete existing mappings to trigger CrewAI regeneration
            from sqlalchemy import and_, delete, select

            from app.models.data_import import ImportFieldMapping
            
            delete_query = delete(ImportFieldMapping).where(
                and_(
                    ImportFieldMapping.data_import_id == import_id,
                    ImportFieldMapping.client_account_id == service.context.client_account_id
                )
            )
            await service.db.execute(delete_query)
            await service.db.commit()
            logger.info(f"✅ Deleted existing field mappings for import {import_id}")
        
        result = await service.generate_mappings_for_import(import_id)
        return result
    except ValueError as e:
        logger.warning(f"Error generating mappings for import {import_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating mappings for import {import_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate field mappings")


@router.post("/imports/latest/mappings")
async def create_field_mapping_latest(
    mapping_data: Optional[FieldMappingCreate] = None,
    force_regenerate: bool = False,
    request: Request = None,
    service: MappingService = Depends(get_mapping_service)
):
    """Create field mapping for the latest import in current context."""
    try:
        # Extract context from request headers
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        # Get latest import for context
        from sqlalchemy import and_, select

        from app.models.data_import import DataImport
        
        latest_query = select(DataImport).where(
            and_(
                DataImport.status.in_(['processed', 'completed']),
                DataImport.client_account_id == context.client_account_id,
                DataImport.engagement_id == context.engagement_id
            )
        ).order_by(DataImport.completed_at.desc()).limit(1)
        
        result = await service.db.execute(latest_query)
        latest_import = result.scalar_one_or_none()
        
        if not latest_import:
            raise HTTPException(status_code=404, detail="No processed imports found")
        
        if mapping_data:
            # Create specific mapping
            mapping = await service.create_field_mapping(latest_import.id, mapping_data)
            return mapping
        else:
            # Generate all mappings with optional force regeneration
            if force_regenerate:
                logger.info(f"🔄 Force regenerating field mappings for latest import {latest_import.id}")
                # Delete existing mappings to trigger CrewAI regeneration
                from sqlalchemy import and_, delete, select

                from app.models.data_import import ImportFieldMapping
                
                delete_query = delete(ImportFieldMapping).where(
                    and_(
                        ImportFieldMapping.data_import_id == latest_import.id,
                        ImportFieldMapping.client_account_id == service.context.client_account_id
                    )
                )
                await service.db.execute(delete_query)
                await service.db.commit()
                logger.info(f"✅ Deleted existing field mappings for latest import {latest_import.id}")
            
            result = await service.generate_mappings_for_import(latest_import.id)
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with latest import field mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to process field mapping request")


@router.post("/validate", response_model=MappingValidationResponse)
async def validate_field_mappings(
    request: MappingValidationRequest,
    service: MappingService = Depends(get_mapping_service)
):
    """Validate a set of field mappings."""
    try:
        validation_result = await service.validate_mappings(request)
        return validation_result
    except Exception as e:
        logger.error(f"Error validating field mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate field mappings")


@router.get("/imports/{import_id}/mappings/count")
async def get_mapping_count(
    import_id: str,
    service: MappingService = Depends(get_mapping_service)
):
    """Get count of field mappings for an import."""
    try:
        mappings = await service.get_field_mappings(import_id)
        return {
            "import_id": import_id,
            "total_mappings": len(mappings),
            "approved_mappings": len([m for m in mappings if m.is_approved]),
            "pending_mappings": len([m for m in mappings if not m.is_approved])
        }
    except Exception as e:
        logger.error(f"Error getting mapping count for import {import_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mapping count")


@router.get("/health")
async def health_check():
    """Health check endpoint for field mapping routes."""
    return {"status": "healthy", "service": "field_mapping_routes"}