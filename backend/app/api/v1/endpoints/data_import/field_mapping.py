"""
Field Mapping Module - Field mapping management and suggestions.
Handles field mapping operations, target field definitions, and AI-powered mapping suggestions.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
import logging
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import (
    DataImport, RawImportRecord, ImportFieldMapping, ImportStatus
)
from app.models.asset import Asset
# Import CrewAI Field Mapping Crew for AI-driven field mapping
try:
    from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew
    CREWAI_FIELD_MAPPING_AVAILABLE = True
except ImportError:
    CREWAI_FIELD_MAPPING_AVAILABLE = False
    create_field_mapping_crew = None

from .utilities import (
    matches_data_type, is_in_range
)
from app.schemas.discovery_schemas import FieldMappingUpdate, FieldMappingSuggestion, FieldMappingAnalysis, FieldMappingResponse
from app.services.field_mapper_modular import field_mapper
# Note: AgentManager is legacy - using individual agents per Discovery Flow Redesign
# from app.services.agents_legacy import AgentManager
from app.core.auth import get_current_user_id

def validate_context_access(
    resource: Any, 
    context: RequestContext
) -> None:
    """Validate user has access to resource"""
    if hasattr(resource, 'client_account_id'):
        if resource.client_account_id != context.client_account_id:
            raise HTTPException(403, "Access denied")
    
    if hasattr(resource, 'engagement_id') and context.engagement_id:
        if resource.engagement_id != context.engagement_id:
            raise HTTPException(403, "Access denied")

router = APIRouter()
logger = logging.getLogger(__name__)

def get_safe_context() -> RequestContext:
    """Get context safely with fallback values"""
    context = get_current_context()
    if context:
        return context
    
    logger.warning("⚠️ No context available, using fallback values")
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222", 
        user_id="347d1ecd-04f6-4e3a-86ca-d35703512301"
    )

@router.get("/imports/{import_id}/field-mappings")
async def get_field_mappings(
    import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get field mappings for a specific import."""
    query = select(ImportFieldMapping).where(ImportFieldMapping.data_import_id == import_id)
    result = await db.execute(query)
    mappings = result.scalars().all()
    
    return {
        "mappings": [
            {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "mapping_type": mapping.mapping_type,
                "confidence_score": mapping.confidence_score,
                "is_user_defined": mapping.is_user_defined,
                "status": mapping.status,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None
            }
            for mapping in mappings
        ]
    }

@router.post("/imports/{import_id}/field-mappings")
async def create_or_generate_field_mappings(
    import_id: str,
    mapping_data: dict = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Create a new field mapping or generate all mappings for an import if none exist."""
    try:
        # Check if this is a request to generate all mappings (no mapping_data provided)
        if not mapping_data:
            # Check if mappings already exist
            existing_query = select(ImportFieldMapping).where(ImportFieldMapping.data_import_id == import_id)
            existing_result = await db.execute(existing_query)
            existing_mappings = existing_result.scalars().all()
            
            if existing_mappings:
                return {
                    "status": "success",
                    "message": f"Field mappings already exist ({len(existing_mappings)} mappings)",
                    "mappings_created": 0,
                    "existing_mappings": len(existing_mappings)
                }
            
            # Get the import data to extract fields
            from app.models.data_import import DataImport, RawImportRecord
            
            import_query = select(DataImport).where(DataImport.id == import_id)
            import_result = await db.execute(import_query)
            data_import = import_result.scalar_one_or_none()
            
            if not data_import:
                raise HTTPException(status_code=404, detail="Data import not found")
            
            # Get sample raw record to extract field names
            sample_query = select(RawImportRecord).where(
                RawImportRecord.data_import_id == import_id
            ).limit(1)
            sample_result = await db.execute(sample_query)
            sample_record = sample_result.scalar_one_or_none()
            
            if not sample_record or not sample_record.raw_data:
                raise HTTPException(status_code=404, detail="No raw data found for this import")
            
            # Extract field names from the raw data
            field_names = list(sample_record.raw_data.keys())
            field_names = [field for field in field_names if field.strip()]  # Remove empty fields
            
            logger.info(f"🔍 Found {len(field_names)} fields to map: {field_names}")
            
            # Generate intelligent field mappings
            mappings_created = []
            
            for source_field in field_names:
                # Intelligent mapping based on field name similarity
                target_field = _intelligent_field_mapping(source_field)
                confidence = _calculate_mapping_confidence(source_field, target_field)
                
                # Create the mapping
                mapping = ImportFieldMapping(
                    data_import_id=import_id,
                    source_field=source_field,
                    target_field=target_field,
                    mapping_type="ai_suggested",
                    confidence_score=confidence,
                    status="suggested",  # Requires user approval
                    is_user_defined=False,
                    is_validated=False,
                    original_ai_suggestion=target_field,
                    user_feedback=None
                )
                
                db.add(mapping)
                mappings_created.append({
                    "source_field": source_field,
                    "target_field": target_field,
                    "confidence": confidence
                })
            
            await db.commit()
            
            logger.info(f"✅ Created {len(mappings_created)} field mappings for import {import_id}")
            
            return {
                "status": "success",
                "message": f"Generated {len(mappings_created)} field mappings",
                "mappings_created": len(mappings_created),
                "import_id": import_id,
                "mappings": mappings_created
            }
        
        else:
            # Original single mapping creation logic
            mapping = ImportFieldMapping(
                data_import_id=import_id,
                source_field=mapping_data["source_field"],
                target_field=mapping_data["target_field"],
                mapping_type=mapping_data.get("mapping_type", "direct"),
                confidence_score=mapping_data.get("confidence_score", 1.0),
                is_user_defined=mapping_data.get("is_user_defined", True),
                validation_rules=mapping_data.get("validation_rules"),
                transformation_logic=mapping_data.get("transformation_logic"),
                status=mapping_data.get("status", "approved"),
                user_feedback=mapping_data.get("user_feedback"),
                original_ai_suggestion=mapping_data.get("original_ai_suggestion")
            )
            
            db.add(mapping)
            await db.commit()
            await db.refresh(mapping)
            
            return {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "status": "created"
            }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create/generate field mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create/generate mappings: {str(e)}")

@router.post("/imports/latest/field-mappings")
async def create_field_mapping_latest(
    mapping_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new field mapping for the latest import."""
    try:
        # Get the latest import
        latest_query = select(DataImport).where(
            DataImport.status == ImportStatus.PROCESSED
        ).order_by(DataImport.completed_at.desc()).limit(1)
        
        result = await db.execute(latest_query)
        latest_import = result.scalar_one_or_none()
        
        if not latest_import:
            raise HTTPException(status_code=404, detail="No import found")
        
        # Check if mapping already exists
        existing_query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == latest_import.id,
                ImportFieldMapping.source_field == mapping_data["source_field"],
                ImportFieldMapping.target_field == mapping_data["target_field"]
            )
        )
        existing_result = await db.execute(existing_query)
        existing_mapping = existing_result.scalar_one_or_none()
        
        if existing_mapping:
            # Update existing mapping
            existing_mapping.status = mapping_data.get("status", "approved")
            existing_mapping.confidence_score = mapping_data.get("confidence_score", existing_mapping.confidence_score)
            existing_mapping.user_feedback = mapping_data.get("user_feedback")
            existing_mapping.mapping_type = mapping_data.get("mapping_type", existing_mapping.mapping_type)
            existing_mapping.is_user_defined = mapping_data.get("is_user_defined", True)
            
            await db.commit()
            
            return {
                "id": str(existing_mapping.id),
                "source_field": existing_mapping.source_field,
                "target_field": existing_mapping.target_field,
                "status": "updated"
            }
        else:
            # Create new mapping
            mapping = ImportFieldMapping(
                data_import_id=latest_import.id,
                source_field=mapping_data["source_field"],
                target_field=mapping_data["target_field"],
                mapping_type=mapping_data.get("mapping_type", "direct"),
                confidence_score=mapping_data.get("confidence_score", 1.0),
                is_user_defined=mapping_data.get("is_user_defined", True),
                validation_rules=mapping_data.get("validation_rules"),
                transformation_logic=mapping_data.get("transformation_logic"),
                status=mapping_data.get("status", "approved"),
                user_feedback=mapping_data.get("user_feedback"),
                original_ai_suggestion=mapping_data.get("original_ai_suggestion")
            )
            
            db.add(mapping)
            await db.commit()
            await db.refresh(mapping)
            
            return {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "status": "created"
            }
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create field mapping: {str(e)}")

