"""
Core field mapping service containing business logic.
Enhanced to use CrewAI agents for intelligent field mapping.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord

from ..models.mapping_schemas import (
    FieldMappingCreate,
    FieldMappingResponse,
    FieldMappingUpdate,
    MappingValidationRequest,
    MappingValidationResponse,
)

# Legacy hardcoded mapping helpers removed - using CrewAI agents only
# from ..utils.mapping_helpers import intelligent_field_mapping, calculate_mapping_confidence
from ..validators.mapping_validators import MappingValidator

# CrewAI integration for intelligent field mapping
CREWAI_FIELD_MAPPING_ENABLED = os.getenv("CREWAI_FIELD_MAPPING_ENABLED", "true").lower() == "true"
try:
    from app.services.crewai_flows.flow_state_manager import FlowStateManager
    from app.services.crewai_flows.handlers.phase_executors.field_mapping_executor import FieldMappingExecutor
    from app.services.crewai_flows.handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI field mapping components available")
except ImportError as e:
    CREWAI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI components not available, using fallback: {e}")

logger = logging.getLogger(__name__)


class MappingService:
    """Service for field mapping operations."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.validator = MappingValidator()
    
    async def get_field_mappings(self, import_id: str) -> List[FieldMappingResponse]:
        """Get all field mappings for an import."""
        
        # Convert string UUIDs to UUID objects if needed
        from uuid import UUID
        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id
            
            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for import_id: {import_id}")
        
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid
            )
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()
        
        # NO HARDCODED FILTERING - Let CrewAI agents determine what's valid
        # The agents should have already made intelligent decisions about which fields to map
        
        # CrewAI agents determine valid mappings - no hardcoded validation
        valid_mappings = []
        for mapping in mappings:
            # Trust the agent decisions - no hardcoded filtering
            
            # Debug logging to identify the issue
            logger.info(f"🔍 DEBUG: Field mapping - source_field type: {type(mapping.source_field)}, value: {mapping.source_field}")
            logger.info(f"🔍 DEBUG: Field mapping - target_field type: {type(mapping.target_field)}, value: {mapping.target_field}")
                
            # Convert JSON transformation_rules to string, handle None values
            transformation_rule_str = None
            if mapping.transformation_rules:
                if isinstance(mapping.transformation_rules, dict):
                    # Convert dict to JSON string if needed
                    import json
                    transformation_rule_str = json.dumps(mapping.transformation_rules, default=str)
                elif isinstance(mapping.transformation_rules, str):
                    transformation_rule_str = mapping.transformation_rules
                else:
                    transformation_rule_str = str(mapping.transformation_rules)
            
            valid_mappings.append(FieldMappingResponse(
                id=mapping.id,
                source_field=str(mapping.source_field),  # Ensure string type
                target_field=str(mapping.target_field),  # Keep as string, frontend handles "UNMAPPED"
                transformation_rule=transformation_rule_str,
                validation_rule=transformation_rule_str,  # Using transformation_rules for now
                is_required=getattr(mapping, 'is_required', False),
                is_approved=mapping.status == "approved",
                confidence=float(mapping.confidence_score) if mapping.confidence_score is not None else 0.0,
                created_at=mapping.created_at,
                updated_at=mapping.updated_at
            ))
        
        logger.info(f"✅ Returning {len(valid_mappings)} field mappings for import {import_id}")
        return valid_mappings
    
    async def create_field_mapping(
        self, 
        import_id: str, 
        mapping_data: FieldMappingCreate
    ) -> FieldMappingResponse:
        """Create a new field mapping."""
        
        # Convert string UUIDs to UUID objects if needed
        from uuid import UUID
        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id
            
            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for import_id: {import_id}")
        
        # Validate mapping data
        validation_result = await self.validator.validate_mapping(mapping_data)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid mapping: {validation_result.validation_errors}")
        
        # Create mapping record
        mapping = ImportFieldMapping(
            data_import_id=import_uuid,
            client_account_id=client_account_uuid,
            source_field=mapping_data.source_field,
            target_field=mapping_data.target_field,
            match_type="user_defined",
            confidence_score=mapping_data.confidence,
            transformation_rules=mapping_data.transformation_rule,
            status="approved"  # User-created mappings are auto-approved
        )
        
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        
        logger.info(f"Created field mapping: {mapping_data.source_field} -> {mapping_data.target_field}")
        
        # Serialize transformation_rules properly for response
        transformation_rule_str = None
        if mapping.transformation_rules:
            if isinstance(mapping.transformation_rules, dict):
                import json
                transformation_rule_str = json.dumps(mapping.transformation_rules, default=str)
            elif isinstance(mapping.transformation_rules, str):
                transformation_rule_str = mapping.transformation_rules
            else:
                transformation_rule_str = str(mapping.transformation_rules)
        
        return FieldMappingResponse(
            id=mapping.id,
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            transformation_rule=transformation_rule_str,
            validation_rule=transformation_rule_str,
            is_required=False,
            is_approved=True,
            confidence=mapping.confidence_score or 0.7,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at
        )
    
    async def bulk_update_field_mappings(
        self, 
        mapping_ids: List[str], 
        update_data: FieldMappingUpdate
    ) -> Dict[str, Any]:
        """Update multiple field mappings in a single database transaction."""
        
        # Convert string UUIDs to UUID objects
        from uuid import UUID
        try:
            mapping_uuids = [UUID(id_str) if isinstance(id_str, str) else id_str for id_str in mapping_ids]
            
            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format in bulk update: {e}")
            raise ValueError(f"Invalid UUID format in mapping_ids: {e}")
        
        # Get all mappings to update
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id.in_(mapping_uuids),
                ImportFieldMapping.client_account_id == client_account_uuid
            )
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()
        
        if not mappings:
            raise ValueError("No field mappings found for the provided IDs")
        
        # Update all mappings in a single transaction
        updated_mappings = []
        failed_updates = []
        
        try:
            for mapping in mappings:
                try:
                    # Update fields
                    if update_data.target_field is not None:
                        mapping.target_field = update_data.target_field
                    if update_data.transformation_rule is not None:
                        mapping.transformation_rules = update_data.transformation_rule
                    if update_data.validation_rule is not None:
                        mapping.transformation_rules = update_data.validation_rule
                    if update_data.is_approved is not None:
                        mapping.status = "approved" if update_data.is_approved else "suggested"
                    
                    mapping.updated_at = datetime.utcnow()
                    updated_mappings.append(mapping.id)
                    
                except Exception as e:
                    logger.error(f"Error updating mapping {mapping.id}: {e}")
                    failed_updates.append({"mapping_id": mapping.id, "error": str(e)})
            
            # Commit all changes at once
            await self.db.commit()
            
            logger.info(f"Bulk updated {len(updated_mappings)} field mappings")
            
            return {
                "status": "success",
                "total_mappings": len(mapping_ids),
                "updated_mappings": len(updated_mappings),
                "failed_updates": len(failed_updates),
                "updated_ids": updated_mappings,
                "failures": failed_updates
            }
            
        except Exception as e:
            # Rollback on any error
            await self.db.rollback()
            logger.error(f"Bulk update failed: {e}")
            raise ValueError(f"Bulk update failed: {str(e)}")
    
    async def update_field_mapping(
        self, 
        mapping_id: str, 
        update_data: FieldMappingUpdate
    ) -> FieldMappingResponse:
        """Update an existing field mapping."""
        
        # Convert string UUID to UUID object if needed
        from uuid import UUID
        try:
            if isinstance(mapping_id, str):
                mapping_uuid = UUID(mapping_id)
            else:
                mapping_uuid = mapping_id
            
            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for mapping_id: {mapping_id}")
        
        # Get existing mapping
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid
            )
        )
        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            # Check if mapping exists but access is denied (different client_account)
            debug_query = select(ImportFieldMapping).where(ImportFieldMapping.id == mapping_uuid)
            debug_result = await self.db.execute(debug_query)
            debug_mapping = debug_result.scalar_one_or_none()
            
            if debug_mapping:
                logger.warning(f"Field mapping {mapping_id} access denied - different client account")
                raise ValueError(f"Field mapping {mapping_id} not found")
            else:
                logger.info(f"Field mapping {mapping_id} does not exist")
                raise ValueError(f"Field mapping {mapping_id} not found")
        
        # Update fields
        if update_data.target_field is not None:
            mapping.target_field = update_data.target_field
        if update_data.transformation_rule is not None:
            mapping.transformation_rules = update_data.transformation_rule
        if update_data.validation_rule is not None:
            mapping.transformation_rules = update_data.validation_rule
        # is_required field doesn't exist in ImportFieldMapping model
        # if update_data.is_required is not None:
        #     mapping.is_required = update_data.is_required
        if update_data.is_approved is not None:
            mapping.status = "approved" if update_data.is_approved else "suggested"
        
        mapping.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(mapping)
        
        logger.info(f"Updated field mapping {mapping_id}")
        
        # Serialize transformation_rules properly for response
        transformation_rule_str = None
        if mapping.transformation_rules:
            if isinstance(mapping.transformation_rules, dict):
                import json
                transformation_rule_str = json.dumps(mapping.transformation_rules, default=str)
            elif isinstance(mapping.transformation_rules, str):
                transformation_rule_str = mapping.transformation_rules
            else:
                transformation_rule_str = str(mapping.transformation_rules)
        
        return FieldMappingResponse(
            id=mapping.id,
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            transformation_rule=transformation_rule_str,
            validation_rule=transformation_rule_str,
            is_required=False,  # is_required field doesn't exist in ImportFieldMapping model
            is_approved=mapping.status == "approved",
            confidence=mapping.confidence_score or 0.7,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at
        )
    
    async def generate_mappings_for_import(self, import_id: str) -> Dict[str, Any]:
        """Generate field mappings for an entire import."""
        
        # Check if mappings already exist
        existing_query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_id,
                ImportFieldMapping.client_account_id == self.context.client_account_id
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_mappings = existing_result.scalars().all()
        
        if existing_mappings:
            return {
                "status": "exists",
                "message": f"Field mappings already exist ({len(existing_mappings)} mappings)",
                "mappings_created": 0,
                "existing_mappings": len(existing_mappings)
            }
        
        # Get import data
        import_query = select(DataImport).where(
            and_(
                DataImport.id == import_id,
                DataImport.client_account_id == self.context.client_account_id
            )
        )
        import_result = await self.db.execute(import_query)
        data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            raise ValueError(f"Data import {import_id} not found")
        
        # Get sample data to extract fields
        sample_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == import_id
        ).limit(1)
        sample_result = await self.db.execute(sample_query)
        sample_record = sample_result.scalar_one_or_none()
        
        if not sample_record or not sample_record.raw_data:
            raise ValueError("No raw data found for this import")
        
        # Extract field names
        field_names = [field for field in sample_record.raw_data.keys() if field.strip()]
        
        logger.info(f"Found {len(field_names)} fields to map: {field_names}")
        
        # Field mappings should already exist from discovery flow's field mapping phase
        # Check if discovery flow has already generated mappings
        logger.info("🔍 Field mappings should have been generated by discovery flow field mapping phase")
        logger.info("📋 The discovery flow contains a real CrewAI field mapping crew that automatically generates mappings")
        logger.error("❌ No field mappings found - discovery flow may not have completed field mapping phase")
        raise RuntimeError(f"Field mappings not found for import {import_id}. The discovery flow should have generated these automatically via the real CrewAI field mapping phase.")
        
        # This code should never be reached if discovery flow worked properly
        return {
            "status": "error",
            "message": "Field mappings should have been generated by discovery flow",
            "mappings_created": 0,
            "import_id": import_id,
            "error": "Discovery flow field mapping phase did not complete properly"
        }
    
    async def delete_field_mapping(self, mapping_id: str) -> bool:
        """Delete a field mapping."""
        
        # Convert string UUID to UUID object if needed
        from uuid import UUID
        try:
            if isinstance(mapping_id, str):
                mapping_uuid = UUID(mapping_id)
            else:
                mapping_uuid = mapping_id
            
            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for mapping_id: {mapping_id}")
        
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid
            )
        )
        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            return False
        
        await self.db.delete(mapping)
        await self.db.commit()
        
        logger.info(f"Deleted field mapping {mapping_id}")
        return True
    
    async def validate_mappings(
        self, 
        request: MappingValidationRequest
    ) -> MappingValidationResponse:
        """Validate a set of field mappings."""
        validation_errors = []
        warnings = []
        validated_mappings = []
        
        for mapping_data in request.mappings:
            try:
                # Validate individual mapping
                validation_result = await self.validator.validate_mapping(mapping_data)
                
                if validation_result.is_valid:
                    validated_mappings.append(FieldMappingResponse(
                        id=0,  # Temporary ID for new mappings
                        source_field=mapping_data.source_field,
                        target_field=mapping_data.target_field,
                        transformation_rule=mapping_data.transformation_rule,
                        validation_rule=mapping_data.validation_rule,
                        is_required=mapping_data.is_required,
                        is_approved=False,
                        confidence=mapping_data.confidence,
                        created_at=datetime.utcnow()
                    ))
                else:
                    validation_errors.extend(validation_result.validation_errors)
                    
                warnings.extend(validation_result.warnings)
                
            except Exception as e:
                validation_errors.append(f"Error validating mapping {mapping_data.source_field}: {str(e)}")
        
        return MappingValidationResponse(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            warnings=warnings,
            validated_mappings=validated_mappings
        )
    
    # All field mapping logic has been moved to the discovery flow's field mapping phase
    # The real CrewAI field mapping crew handles all intelligent mapping
    # This service should only retrieve existing mappings, not generate them
