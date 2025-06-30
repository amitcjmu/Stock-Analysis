"""
Field Mapping API v3
Dedicated endpoints for field mapping operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import uuid

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.api.v3.schemas.responses import ErrorResponse, create_error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/field-mapping", tags=["field-mapping-v3"])


# === Field Mapping Schemas ===

class FieldMappingCreate(BaseModel):
    """Request schema for creating field mappings"""
    flow_id: uuid.UUID = Field(..., description="Discovery flow identifier")
    source_fields: List[str] = Field(..., description="Source field names")
    target_schema: str = Field(..., description="Target schema name")
    mapping_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom mapping rules")
    auto_map: bool = Field(default=True, description="Enable automatic mapping")


class FieldMappingUpdate(BaseModel):
    """Request schema for updating field mappings"""
    mappings: Dict[str, str] = Field(..., description="Field mappings (source -> target)")
    confidence_scores: Optional[Dict[str, float]] = Field(None, description="Mapping confidence scores")
    validation_notes: Optional[Dict[str, str]] = Field(None, description="Validation notes")


class FieldMappingResponse(BaseModel):
    """Response schema for field mapping operations"""
    flow_id: uuid.UUID
    mapping_id: uuid.UUID
    status: str
    mappings: Dict[str, str] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    unmapped_fields: List[str] = Field(default_factory=list)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    # Statistics
    total_fields: int = 0
    mapped_fields: int = 0
    mapping_percentage: float = 0.0
    avg_confidence: float = 0.0


class FieldMappingValidation(BaseModel):
    """Request schema for validating field mappings"""
    mappings: Dict[str, str] = Field(..., description="Field mappings to validate")
    sample_data: Optional[List[Dict[str, Any]]] = Field(None, description="Sample data for validation")


class FieldMappingValidationResponse(BaseModel):
    """Response schema for field mapping validation"""
    is_valid: bool
    validation_score: float = Field(ge=0.0, le=1.0)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    field_coverage: Dict[str, Any] = Field(default_factory=dict)
    data_type_conflicts: List[Dict[str, Any]] = Field(default_factory=list)


# === Import Field Mapping Handlers ===

# V3 uses its own implementation, V1 handlers not needed
FIELD_MAPPING_HANDLERS_AVAILABLE = True

try:
    from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
    FLOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    FLOW_MANAGEMENT_AVAILABLE = False
    logger.warning("⚠️ Flow management handler not available")


# === Field Mapping Endpoints ===

@router.post("/mappings", response_model=FieldMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_field_mapping(
    request: FieldMappingCreate,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FieldMappingResponse:
    """
    Create new field mappings for a discovery flow
    """
    try:
        logger.info(f"🗺️ Creating field mappings for flow: {request.flow_id}")
        
        mapping_id = uuid.uuid4()
        
        # Initialize response
        result = FieldMappingResponse(
            flow_id=request.flow_id,
            mapping_id=mapping_id,
            status="created",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            total_fields=len(request.source_fields)
        )
        
        # Auto-mapping logic (simplified)
        if request.auto_map:
            # Basic auto-mapping heuristics
            auto_mappings = {}
            confidence_scores = {}
            
            for field in request.source_fields:
                # Simple field name matching
                field_lower = field.lower().replace('_', '').replace(' ', '')
                
                # Common field mappings
                if 'name' in field_lower or 'hostname' in field_lower:
                    auto_mappings[field] = 'asset_name'
                    confidence_scores[field] = 0.9
                elif 'ip' in field_lower:
                    auto_mappings[field] = 'ip_address'
                    confidence_scores[field] = 0.95
                elif 'os' in field_lower or 'operating' in field_lower:
                    auto_mappings[field] = 'operating_system'
                    confidence_scores[field] = 0.85
                elif 'cpu' in field_lower or 'processor' in field_lower:
                    auto_mappings[field] = 'cpu_cores'
                    confidence_scores[field] = 0.8
                elif 'memory' in field_lower or 'ram' in field_lower:
                    auto_mappings[field] = 'memory_gb'
                    confidence_scores[field] = 0.8
                elif 'storage' in field_lower or 'disk' in field_lower:
                    auto_mappings[field] = 'storage_gb'
                    confidence_scores[field] = 0.8
                elif 'environment' in field_lower or 'env' in field_lower:
                    auto_mappings[field] = 'environment'
                    confidence_scores[field] = 0.75
                elif 'location' in field_lower or 'datacenter' in field_lower:
                    auto_mappings[field] = 'location'
                    confidence_scores[field] = 0.75
            
            result.mappings = auto_mappings
            result.confidence_scores = confidence_scores
            result.unmapped_fields = [f for f in request.source_fields if f not in auto_mappings]
            result.mapped_fields = len(auto_mappings)
            result.mapping_percentage = (len(auto_mappings) / len(request.source_fields)) * 100
            result.avg_confidence = sum(confidence_scores.values()) / max(len(confidence_scores), 1)
        
        # Store mapping in flow data if flow management is available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                mapping_data = {
                    "mapping_id": str(mapping_id),
                    "mappings": result.mappings,
                    "confidence_scores": result.confidence_scores,
                    "unmapped_fields": result.unmapped_fields,
                    "validation_results": result.validation_results,
                    "statistics": {
                        "total_fields": result.total_fields,
                        "mapped_fields": result.mapped_fields,
                        "mapping_percentage": result.mapping_percentage,
                        "avg_confidence": result.avg_confidence
                    }
                }
                
                await flow_handler.update_field_mappings(str(request.flow_id), mapping_data)
                logger.info("✅ Field mappings stored in flow data")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to store mapping in flow: {e}")
        
        logger.info(f"✅ Field mappings created: {result.mapped_fields}/{result.total_fields} mapped")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to create field mappings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create field mappings: {str(e)}"
        )


@router.get("/mappings/{flow_id}", response_model=FieldMappingResponse)
async def get_field_mapping(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FieldMappingResponse:
    """
    Get field mappings for a discovery flow
    """
    try:
        logger.info(f"🔍 Getting field mappings for flow: {flow_id}")
        
        # Try to get mappings from flow data
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                flow_status = await flow_handler.get_flow_status(str(flow_id))
                
                field_mapping = flow_status.get('field_mapping', {})
                if field_mapping:
                    result = FieldMappingResponse(
                        flow_id=flow_id,
                        mapping_id=uuid.UUID(field_mapping.get('mapping_id', str(uuid.uuid4()))),
                        status="active",
                        mappings=field_mapping.get('mappings', {}),
                        confidence_scores=field_mapping.get('confidence_scores', {}),
                        unmapped_fields=field_mapping.get('unmapped_fields', []),
                        validation_results=field_mapping.get('validation_results', {}),
                        agent_insights=field_mapping.get('agent_insights', []),
                        created_at=datetime.fromisoformat(flow_status.get('created_at', datetime.utcnow().isoformat())),
                        updated_at=datetime.fromisoformat(flow_status.get('updated_at', datetime.utcnow().isoformat())),
                        total_fields=field_mapping.get('statistics', {}).get('total_fields', 0),
                        mapped_fields=field_mapping.get('statistics', {}).get('mapped_fields', 0),
                        mapping_percentage=field_mapping.get('statistics', {}).get('mapping_percentage', 0.0),
                        avg_confidence=field_mapping.get('statistics', {}).get('avg_confidence', 0.0)
                    )
                    
                    logger.info(f"✅ Field mappings retrieved from flow data")
                    return result
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to get mappings from flow: {e}")
        
        # Return empty mapping if not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field mappings not found for flow: {flow_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get field mappings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get field mappings: {str(e)}"
        )


@router.put("/mappings/{flow_id}", response_model=FieldMappingResponse)
async def update_field_mapping(
    request: FieldMappingUpdate,
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FieldMappingResponse:
    """
    Update field mappings for a discovery flow
    """
    try:
        logger.info(f"📝 Updating field mappings for flow: {flow_id}")
        
        # Get existing mappings first
        try:
            existing_mapping = await get_field_mapping(flow_id, db, context)
        except HTTPException:
            # Create new mapping if it doesn't exist
            existing_mapping = FieldMappingResponse(
                flow_id=flow_id,
                mapping_id=uuid.uuid4(),
                status="new",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        # Update the mapping
        existing_mapping.mappings.update(request.mappings)
        if request.confidence_scores:
            existing_mapping.confidence_scores.update(request.confidence_scores)
        if request.validation_notes:
            existing_mapping.validation_results["notes"] = request.validation_notes
        
        existing_mapping.updated_at = datetime.utcnow()
        existing_mapping.status = "updated"
        
        # Recalculate statistics
        existing_mapping.mapped_fields = len(existing_mapping.mappings)
        if existing_mapping.total_fields > 0:
            existing_mapping.mapping_percentage = (existing_mapping.mapped_fields / existing_mapping.total_fields) * 100
        if existing_mapping.confidence_scores:
            existing_mapping.avg_confidence = sum(existing_mapping.confidence_scores.values()) / len(existing_mapping.confidence_scores)
        
        # Update in flow data
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                mapping_data = {
                    "mapping_id": str(existing_mapping.mapping_id),
                    "mappings": existing_mapping.mappings,
                    "confidence_scores": existing_mapping.confidence_scores,
                    "unmapped_fields": existing_mapping.unmapped_fields,
                    "validation_results": existing_mapping.validation_results,
                    "statistics": {
                        "total_fields": existing_mapping.total_fields,
                        "mapped_fields": existing_mapping.mapped_fields,
                        "mapping_percentage": existing_mapping.mapping_percentage,
                        "avg_confidence": existing_mapping.avg_confidence
                    }
                }
                
                await flow_handler.update_field_mappings(str(flow_id), mapping_data)
                logger.info("✅ Field mappings updated in flow data")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to update mapping in flow: {e}")
        
        logger.info(f"✅ Field mappings updated: {existing_mapping.mapped_fields} fields mapped")
        return existing_mapping
        
    except Exception as e:
        logger.error(f"❌ Failed to update field mappings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update field mappings: {str(e)}"
        )


@router.post("/mappings/{flow_id}/validate", response_model=FieldMappingValidationResponse)
async def validate_field_mapping(
    request: FieldMappingValidation,
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FieldMappingValidationResponse:
    """
    Validate field mappings against sample data
    """
    try:
        logger.info(f"✅ Validating field mappings for flow: {flow_id}")
        
        issues = []
        recommendations = []
        field_coverage = {}
        data_type_conflicts = []
        
        # Basic validation checks
        if not request.mappings:
            issues.append({
                "type": "EMPTY_MAPPINGS",
                "message": "No field mappings provided",
                "severity": "error"
            })
            
        # Check for duplicate target fields
        target_fields = list(request.mappings.values())
        duplicate_targets = [field for field in set(target_fields) if target_fields.count(field) > 1]
        if duplicate_targets:
            issues.append({
                "type": "DUPLICATE_TARGETS",
                "message": f"Multiple source fields mapped to the same target: {duplicate_targets}",
                "severity": "warning",
                "fields": duplicate_targets
            })
        
        # Validate against sample data if provided
        if request.sample_data:
            sample_record = request.sample_data[0] if request.sample_data else {}
            
            for source_field, target_field in request.mappings.items():
                if source_field not in sample_record:
                    issues.append({
                        "type": "SOURCE_FIELD_NOT_FOUND",
                        "message": f"Source field '{source_field}' not found in sample data",
                        "severity": "error",
                        "field": source_field
                    })
                else:
                    # Check data type compatibility
                    sample_value = sample_record[source_field]
                    field_coverage[source_field] = {
                        "target": target_field,
                        "sample_value": str(sample_value)[:100],  # Truncate for response
                        "data_type": type(sample_value).__name__
                    }
        
        # Calculate validation score
        total_checks = len(request.mappings) + len(request.sample_data or [])
        error_count = len([issue for issue in issues if issue.get("severity") == "error"])
        warning_count = len([issue for issue in issues if issue.get("severity") == "warning"])
        
        validation_score = max(0.0, 1.0 - (error_count * 0.5 + warning_count * 0.2) / max(total_checks, 1))
        is_valid = error_count == 0
        
        # Generate recommendations
        if not is_valid:
            recommendations.append("Fix all error-level issues before proceeding")
        if warning_count > 0:
            recommendations.append("Review warning-level issues for optimal mapping")
        if len(request.mappings) < 5:
            recommendations.append("Consider mapping more fields for better data coverage")
        
        result = FieldMappingValidationResponse(
            is_valid=is_valid,
            validation_score=validation_score,
            issues=issues,
            recommendations=recommendations,
            field_coverage=field_coverage,
            data_type_conflicts=data_type_conflicts
        )
        
        logger.info(f"✅ Validation completed: score={validation_score:.2f}, valid={is_valid}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to validate field mappings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate field mappings: {str(e)}"
        )


@router.delete("/mappings/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field_mapping(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Delete field mappings for a discovery flow
    """
    try:
        logger.info(f"🗑️ Deleting field mappings for flow: {flow_id}")
        
        # Remove mappings from flow data
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                await flow_handler.clear_field_mappings(str(flow_id))
                logger.info("✅ Field mappings deleted from flow data")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete mapping from flow: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete field mappings: {str(e)}"
                )
        
        logger.info(f"✅ Field mappings deleted for flow: {flow_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete field mappings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete field mappings: {str(e)}"
        )