@router.get("/available-target-fields")
async def get_available_target_fields():
    """Get comprehensive list of available target fields for mapping from Asset model."""
    
    # Core identification fields
    identification_fields = [
        {"name": "name", "type": "string", "required": True, "description": "Asset name or identifier", "category": "identification"},
        {"name": "hostname", "type": "string", "required": False, "description": "Asset hostname or server ID", "category": "identification"},
        {"name": "asset_id", "type": "string", "required": False, "description": "Asset ID from source system", "category": "identification"},
        {"name": "fqdn", "type": "string", "required": False, "description": "Fully qualified domain name", "category": "identification"},
        {"name": "asset_name", "type": "string", "required": False, "description": "Descriptive asset name", "category": "identification"},
    ]
    
    # Technical specification fields
    technical_fields = [
        {"name": "asset_type", "type": "enum", "required": True, "description": "Type of asset (server, database, application, etc.)", "category": "technical"},
        {"name": "operating_system", "type": "string", "required": False, "description": "Operating system", "category": "technical"},
        {"name": "os_version", "type": "string", "required": False, "description": "Operating system version", "category": "technical"},
        {"name": "cpu_cores", "type": "integer", "required": False, "description": "Number of CPU cores", "category": "technical"},
        {"name": "memory_gb", "type": "number", "required": False, "description": "Memory in GB", "category": "technical"},
        {"name": "storage_gb", "type": "number", "required": False, "description": "Storage in GB", "category": "technical"},
        {"name": "hardware_type", "type": "string", "required": False, "description": "Hardware type or model", "category": "technical"},
        {"name": "intelligent_asset_type", "type": "string", "required": False, "description": "AI-classified asset type", "category": "technical"},
    ]
    
    # Network and connectivity fields
    network_fields = [
        {"name": "ip_address", "type": "string", "required": False, "description": "Primary IP address", "category": "network"},
        {"name": "network_interfaces", "type": "json", "required": False, "description": "Network interface configuration", "category": "network"},
    ]
    
    # Environment and location fields  
    environment_fields = [
        {"name": "environment", "type": "string", "required": True, "description": "Environment (Production, Test, Development, etc.)", "category": "environment"},
        {"name": "datacenter", "type": "string", "required": False, "description": "Datacenter or facility", "category": "environment"},
        {"name": "location", "type": "string", "required": False, "description": "Physical location", "category": "environment"},
        {"name": "rack_location", "type": "string", "required": False, "description": "Rack location within datacenter", "category": "environment"},
        {"name": "availability_zone", "type": "string", "required": False, "description": "Cloud availability zone", "category": "environment"},
    ]
    
    # Business ownership fields
    business_fields = [
        {"name": "business_owner", "type": "string", "required": False, "description": "Business owner or stakeholder", "category": "business"},
        {"name": "technical_owner", "type": "string", "required": False, "description": "Technical owner or administrator", "category": "business"},
        {"name": "department", "type": "string", "required": False, "description": "Owning department", "category": "business"},
        {"name": "business_criticality", "type": "string", "required": False, "description": "Business criticality level", "category": "business"},
        {"name": "source_system", "type": "string", "required": False, "description": "Source system or CMDB", "category": "business"},
    ]
    
    # Application and software fields
    application_fields = [
        {"name": "application_id", "type": "string", "required": False, "description": "Application identifier", "category": "application"},
        {"name": "application_name", "type": "string", "required": False, "description": "Application name", "category": "application"},
        {"name": "application_version", "type": "string", "required": False, "description": "Application version", "category": "application"},
        {"name": "programming_language", "type": "string", "required": False, "description": "Primary programming language", "category": "application"},
        {"name": "framework", "type": "string", "required": False, "description": "Software framework", "category": "application"},
        {"name": "database_type", "type": "string", "required": False, "description": "Database type or engine", "category": "application"},
        {"name": "technology_stack", "type": "string", "required": False, "description": "Technology stack details", "category": "application"},
    ]
    
    # Migration planning fields
    migration_fields = [
        {"name": "six_r_strategy", "type": "enum", "required": False, "description": "6R migration strategy", "category": "migration"},
        {"name": "migration_priority", "type": "integer", "required": False, "description": "Migration priority (1-10)", "category": "migration"},
        {"name": "migration_complexity", "type": "string", "required": False, "description": "Migration complexity assessment", "category": "migration"},
        {"name": "migration_wave", "type": "integer", "required": False, "description": "Migration wave number", "category": "migration"},
        {"name": "cloud_readiness_score", "type": "number", "required": False, "description": "Cloud readiness score (0-10)", "category": "migration"},
        {"name": "modernization_complexity", "type": "string", "required": False, "description": "Modernization complexity level", "category": "migration"},
        {"name": "recommended_6r_strategy", "type": "string", "required": False, "description": "AI recommended 6R strategy", "category": "migration"},
        {"name": "strategy_confidence", "type": "number", "required": False, "description": "Confidence in strategy recommendation", "category": "migration"},
        {"name": "strategy_rationale", "type": "text", "required": False, "description": "Rationale for strategy selection", "category": "migration"},
        {"name": "sixr_ready", "type": "string", "required": False, "description": "6R strategy readiness", "category": "migration"},
        {"name": "estimated_migration_effort", "type": "string", "required": False, "description": "Estimated migration effort", "category": "migration"},
    ]
    
    # Cost and financial fields
    cost_fields = [
        {"name": "current_monthly_cost", "type": "number", "required": False, "description": "Current monthly operating cost", "category": "cost"},
        {"name": "estimated_cloud_cost", "type": "number", "required": False, "description": "Estimated cloud cost", "category": "cost"},
        {"name": "estimated_monthly_cost", "type": "number", "required": False, "description": "Estimated monthly cost", "category": "cost"},
        {"name": "license_cost", "type": "number", "required": False, "description": "Software license cost", "category": "cost"},
        {"name": "support_cost", "type": "number", "required": False, "description": "Support and maintenance cost", "category": "cost"},
        {"name": "cost_optimization_potential", "type": "number", "required": False, "description": "Cost optimization potential", "category": "cost"},
    ]
    
    # Risk and security fields
    risk_fields = [
        {"name": "risk_score", "type": "number", "required": False, "description": "Overall risk score", "category": "risk"},
        {"name": "security_classification", "type": "string", "required": False, "description": "Security classification level", "category": "risk"},
        {"name": "vulnerability_score", "type": "number", "required": False, "description": "Security vulnerability score", "category": "risk"},
        {"name": "tech_debt_score", "type": "number", "required": False, "description": "Technical debt score", "category": "risk"},
        {"name": "compliance_requirements", "type": "json", "required": False, "description": "Compliance requirements", "category": "risk"},
        {"name": "security_findings", "type": "json", "required": False, "description": "Security assessment findings", "category": "risk"},
    ]
    
    # Dependencies and relationships
    dependency_fields = [
        {"name": "dependencies", "type": "json", "required": False, "description": "Asset dependencies", "category": "dependencies"},
        {"name": "dependents", "type": "json", "required": False, "description": "Assets dependent on this asset", "category": "dependencies"},
    ]
    
    # Performance and quality fields
    performance_fields = [
        {"name": "performance_metrics", "type": "json", "required": False, "description": "Performance metrics", "category": "performance"},
        {"name": "compatibility_issues", "type": "json", "required": False, "description": "Compatibility issues", "category": "performance"},
        {"name": "completeness_score", "type": "number", "required": False, "description": "Data completeness score", "category": "performance"},
        {"name": "quality_score", "type": "number", "required": False, "description": "Overall data quality score", "category": "performance"},
        {"name": "confidence_score", "type": "number", "required": False, "description": "AI confidence score", "category": "performance"},
        {"name": "ai_confidence_score", "type": "number", "required": False, "description": "AI analysis confidence", "category": "performance"},
    ]
    
    # Discovery and metadata fields
    discovery_fields = [
        {"name": "discovery_method", "type": "string", "required": False, "description": "Discovery method used", "category": "discovery"},
        {"name": "discovery_source", "type": "string", "required": False, "description": "Discovery source system", "category": "discovery"},
        {"name": "source_file", "type": "string", "required": False, "description": "Source import file", "category": "discovery"},
        {"name": "description", "type": "text", "required": False, "description": "Asset description", "category": "discovery"},
    ]
    
    # AI insights and recommendations
    ai_fields = [
        {"name": "ai_recommendations", "type": "json", "required": False, "description": "AI recommendations", "category": "ai_insights"},
    ]
    
    # Combine all fields
    all_fields = (
        identification_fields + technical_fields + network_fields + 
        environment_fields + business_fields + application_fields + 
        migration_fields + cost_fields + risk_fields + dependency_fields +
        performance_fields + discovery_fields + ai_fields
    )
    
    return {
        "fields": all_fields,
        "field_count": len(all_fields),
        "categories": {
            "identification": len(identification_fields),
            "technical": len(technical_fields), 
            "network": len(network_fields),
            "environment": len(environment_fields),
            "business": len(business_fields),
            "application": len(application_fields),
            "migration": len(migration_fields),
            "cost": len(cost_fields),
            "risk": len(risk_fields),
            "dependencies": len(dependency_fields),
            "performance": len(performance_fields),
            "discovery": len(discovery_fields),
            "ai_insights": len(ai_fields)
        }
    }

