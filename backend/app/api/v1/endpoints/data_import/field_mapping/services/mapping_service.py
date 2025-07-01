"""
Core field mapping service containing business logic.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.context import RequestContext
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord
from ..models.mapping_schemas import (
    FieldMappingCreate, FieldMappingUpdate, FieldMappingResponse,
    MappingValidationRequest, MappingValidationResponse
)
from ..utils.mapping_helpers import intelligent_field_mapping, calculate_mapping_confidence
from ..validators.mapping_validators import MappingValidator

logger = logging.getLogger(__name__)


class MappingService:
    """Service for field mapping operations."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.validator = MappingValidator()
    
    async def get_field_mappings(self, import_id: str) -> List[FieldMappingResponse]:
        """Get all field mappings for an import."""
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_id,
                ImportFieldMapping.client_account_id == self.context.client_account_id
            )
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()
        
        return [
            FieldMappingResponse(
                id=mapping.id,
                source_field=mapping.source_field,
                target_field=mapping.target_field,
                transformation_rule=mapping.transformation_logic,
                validation_rule=mapping.validation_rules,
                is_required=mapping.is_required or False,
                is_approved=mapping.status == "approved",
                confidence=mapping.confidence_score or 0.7,
                created_at=mapping.created_at,
                updated_at=mapping.updated_at
            )
            for mapping in mappings
        ]
    
    async def create_field_mapping(
        self, 
        import_id: str, 
        mapping_data: FieldMappingCreate
    ) -> FieldMappingResponse:
        """Create a new field mapping."""
        
        # Validate mapping data
        validation_result = await self.validator.validate_mapping(mapping_data)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid mapping: {validation_result.validation_errors}")
        
        # Create mapping record
        mapping = ImportFieldMapping(
            data_import_id=import_id,
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            source_field=mapping_data.source_field,
            target_field=mapping_data.target_field,
            mapping_type="user_defined",
            confidence_score=mapping_data.confidence,
            is_user_defined=True,
            is_required=mapping_data.is_required,
            transformation_logic=mapping_data.transformation_rule,
            validation_rules=mapping_data.validation_rule,
            status="approved"  # User-created mappings are auto-approved
        )
        
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        
        logger.info(f"Created field mapping: {mapping_data.source_field} -> {mapping_data.target_field}")
        
        return FieldMappingResponse(
            id=mapping.id,
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            transformation_rule=mapping.transformation_logic,
            validation_rule=mapping.validation_rules,
            is_required=mapping.is_required or False,
            is_approved=True,
            confidence=mapping.confidence_score or 0.7,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at
        )
    
    async def update_field_mapping(
        self, 
        mapping_id: int, 
        update_data: FieldMappingUpdate
    ) -> FieldMappingResponse:
        """Update an existing field mapping."""
        
        # Get existing mapping
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_id,
                ImportFieldMapping.client_account_id == self.context.client_account_id
            )
        )
        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            raise ValueError(f"Field mapping {mapping_id} not found")
        
        # Update fields
        if update_data.target_field is not None:
            mapping.target_field = update_data.target_field
        if update_data.transformation_rule is not None:
            mapping.transformation_logic = update_data.transformation_rule
        if update_data.validation_rule is not None:
            mapping.validation_rules = update_data.validation_rule
        if update_data.is_required is not None:
            mapping.is_required = update_data.is_required
        if update_data.is_approved is not None:
            mapping.status = "approved" if update_data.is_approved else "suggested"
        
        mapping.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(mapping)
        
        logger.info(f"Updated field mapping {mapping_id}")
        
        return FieldMappingResponse(
            id=mapping.id,
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            transformation_rule=mapping.transformation_logic,
            validation_rule=mapping.validation_rules,
            is_required=mapping.is_required or False,
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
        
        # Generate mappings
        mappings_created = []
        for source_field in field_names:
            target_field = intelligent_field_mapping(source_field)
            confidence = calculate_mapping_confidence(source_field, target_field)
            
            mapping = ImportFieldMapping(
                data_import_id=import_id,
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                source_field=source_field,
                target_field=target_field,
                mapping_type="ai_suggested",
                confidence_score=confidence,
                status="suggested",
                is_user_defined=False,
                is_validated=False,
                original_ai_suggestion=target_field
            )
            
            self.db.add(mapping)
            mappings_created.append({
                "source_field": source_field,
                "target_field": target_field,
                "confidence": confidence
            })
        
        await self.db.commit()
        
        logger.info(f"Created {len(mappings_created)} field mappings for import {import_id}")
        
        return {
            "status": "success",
            "message": f"Generated {len(mappings_created)} field mappings",
            "mappings_created": len(mappings_created),
            "import_id": import_id,
            "mappings": mappings_created
        }
    
    async def delete_field_mapping(self, mapping_id: int) -> bool:
        """Delete a field mapping."""
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_id,
                ImportFieldMapping.client_account_id == self.context.client_account_id
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