# === Field Mapping Utilities ===

@router.get("/schemas", response_model=Dict[str, Any])
async def get_target_schemas():
    """
    Get available target schemas for field mapping
    """
    return {
        "schemas": {
            "asset_inventory": {
                "description": "Standard asset inventory schema",
                "fields": {
                    "asset_name": {"type": "string", "required": True, "description": "Asset name or hostname"},
                    "asset_type": {"type": "string", "required": True, "description": "Asset type (server, application, etc.)"},
                    "ip_address": {"type": "string", "required": False, "description": "IP address"},
                    "operating_system": {"type": "string", "required": False, "description": "Operating system"},
                    "environment": {"type": "string", "required": False, "description": "Environment (prod, test, dev)"},
                    "location": {"type": "string", "required": False, "description": "Physical location"},
                    "cpu_cores": {"type": "integer", "required": False, "description": "CPU core count"},
                    "memory_gb": {"type": "number", "required": False, "description": "Memory in GB"},
                    "storage_gb": {"type": "number", "required": False, "description": "Storage in GB"},
                    "business_owner": {"type": "string", "required": False, "description": "Business owner"},
                    "technical_owner": {"type": "string", "required": False, "description": "Technical owner"}
                }
            }
        }
    }


@router.get("/suggestions/{flow_id}", response_model=Dict[str, Any])
async def get_mapping_suggestions(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    source_field: str = Query(..., description="Source field name"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get field mapping suggestions for a specific source field
    """
    try:
        logger.info(f"💡 Getting mapping suggestions for field: {source_field}")
        
        # Simple suggestion logic based on field name patterns
        field_lower = source_field.lower().replace('_', '').replace(' ', '')
        suggestions = []
        
        # Pattern-based suggestions with confidence scores
        if 'name' in field_lower or 'hostname' in field_lower:
            suggestions.append({"target": "asset_name", "confidence": 0.9, "reason": "Field name contains 'name' or 'hostname'"})
        if 'ip' in field_lower:
            suggestions.append({"target": "ip_address", "confidence": 0.95, "reason": "Field name contains 'ip'"})
        if 'os' in field_lower or 'operating' in field_lower:
            suggestions.append({"target": "operating_system", "confidence": 0.85, "reason": "Field name suggests operating system"})
        if 'cpu' in field_lower or 'processor' in field_lower:
            suggestions.append({"target": "cpu_cores", "confidence": 0.8, "reason": "Field name suggests CPU information"})
        if 'memory' in field_lower or 'ram' in field_lower:
            suggestions.append({"target": "memory_gb", "confidence": 0.8, "reason": "Field name suggests memory information"})
        if 'storage' in field_lower or 'disk' in field_lower:
            suggestions.append({"target": "storage_gb", "confidence": 0.8, "reason": "Field name suggests storage information"})
        if 'environment' in field_lower or 'env' in field_lower:
            suggestions.append({"target": "environment", "confidence": 0.75, "reason": "Field name suggests environment"})
        if 'location' in field_lower or 'datacenter' in field_lower:
            suggestions.append({"target": "location", "confidence": 0.75, "reason": "Field name suggests location"})
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "source_field": source_field,
            "suggestions": suggestions[:5],  # Top 5 suggestions
            "auto_mapping_available": len(suggestions) > 0
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get mapping suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mapping suggestions: {str(e)}"
        )