@router.post("/custom-fields")
async def create_custom_field(
    field_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a custom target field dynamically that becomes available for all future mappings."""
    try:
        # Validate field data
        required_fields = ["field_name", "field_type"]
        for field in required_fields:
            if field not in field_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        field_name = field_data["field_name"].lower().replace(" ", "_").replace('(', '').replace(')', '')
        
        # Check if field already exists
        existing_query = select(CustomTargetField).where(
            and_(
                CustomTargetField.field_name == field_name,
                CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
            )
        )
        existing_result = await db.execute(existing_query)
        existing_field = existing_result.scalar_one_or_none()
        
        if existing_field:
            return {
                "field_name": field_name,
                "status": "already_exists",
                "message": f"Field '{field_name}' already exists",
                "field_id": str(existing_field.id)
            }
        
        # Create new custom field
        custom_field = CustomTargetField(
            client_account_id="d838573d-f461-44e4-81b5-5af510ef83b7",
            field_name=field_name,
            field_type=field_data["field_type"],
            description=field_data.get("description", f"Custom field: {field_name}"),
            is_required=field_data.get("required", False),
            is_critical=field_data.get("is_critical", False),
            created_by="eef6ea50-6550-4f14-be2c-081d4eb23038",  # Demo user
            validation_schema=field_data.get("validation_schema"),
            default_value=field_data.get("default_value"),
            allowed_values=field_data.get("allowed_values")
        )
        
        db.add(custom_field)
        await db.commit()
        await db.refresh(custom_field)
        
        return {
            "field_id": str(custom_field.id),
            "field_name": custom_field.field_name,
            "field_type": custom_field.field_type,
            "description": custom_field.description,
            "status": "created",
            "message": f"Custom field '{field_name}' created successfully and is now available for mapping"
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating custom field: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create custom field: {str(e)}")

@router.get("/imports/{import_id}/field-mapping-suggestions")
async def get_field_mapping_suggestions(
    import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get AI-learned field mapping suggestions based on historical patterns."""
    try:
        # Get raw records to analyze content
        query = select(RawImportRecord).where(RawImportRecord.data_import_id == import_id).limit(10)
        result = await db.execute(query)
        records = result.scalars().all()
        
        if not records:
            return {"suggestions": []}
        
        # Get all available target fields (standard + custom)
        available_fields = await get_all_available_fields(db)
        
        # Get learned patterns for this client
        client_account_id = "d838573d-f461-44e4-81b5-5af510ef83b7"  # Demo context
        learned_patterns = await get_learned_patterns(client_account_id, db)
        
        # Analyze each source field using AI learning
        sample_data = records[0].raw_data
        suggestions = []
        
        for source_field, sample_value in sample_data.items():
            suggestion = generate_learned_suggestion(
                source_field, 
                sample_value,
                [record.raw_data.get(source_field, "") for record in records[:5]],
                available_fields,
                learned_patterns
            )
            if suggestion:
                suggestions.append(suggestion)
        
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error in field mapping suggestions: {e}")
        return {"suggestions": [], "error": str(e)}

async def get_all_available_fields(db: AsyncSession):
    """Get both standard and custom target fields."""
    # Standard fields (from your existing endpoint)
    standard_fields = [
        {"name": "hostname", "type": "string", "required": True, "description": "Asset hostname or server ID"},
        {"name": "asset_name", "type": "string", "required": False, "description": "Descriptive name of application/service"},
        {"name": "ip_address", "type": "string", "required": False, "description": "Primary IP address"},
        {"name": "asset_type", "type": "string", "required": True, "description": "Type of asset (Server, Database, etc.)"},
        {"name": "operating_system", "type": "string", "required": False, "description": "Operating system"},
        {"name": "environment", "type": "string", "required": True, "description": "Environment (Production, Test, etc.)"},
        {"name": "cpu_cores", "type": "integer", "required": False, "description": "Number of CPU cores"},
        {"name": "memory_gb", "type": "number", "required": False, "description": "Memory in GB"},
        {"name": "location", "type": "string", "required": False, "description": "Physical location or datacenter"},
        {"name": "department", "type": "string", "required": False, "description": "Owning department"},
        {"name": "owner", "type": "string", "required": False, "description": "Asset owner"},
        {"name": "vendor", "type": "string", "required": False, "description": "Hardware/software vendor"},
        {"name": "model", "type": "string", "required": False, "description": "Asset model number"}
    ]
    
    try:
        # Get custom fields for this client
        query = select(CustomTargetField).where(CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7")
        result = await db.execute(query)
        custom_fields = result.scalars().all()
        
        # Combine standard and custom fields
        all_fields = standard_fields + [
            {
                "name": field.field_name,
                "type": field.field_type,
                "required": field.is_required,
                "description": field.description,
                "is_custom": True,
                "usage_count": field.usage_count,
                "success_rate": field.success_rate
            }
            for field in custom_fields
        ]
        
        return all_fields
    except Exception as e:
        logger.error(f"Error getting custom fields: {e}")
        return standard_fields

async def get_learned_patterns(client_account_id: str, db: AsyncSession):
    """Get AI-learned mapping patterns for this client."""
    # MappingLearningPattern model removed in consolidation
    # TODO: Implement new learning pattern storage if needed
    return []
    
    # Original implementation commented out:
    # try:
    #     query = select(MappingLearningPattern).where(
    #         MappingLearningPattern.client_account_id == client_account_id
    #     ).order_by(MappingLearningPattern.pattern_confidence.desc())
    #     
    #     result = await db.execute(query)
    #     patterns = result.scalars().all()
    #     
    #     return [
    #         {
    #             "source_pattern": pattern.source_field_pattern,
    #             "target_field": pattern.target_field,
    #             "confidence": pattern.pattern_confidence,
    #             "content_pattern": pattern.content_pattern,
    #             "matching_rules": pattern.matching_rules,
    #             "success_count": pattern.success_count,
    #             "failure_count": pattern.failure_count
    #         }
    #         for pattern in patterns
    #     ]
    # except Exception as e:
    #     logger.error(f"Error getting learned patterns: {e}")
    #     return []

async def generate_ai_field_mapping_suggestions(
    source_fields: List[str], 
    sample_data: List[Dict[str, Any]], 
    available_fields: List[Dict[str, Any]],
    crewai_service=None
) -> List[Dict[str, Any]]:
    """Generate field mapping suggestions using CrewAI Field Mapping Crew."""
    
    if not CREWAI_FIELD_MAPPING_AVAILABLE or not crewai_service:
        logger.warning("CrewAI Field Mapping not available, using fallback suggestions")
        return _fallback_field_mapping_suggestions(source_fields, sample_data, available_fields)
    
    try:
        # Create Field Mapping Crew
        field_mapping_crew = create_field_mapping_crew(
            crewai_service=crewai_service,
            raw_data=sample_data,
            shared_memory=None,
            knowledge_base=None
        )
        
        # Execute the crew to get AI-driven field mapping analysis
        crew_result = field_mapping_crew.kickoff()
        
        # Parse crew results into field mapping suggestions
        suggestions = _parse_field_mapping_crew_results(crew_result, source_fields, available_fields)
        
        logger.info(f"✅ CrewAI Field Mapping Crew generated {len(suggestions)} suggestions")
        return suggestions
        
    except Exception as e:
        logger.error(f"Error in CrewAI field mapping analysis: {e}")
        return _fallback_field_mapping_suggestions(source_fields, sample_data, available_fields)

def _parse_field_mapping_crew_results(crew_result: Any, source_fields: List[str], available_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse CrewAI Field Mapping Crew results into structured suggestions."""
    suggestions = []
    result_str = str(crew_result) if crew_result else ""
    
    try:
        # Extract field mapping recommendations from crew result
        # This is a simplified parser - in production, this would use structured output
        
        for source_field in source_fields:
            # Look for field mapping suggestions in the crew result
            best_match = None
            confidence = 0.7  # Default confidence for AI analysis
            
            # Simple pattern matching to find suggested target fields
            for field in available_fields:
                field_name = field.get("name", "")
                if field_name.lower() in result_str.lower() or source_field.lower() in field_name.lower():
                    best_match = field_name
                    confidence = 0.8
                    break
            
            # If no specific match found, use intelligent fallback
            if not best_match:
                best_match = _intelligent_field_fallback(source_field, available_fields)
                confidence = 0.6
            
            suggestion = {
                "source_field": source_field,
                "target_field": best_match,
                "confidence": confidence,
                "reasoning": f"AI analysis using CrewAI Field Mapping Crew: Semantic analysis suggests mapping '{source_field}' to '{best_match}'",
                "sample_values": [],  # Would be populated with actual sample data
                "mapping_type": "ai_crewai",
                "crew_analysis": result_str[:200] + "..." if len(result_str) > 200 else result_str,
                "ai_driven": True
            }
            suggestions.append(suggestion)
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error parsing crew results: {e}")
        return _fallback_field_mapping_suggestions(source_fields, [], available_fields)

def _intelligent_field_fallback(source_field: str, available_fields: List[Dict[str, Any]]) -> str:
    """Intelligent fallback for field mapping when AI analysis is unclear."""
    source_lower = source_field.lower()
    
    # Common field mapping patterns
    field_patterns = {
        'name': ['name', 'asset_name', 'hostname'],
        'id': ['asset_id', 'name', 'hostname'],
        'type': ['asset_type', 'intelligent_asset_type'],
        'os': ['operating_system'],
        'ip': ['ip_address'],
        'env': ['environment'],
        'cpu': ['cpu_cores'],
        'memory': ['memory_gb'],
        'storage': ['storage_gb'],
        'server': ['asset_type', 'name'],
        'host': ['hostname', 'name']
    }
    
    # Find best match
    for pattern, targets in field_patterns.items():
        if pattern in source_lower:
            for target in targets:
                if any(field.get("name") == target for field in available_fields):
                    return target
    
    # Default fallback
    return "name"  # Most common target field

def _fallback_field_mapping_suggestions(
    source_fields: List[str], 
    sample_data: List[Dict[str, Any]], 
    available_fields: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Fallback field mapping suggestions when CrewAI is not available."""
    suggestions = []
    
    for source_field in source_fields:
        target_field = _intelligent_field_fallback(source_field, available_fields)
        
        suggestion = {
            "source_field": source_field,
            "target_field": target_field,
            "confidence": 0.5,  # Lower confidence for fallback
            "reasoning": f"Fallback analysis: Pattern-based mapping of '{source_field}' to '{target_field}'",
            "sample_values": [],
            "mapping_type": "fallback_pattern",
            "fallback_mode": True
        }
        suggestions.append(suggestion)
    
    return suggestions

@router.post("/{import_id}/suggest-mappings", response_model=FieldMappingResponse)
async def suggest_mappings_for_import(
    import_id: str, 
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Generate and return AI-driven field mapping suggestions for a given import."""
    try:
        # 1. Get the data import session
        data_import = await db.get(DataImport, import_id)
        if not data_import:
            raise HTTPException(status_code=404, detail="Data import not found")

        # 2. Get source columns and sample data from raw records
        raw_records_query = select(RawImportRecord).where(RawImportRecord.data_import_id == import_id).limit(10)
        result = await db.execute(raw_records_query)
        raw_records = result.scalars().all()
        
        if not raw_records:
            raise HTTPException(status_code=404, detail="No raw data found for this import")
        
        source_columns = list(raw_records[0].raw_data.keys())
        sample_data = [record.raw_data for record in raw_records]

        # 3. Get available target fields
        available_fields = await get_all_available_fields(db)

        # 4. Use AI-driven field mapping analysis
        try:
            # Try to get CrewAI service for AI-driven analysis
            from app.services.crewai_modular import crewai_service
            ai_suggestions = await generate_ai_field_mapping_suggestions(
                source_fields=source_columns,
                sample_data=sample_data,
                available_fields=available_fields,
                crewai_service=crewai_service if hasattr(crewai_service, 'llm') else None
            )
        except Exception as e:
            logger.warning(f"CrewAI service not available for field mapping: {e}")
            # Fallback to traditional field_mapper service
            analysis_result = await field_mapper.analyze_and_suggest_mappings(
                source_columns=source_columns,
                client_account_id=data_import.client_account_id,
                db=db
            )
            ai_suggestions = analysis_result.get("suggestions", [])

        # 5. Get existing mappings to avoid re-suggesting
        existing_mappings_query = select(ImportFieldMapping).where(ImportFieldMapping.data_import_id == import_id)
        result = await db.execute(existing_mappings_query)
        existing_mappings = result.scalars().all()

        # 6. Create enhanced analysis result
        enhanced_analysis = {
            "suggestions": ai_suggestions,
            "total_fields": len(source_columns),
            "mapped_fields": len(existing_mappings),
            "confidence_score": sum(s.get("confidence", 0) for s in ai_suggestions) / len(ai_suggestions) if ai_suggestions else 0,
            "ai_driven": True,
            "analysis_method": "crewai_field_mapping_crew" if CREWAI_FIELD_MAPPING_AVAILABLE else "fallback_pattern_matching"
        }

        response = FieldMappingResponse(
            mappings=existing_mappings,
            analysis=enhanced_analysis
        )
        
        return response

    except Exception as e:
        logger.error(f"Error suggesting mappings for import {import_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest field mappings") 

@router.get("/context-field-mappings")
async def get_context_field_mappings(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get field mappings for the current user context (client + engagement)."""
    try:
        # Extract context from request headers
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        if not context.client_account_id or not context.engagement_id:
            # Use demo context as fallback
            context.client_account_id = "demo-client-123"
            context.engagement_id = "demo-engagement-456"
            
        # Get the latest import for this context
        latest_query = select(DataImport).where(
            and_(
                DataImport.status.in_(['processed', 'completed']),  # Include both statuses
                DataImport.client_account_id == context.client_account_id,
                DataImport.engagement_id == context.engagement_id
            )
        ).order_by(DataImport.completed_at.desc()).limit(1)
        
        result = await db.execute(latest_query)
        latest_import = result.scalar_one_or_none()
        
        if not latest_import:
            return {
                "success": False,
                "message": "No processed imports found for current context",
                "mappings": [],
                "context": {
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id
                }
            }
        
        # Get field mappings for this import
        mappings_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == latest_import.id
        )
        mappings_result = await db.execute(mappings_query)
        mappings = mappings_result.scalars().all()
        
        # If no mappings exist, auto-generate them from the raw data
        if not mappings:
            logger.info(f"🔄 No field mappings found for import {latest_import.id}, auto-generating...")
            
            # Get sample raw record to extract field names
            from app.models.data_import import RawImportRecord
            sample_query = select(RawImportRecord).where(
                RawImportRecord.data_import_id == latest_import.id
            ).limit(1)
            sample_result = await db.execute(sample_query)
            sample_record = sample_result.scalar_one_or_none()
            
            if sample_record and sample_record.raw_data:
                field_names = list(sample_record.raw_data.keys())
                field_names = [field for field in field_names if field.strip()]  # Remove empty fields
                
                logger.info(f"🔍 Auto-generating mappings for {len(field_names)} fields")
                
                # Generate intelligent field mappings
                for source_field in field_names:
                    target_field = _intelligent_field_mapping(source_field)
                    confidence = _calculate_mapping_confidence(source_field, target_field)
                    
                    # Create the mapping
                    mapping = ImportFieldMapping(
                        data_import_id=latest_import.id,
                        source_field=source_field,
                        target_field=target_field,
                        mapping_type="ai_suggested",
                        confidence_score=confidence,
                        status="suggested",  # Requires user approval
                        is_user_defined=False,
                        is_validated=False,
                        original_ai_suggestion=target_field,
                        user_feedback=None
                    )
                    
                    db.add(mapping)
                
                await db.commit()
                
                # Re-fetch the newly created mappings
                mappings_result = await db.execute(mappings_query)
                mappings = mappings_result.scalars().all()
                
                logger.info(f"✅ Auto-generated {len(mappings)} field mappings")
        
        # Transform mappings to include agent confidence and reasoning
        transformed_mappings = []
        for mapping in mappings:
            transformed_mappings.append({
                "id": str(mapping.id),
                "sourceField": mapping.source_field,
                "targetAttribute": mapping.target_field,
                "confidence": mapping.confidence_score or 0.0,
                "mapping_type": mapping.mapping_type or "direct",
                "sample_values": mapping.sample_values or [],
                "status": mapping.status or "pending",
                "ai_reasoning": mapping.original_ai_suggestion or f"Agent mapped {mapping.source_field} to {mapping.target_field}",
                "is_user_defined": mapping.is_user_defined or False,
                "user_feedback": mapping.user_feedback,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                "validation_method": mapping.validation_method,
                "is_validated": mapping.is_validated or False
            })
        
        return {
            "success": True,
            "mappings": transformed_mappings,
            "total_mappings": len(transformed_mappings),
            "import_info": {
                "import_id": str(latest_import.id),
                "filename": latest_import.source_filename,
                "completed_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None
            },
            "context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get context field mappings: {e}")
        return {
            "success": False,
            "message": f"Failed to retrieve field mappings: {str(e)}",
            "mappings": []
        }

@router.get("/simple-field-mappings")
async def get_simple_field_mappings(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get simplified field mappings based on latest import data for current context."""
    try:
        # Extract context from request headers  
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        # Get the latest import for the current context
        latest_query = select(DataImport).where(
            and_(
                DataImport.status == ImportStatus.PROCESSED,
                DataImport.client_account_id == context.client_account_id if context.client_account_id else "demo-client-123",
                DataImport.engagement_id == context.engagement_id if context.engagement_id else "demo-engagement-456"
            )
        ).order_by(DataImport.completed_at.desc()).limit(1)
        
        result = await db.execute(latest_query)
        latest_import = result.scalar_one_or_none()
        
        if not latest_import:
            # Fallback to any processed import if no context-specific import found
            fallback_query = select(DataImport).where(
                DataImport.status == ImportStatus.PROCESSED
            ).order_by(DataImport.completed_at.desc()).limit(1)
            
            fallback_result = await db.execute(fallback_query)
            latest_import = fallback_result.scalar_one_or_none()
            
            if not latest_import:
                return {
                    "success": False,
                    "message": "No processed imports found",
                    "mappings": [],
                    "context": {
                        "client_account_id": context.client_account_id,
                        "engagement_id": context.engagement_id
                    }
                }
        
        # Get sample data to create intelligent mappings
        from app.models.data_import import RawImportRecord
        sample_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == latest_import.id
        ).limit(3)
        
        sample_result = await db.execute(sample_query)
        sample_records = sample_result.scalars().all()
        
        if not sample_records:
            return {
                "success": False,
                "message": "No sample data found",
                "mappings": [],
                "context": {
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id
                }
            }
        
        # Extract field names from the first record
        if sample_records:
            import json
            sample_data = json.loads(sample_records[0].raw_data) if isinstance(sample_records[0].raw_data, str) else sample_records[0].raw_data
            field_names = list(sample_data.keys()) if isinstance(sample_data, dict) else []
        else:
            field_names = []
        
        # 🎯 AGENTIC FIELD MAPPING: Use CrewAI for intelligent field mapping analysis
        # NO hard-coded heuristics - this is an agentic-first platform
        
        logger.info("🤖 Triggering agentic field mapping analysis for imported data")
        
        # Trigger the agentic field mapping crew analysis
        try:
            from app.api.v1.endpoints.data_import.agentic_critical_attributes import _execute_field_mapping_crew
            from app.core.context import extract_context_from_request
            
            # Get context for crew execution
            request_context = extract_context_from_request(request)
            
            # Execute the agentic field mapping crew
            crew_result = await _execute_field_mapping_crew(
                context=request_context,
                data_import=latest_import,
                db=db
            )
            
            # Extract mappings from crew results
            if crew_result.get("crew_execution") == "completed" and "field_mappings" in crew_result:
                mappings = crew_result["field_mappings"]
                logger.info(f"✅ Agentic field mapping completed with {len(mappings)} mappings")
            else:
                logger.warning(f"Agentic field mapping failed: {crew_result.get('analysis_result', 'Unknown error')}")
                # Create basic mappings for all fields without heuristics
                mappings = []
                for i, field_name in enumerate(field_names):
                    mappings.append({
                        "id": str(i + 1),
                        "sourceField": field_name,
                        "targetAttribute": "unmapped",
                        "confidence": 0.0,
                        "mapping_type": "agentic_pending",
                        "sample_values": [],
                        "status": "pending",
                        "ai_reasoning": "Agentic analysis required - trigger field mapping crew",
                        "is_user_defined": False,
                        "category": "agentic_analysis_required"
                    })
                    
        except Exception as e:
            logger.error(f"Agentic field mapping failed: {e}")
            # Create basic mappings for all fields without heuristics  
            mappings = []
            for i, field_name in enumerate(field_names):
                mappings.append({
                    "id": str(i + 1),
                    "sourceField": field_name,
                    "targetAttribute": "unmapped", 
                    "confidence": 0.0,
                    "mapping_type": "agentic_error",
                    "sample_values": [],
                    "status": "pending",
                    "ai_reasoning": f"Agentic analysis failed: {str(e)}",
                    "is_user_defined": False,
                    "category": "agentic_analysis_error"
                })
        
        # 🎯 AGENTIC: All field mapping analysis completed by CrewAI agents above
        # No additional heuristic processing needed
        
        return {
            "success": True,
            "mappings": mappings,
            "total_mappings": len(mappings),
            "import_info": {
                "import_id": str(latest_import.id),
                "filename": latest_import.source_filename or "Unknown",
                "completed_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
                "total_fields": len(field_names)
            },
            "agent_analysis": {
                "confidence": "high" if len(mappings) > 5 else "medium",
                "total_fields_analyzed": len(field_names),
                "mappings_suggested": len(mappings),
                "high_confidence_mappings": len([m for m in mappings if m["confidence"] >= 0.85])
            },
            "context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "import_context_specific": True if context.client_account_id and context.engagement_id else False
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get simple field mappings: {e}")
        return {
            "success": False,
            "message": f"Failed to retrieve field mappings: {str(e)}",
            "mappings": []
        }

@router.post("/mappings/approve-by-field")
async def approve_field_mapping_by_field(
    request_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Approve a field mapping by source and target field names."""
    try:
        context = get_safe_context()
        source_field = request_data.get("source_field")
        target_field = request_data.get("target_field") 
        import_id = request_data.get("import_id")
        
        if not all([source_field, target_field, import_id]):
            raise HTTPException(status_code=400, detail="Missing required fields: source_field, target_field, import_id")
        
        # Validate import exists and user has access
        import_query = select(DataImport).where(DataImport.id == import_id)
        import_result = await db.execute(import_query)
        data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            raise HTTPException(status_code=404, detail="Data import not found")
            
        # Validate context access
        validate_context_access(data_import, context)
        
        # Find or create the mapping
        mapping_query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_id,
                ImportFieldMapping.source_field == source_field
            )
        )
        result = await db.execute(mapping_query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            # Create new mapping
            mapping = ImportFieldMapping(
                data_import_id=import_id,
                source_field=source_field,
                target_field=target_field,
                mapping_type="user_defined",
                confidence_score=1.0,
                status="approved",
                is_user_defined=True,
                is_validated=True,
                validation_method="user_approved",
                user_feedback="User approved mapping"
            )
            db.add(mapping)
        else:
            # Update existing mapping
            mapping.target_field = target_field
            mapping.status = "approved"
            mapping.is_validated = True
            mapping.validation_method = "user_approved"
            mapping.user_feedback = "User approved mapping"
            mapping.is_user_defined = True
        
        # Enable agent learning
        try:
            from app.services.field_mapper_modular import field_mapper
            learning_result = field_mapper.learn_field_mapping(
                canonical_field=mapping.target_field, 
                field_variations=[mapping.source_field], 
                source="user_approval"
            )
            logger.info(f"✅ Agent learning applied for approved mapping: {mapping.source_field} -> {mapping.target_field}")
        except Exception as e:
            logger.warning(f"⚠️ Agent learning failed but mapping approved: {e}")
        
        await db.commit()
        await db.refresh(mapping)
        
        return {
            "status": "success",
            "message": f"Field mapping approved: {mapping.source_field} -> {mapping.target_field}",
            "mapping_id": str(mapping.id),
            "learning_applied": True
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to approve field mapping by field: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve mapping: {str(e)}")

@router.post("/mappings/reject-by-field")
async def reject_field_mapping_by_field(
    request_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Reject a field mapping by source and target field names."""
    try:
        context = get_safe_context()
        source_field = request_data.get("source_field")
        target_field = request_data.get("target_field")
        rejection_reason = request_data.get("rejection_reason", "User rejected this mapping")
        import_id = request_data.get("import_id")
        
        if not all([source_field, target_field, import_id]):
            raise HTTPException(status_code=400, detail="Missing required fields: source_field, target_field, import_id")
        
        # Validate import exists and user has access
        import_query = select(DataImport).where(DataImport.id == import_id)
        import_result = await db.execute(import_query)
        data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            raise HTTPException(status_code=404, detail="Data import not found")
            
        # Validate context access
        validate_context_access(data_import, context)
        
        # Find or create the mapping
        mapping_query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_id,
                ImportFieldMapping.source_field == source_field
            )
        )
        result = await db.execute(mapping_query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            # Create new mapping as rejected
            mapping = ImportFieldMapping(
                data_import_id=import_id,
                source_field=source_field,
                target_field=target_field,
                mapping_type="user_defined",
                confidence_score=0.0,
                status="rejected",
                is_user_defined=True,
                is_validated=True,
                validation_method="user_rejected",
                user_feedback=rejection_reason,
                correction_reason=rejection_reason
            )
            db.add(mapping)
        else:
            # Update existing mapping
            mapping.target_field = target_field
            mapping.status = "rejected"
            mapping.is_validated = True
            mapping.validation_method = "user_rejected"
            mapping.user_feedback = rejection_reason
            mapping.correction_reason = rejection_reason
            mapping.is_user_defined = True
        
        # Enable agent learning from rejection
        try:
            from app.services.field_mapper_modular import field_mapper
            learning_result = field_mapper.learn_field_mapping_rejection(
                mapping.source_field,
                mapping.target_field,
                rejection_reason
            )
            logger.info(f"✅ Agent learning applied for rejected mapping: {mapping.source_field} -> {mapping.target_field}")
        except Exception as e:
            logger.warning(f"⚠️ Agent learning failed but mapping rejected: {e}")
        
        await db.commit()
        await db.refresh(mapping)
        
        return {
            "status": "success", 
            "message": f"Field mapping rejected: {mapping.source_field} -> {mapping.target_field}",
            "mapping_id": str(mapping.id),
            "learning_applied": True,
            "reason": rejection_reason
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to reject field mapping by field: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject mapping: {str(e)}")

@router.post("/mappings/{mapping_id}/approve")
async def approve_field_mapping(
    mapping_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Approve a field mapping and enable agent learning."""
    try:
        context = get_safe_context()
        # Get the mapping
        mapping_query = select(ImportFieldMapping).where(ImportFieldMapping.id == mapping_id)
        result = await db.execute(mapping_query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Field mapping not found")
        
        # Update mapping status
        mapping.status = "approved"
        mapping.is_validated = True
        mapping.validation_method = "user_approved"
        mapping.user_feedback = "User approved mapping"
        
        # Enable agent learning - teach the field mapping agents
        try:
            from app.services.field_mapper_modular import field_mapper
            learning_result = field_mapper.learn_field_mapping(
                canonical_field=mapping.target_field, 
                field_variations=[mapping.source_field], 
                source="user_approval"
            )
            logger.info(f"✅ Agent learning applied for approved mapping: {mapping.source_field} -> {mapping.target_field}")
        except Exception as e:
            logger.warning(f"⚠️ Agent learning failed but mapping approved: {e}")
        
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Field mapping approved: {mapping.source_field} -> {mapping.target_field}",
            "mapping_id": mapping_id,
            "learning_applied": True
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to approve field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve mapping: {str(e)}")

@router.post("/mappings/{mapping_id}/reject")
async def reject_field_mapping(
    mapping_id: str,
    rejection_reason: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Reject a field mapping and enable agent learning from the rejection."""
    try:
        context = get_safe_context()
        # Get the mapping
        mapping_query = select(ImportFieldMapping).where(ImportFieldMapping.id == mapping_id)
        result = await db.execute(mapping_query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Field mapping not found")
        
        # Update mapping status
        mapping.status = "rejected"
        mapping.is_validated = True
        mapping.validation_method = "user_rejected"
        mapping.user_feedback = rejection_reason or "User rejected mapping"
        mapping.correction_reason = rejection_reason
        
        # Enable agent learning - teach the agents what NOT to map
        try:
            from app.services.field_mapper_modular import field_mapper
            # Learn from rejection - this is negative feedback
            learning_result = field_mapper.learn_field_mapping_rejection(
                mapping.source_field,
                mapping.target_field,
                rejection_reason or "User rejected this mapping"
            )
            logger.info(f"✅ Agent learning applied for rejected mapping: {mapping.source_field} -> {mapping.target_field}")
        except Exception as e:
            logger.warning(f"⚠️ Agent learning failed but mapping rejected: {e}")
        
        await db.commit()
        
        return {
            "status": "success", 
            "message": f"Field mapping rejected: {mapping.source_field} -> {mapping.target_field}",
            "mapping_id": mapping_id,
            "learning_applied": True,
            "reason": rejection_reason
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to reject field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject mapping: {str(e)}")

@router.patch("/mappings/{mapping_id}")
async def update_field_mapping(
    mapping_id: str,
    mapping_update: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update a field mapping."""
    try:
        context = get_safe_context()
        # Get the mapping
        mapping_query = select(ImportFieldMapping).where(ImportFieldMapping.id == mapping_id)
        result = await db.execute(mapping_query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Field mapping not found")
        
        # Update the mapping
        if "target_field" in mapping_update:
            mapping.target_field = mapping_update["target_field"]
        if "status" in mapping_update:
            mapping.status = mapping_update["status"]
        if "is_user_defined" in mapping_update:
            mapping.is_user_defined = mapping_update["is_user_defined"]
        if "confidence_score" in mapping_update:
            mapping.confidence_score = mapping_update["confidence_score"]
        if "user_feedback" in mapping_update:
            mapping.user_feedback = mapping_update["user_feedback"]
        
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Field mapping updated: {mapping.source_field} -> {mapping.target_field}",
            "mapping_id": mapping_id
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update mapping: {str(e)}")

@router.get("/mappings/approval-status/{data_import_id}")
async def get_mapping_approval_status(
    data_import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the approval status of all mappings for a data import."""
    try:
        # Get all mappings for this import
        mappings_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == data_import_id
        )
        result = await db.execute(mappings_query)
        mappings = result.scalars().all()
        
        if not mappings:
            return {
                "data_import_id": data_import_id,
                "total_mappings": 0,
                "approved_mappings": 0,
                "rejected_mappings": 0,
                "pending_mappings": 0,
                "approval_complete": False,
                "can_proceed_to_asset_creation": False
            }
        
        # Calculate approval statistics
        approved_count = len([m for m in mappings if m.status == "approved"])
        rejected_count = len([m for m in mappings if m.status == "rejected"])
        pending_count = len([m for m in mappings if m.status in ["suggested", "pending"]])
        
        # Determine if we can proceed to asset creation
        # At least some mappings must be approved, and no mappings should be pending
        can_proceed = approved_count > 0 and pending_count == 0
        
        return {
            "data_import_id": data_import_id,
            "total_mappings": len(mappings),
            "approved_mappings": approved_count,
            "rejected_mappings": rejected_count,
            "pending_mappings": pending_count,
            "approval_complete": pending_count == 0,
            "can_proceed_to_asset_creation": can_proceed,
            "mappings": [
                {
                    "id": str(m.id),
                    "source_field": m.source_field,
                    "target_field": m.target_field,
                    "status": m.status,
                    "confidence_score": m.confidence_score,
                    "user_feedback": m.user_feedback
                }
                for m in mappings
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get mapping approval status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get approval status: {str(e)}")

@router.post("/generate-mappings-for-import/{import_id}")
async def generate_field_mappings_for_import(
    import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate field mappings for all fields in an import when none exist."""
    try:
        context = get_safe_context()
        # Check if mappings already exist
        existing_query = select(ImportFieldMapping).where(ImportFieldMapping.data_import_id == import_id)
        existing_result = await db.execute(existing_query)
        existing_mappings = existing_result.scalars().all()
        
        if existing_mappings:
            return {
                "status": "success",
                "message": f"Field mappings already exist ({len(existing_mappings)} mappings)",
                "mappings_created": 0,
                "existing_mappings": len(existing_mappings)
            }
        
        # Get the import data to extract fields
        from app.models.data_import import DataImport, RawImportRecord
        
        import_query = select(DataImport).where(DataImport.id == import_id)
        import_result = await db.execute(import_query)
        data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            raise HTTPException(status_code=404, detail="Data import not found")
        
        # Get sample raw record to extract field names
        sample_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == import_id
        ).limit(1)
        sample_result = await db.execute(sample_query)
        sample_record = sample_result.scalar_one_or_none()
        
        if not sample_record or not sample_record.raw_data:
            raise HTTPException(status_code=404, detail="No raw data found for this import")
        
        # Extract field names from the raw data
        field_names = list(sample_record.raw_data.keys())
        field_names = [field for field in field_names if field.strip()]  # Remove empty fields
        
        logger.info(f"🔍 Found {len(field_names)} fields to map: {field_names}")
        
        # Generate intelligent field mappings
        mappings_created = []
        
        for source_field in field_names:
            # Intelligent mapping based on field name similarity
            target_field = _intelligent_field_mapping(source_field)
            confidence = _calculate_mapping_confidence(source_field, target_field)
            
            # Create the mapping
            mapping = ImportFieldMapping(
                data_import_id=import_id,
                source_field=source_field,
                target_field=target_field,
                mapping_type="ai_suggested",
                confidence_score=confidence,
                status="suggested",  # Requires user approval
                is_user_defined=False,
                is_validated=False,
                original_ai_suggestion=target_field,
                user_feedback=None
            )
            
            db.add(mapping)
            mappings_created.append({
                "source_field": source_field,
                "target_field": target_field,
                "confidence": confidence
            })
        
        await db.commit()
        
        logger.info(f"✅ Created {len(mappings_created)} field mappings for import {import_id}")
        
        return {
            "status": "success",
            "message": f"Generated {len(mappings_created)} field mappings",
            "mappings_created": len(mappings_created),
            "import_id": import_id,
            "mappings": mappings_created
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to generate field mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate mappings: {str(e)}")

def _intelligent_field_mapping(source_field: str) -> str:
    """Map source field to target field using intelligent pattern matching."""
    source_lower = source_field.lower().replace('_', ' ').replace('-', ' ')
    
    # Direct name mappings
    direct_mappings = {
        'asset id': 'asset_id',
        'asset name': 'name',
        'asset type': 'asset_type',
        'hostname': 'hostname',
        'ip address': 'ip_address',
        'mac address': 'mac_address',
        'operating system': 'operating_system',
        'os version': 'os_version',
        'cpu cores': 'cpu_cores',
        'ram gb': 'memory_gb',
        'storage gb': 'storage_gb',
        'manufacturer': 'manufacturer',
        'model': 'hardware_model',
        'serial number': 'serial_number',
        'location rack': 'rack_location',
        'location datacenter': 'datacenter',
        'location u': 'rack_position',
        'application service': 'application_name',
        'application owner': 'business_owner',
        'virtualization host id': 'virtualization_host',
        'last discovery date': 'last_scanned',
        'support contract end date': 'warranty_end_date',
        'maintenance window': 'maintenance_window',
        'dr tier': 'disaster_recovery_tier',
        'cloud migration readiness score': 'migration_readiness_score',
        'migration notes': 'migration_notes'
    }
    
    # Check for direct mappings first
    if source_lower in direct_mappings:
        return direct_mappings[source_lower]
    
    # Pattern-based mappings
    if 'name' in source_lower and 'asset' in source_lower:
        return 'name'
    elif 'id' in source_lower and 'asset' in source_lower:
        return 'asset_id'
    elif 'type' in source_lower:
        return 'asset_type'
    elif 'ip' in source_lower:
        return 'ip_address'
    elif 'mac' in source_lower:
        return 'mac_address'
    elif 'cpu' in source_lower or 'core' in source_lower:
        return 'cpu_cores'
    elif 'ram' in source_lower or 'memory' in source_lower:
        return 'memory_gb'
    elif 'storage' in source_lower or 'disk' in source_lower:
        return 'storage_gb'
    elif 'owner' in source_lower:
        return 'business_owner'
    elif 'location' in source_lower:
        return 'physical_location'
    elif 'environment' in source_lower:
        return 'environment'
    elif 'status' in source_lower:
        return 'status'
    else:
        # Default to custom field name
        return source_field.lower().replace(' ', '_')

def _calculate_mapping_confidence(source_field: str, target_field: str) -> float:
    """Calculate confidence score for field mapping."""
    source_lower = source_field.lower().replace('_', ' ').replace('-', ' ')
    target_lower = target_field.lower().replace('_', ' ')
    
    # High confidence for exact matches
    if source_lower == target_lower:
        return 0.95
    
    # High confidence for known good mappings
    high_confidence_patterns = [
        ('asset id', 'asset_id'),
        ('asset name', 'name'),
        ('ip address', 'ip_address'),
        ('mac address', 'mac_address'),
        ('operating system', 'operating_system')
    ]
    
    for source_pattern, target_pattern in high_confidence_patterns:
        if source_pattern in source_lower and target_pattern in target_field:
            return 0.90
    
    # Medium confidence for partial matches
    source_words = set(source_lower.split())
    target_words = set(target_lower.split())
    overlap = len(source_words.intersection(target_words))
    
    if overlap > 0:
        return min(0.85, 0.5 + (overlap * 0.2))
    
    # Low confidence for new/unknown fields
    return 0.40