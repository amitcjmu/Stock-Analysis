"""
Field Mapping Module - Field mapping management and suggestions.
Handles field mapping operations, target field definitions, and AI-powered mapping suggestions.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
import logging

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import (
    DataImport, RawImportRecord, ImportFieldMapping, CustomTargetField, MappingLearningPattern, ImportStatus
)
from app.models.asset import Asset
from .utilities import (
    check_content_pattern_match, apply_matching_rules, matches_data_type,
    is_in_range, is_potential_new_field, infer_field_type
)

router = APIRouter()
logger = logging.getLogger(__name__)

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
async def create_field_mapping(
    import_id: str,
    mapping_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new field mapping."""
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
    try:
        query = select(MappingLearningPattern).where(
            MappingLearningPattern.client_account_id == client_account_id
        ).order_by(MappingLearningPattern.pattern_confidence.desc())
        
        result = await db.execute(query)
        patterns = result.scalars().all()
        
        return [
            {
                "source_pattern": pattern.source_field_pattern,
                "target_field": pattern.target_field,
                "confidence": pattern.pattern_confidence,
                "content_pattern": pattern.content_pattern,
                "matching_rules": pattern.matching_rules,
                "success_count": pattern.success_count,
                "failure_count": pattern.failure_count
            }
            for pattern in patterns
        ]
    except Exception as e:
        logger.error(f"Error getting learned patterns: {e}")
        return []

def generate_learned_suggestion(source_field: str, sample_value: str, all_values: list, available_fields: list, learned_patterns: list):
    """Generate mapping suggestions using learned patterns instead of hardcoded rules."""
    best_suggestion = None
    max_confidence = 0.0
    
    # First, try learned patterns
    for pattern in learned_patterns:
        confidence = calculate_pattern_match(source_field, sample_value, all_values, pattern)
        
        if confidence > max_confidence and confidence > 0.3:  # Minimum confidence threshold
            max_confidence = confidence
            best_suggestion = {
                "source_field": source_field,
                "target_field": pattern["target_field"],
                "confidence": confidence,
                "reasoning": f"AI learned pattern: '{pattern['source_pattern']}' → '{pattern['target_field']}' (success rate: {pattern['success_count']}/{pattern['success_count'] + pattern['failure_count']})",
                "sample_values": all_values[:3],
                "mapping_type": "ai_learned",
                "pattern_id": pattern.get("id"),
                "learned_from": f"{pattern['success_count']} successful mappings"
            }
    
    # If no learned pattern matches well, suggest creating a new field
    if not best_suggestion or max_confidence < 0.5:
        # Check if this looks like a new field type
        if is_potential_new_field(source_field, sample_value, available_fields):
            best_suggestion = {
                "source_field": source_field,
                "target_field": None,  # Will be created dynamically
                "confidence": 0.7,
                "reasoning": f"New field detected: '{source_field}' with values like '{sample_value}'. Consider creating a custom target field.",
                "sample_values": all_values[:3],
                "mapping_type": "suggest_new_field",
                "suggested_field_name": source_field.lower().replace(' ', '_').replace('(', '').replace(')', ''),
                "suggested_field_type": infer_field_type(all_values),
                "requires_new_field": True
            }
    
    return best_suggestion

def calculate_pattern_match(source_field: str, sample_value: str, all_values: list, pattern: dict) -> float:
    """Calculate how well a source field matches a learned pattern."""
    confidence = 0.0
    
    # Field name similarity
    if pattern["source_pattern"].lower() in source_field.lower():
        confidence += 0.4
    
    # Content pattern matching
    if pattern.get("content_pattern"):
        content_match = check_content_pattern_match(all_values, pattern["content_pattern"])
        confidence += content_match * 0.4
    
    # Apply custom matching rules if available
    if pattern.get("matching_rules"):
        rule_match = apply_matching_rules(source_field, sample_value, all_values, pattern["matching_rules"])
        confidence += rule_match * 0.2
    
    # Boost confidence based on historical success rate
    base_confidence = pattern.get("confidence", 0.0)
    confidence = confidence * (0.5 + base_confidence * 0.5)
    
    return min(confidence, 1.0) 