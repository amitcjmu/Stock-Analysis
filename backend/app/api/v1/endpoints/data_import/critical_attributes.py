"""
Critical Attributes Module - Critical attributes analysis and status.
Handles critical attributes framework, mapping status, and assessment readiness.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
import logging

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import ImportFieldMapping, DataImport

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/critical-attributes-status")
async def get_critical_attributes_status(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get critical attributes mapping status with real-time progress."""
    try:
        # Define critical attributes framework
        critical_attributes = {
            "asset_name": {
                "field": "Asset Name",
                "category": "identification",
                "description": "Primary identifier for the asset",
                "required": True,
                "migration_critical": True,
                "business_impact": "high"
            },
            "hostname": {
                "field": "Hostname",
                "category": "identification", 
                "description": "Network hostname or FQDN",
                "required": True,
                "migration_critical": True,
                "business_impact": "high"
            },
            "asset_type": {
                "field": "Asset Type",
                "category": "technical",
                "description": "Classification of asset (server, application, etc.)",
                "required": True,
                "migration_critical": True,
                "business_impact": "high"
            },
            "environment": {
                "field": "Environment",
                "category": "environment",
                "description": "Operating environment (Production, Test, etc.)",
                "required": True,
                "migration_critical": True,
                "business_impact": "high"
            },
            "business_criticality": {
                "field": "Business Criticality",
                "category": "business",
                "description": "Business importance level",
                "required": False,
                "migration_critical": True,
                "business_impact": "high"
            },
            "department": {
                "field": "Department",
                "category": "business",
                "description": "Owning department or business unit",
                "required": False,
                "migration_critical": False,
                "business_impact": "medium"
            },
            "ip_address": {
                "field": "IP Address",
                "category": "network",
                "description": "Primary IP address",
                "required": False,
                "migration_critical": False,
                "business_impact": "medium"
            },
            "operating_system": {
                "field": "Operating System",
                "category": "technical",
                "description": "Operating system and version",
                "required": False,
                "migration_critical": False,
                "business_impact": "medium"
            },
            "business_owner": {
                "field": "Business Owner",
                "category": "business",
                "description": "Business owner or stakeholder",
                "required": False,
                "migration_critical": False,
                "business_impact": "medium"
            },
            "technical_owner": {
                "field": "Technical Owner",
                "category": "business",
                "description": "Technical owner or administrator",
                "required": False,
                "migration_critical": False,
                "business_impact": "medium"
            }
        }
        
        # Get current field mappings for critical attributes
        # Note: ImportFieldMapping doesn't have client_account_id/engagement_id directly
        # We need to join through DataImport to filter by context
        query = select(ImportFieldMapping).join(
            ImportFieldMapping.data_import
        ).where(
            and_(
                DataImport.client_account_id == context.client_account_id,
                DataImport.engagement_id == context.engagement_id,
                ImportFieldMapping.target_field.in_(list(critical_attributes.keys()))
            )
        )
        
        result = await db.execute(query)
        mappings = result.scalars().all()
        
        # Process each critical attribute with current mapping status
        attributes_status = []
        for attr_key, attr_config in critical_attributes.items():
            # Find current mapping for this attribute
            current_mapping = next((m for m in mappings if m.target_field == attr_key), None)
            
            # Determine status and mapping details
            if current_mapping:
                if current_mapping.status == "approved":
                    status = "mapped"
                    confidence = current_mapping.confidence_score or 0.8
                    quality_score = min(95, confidence * 100 + 10)
                    completeness_percentage = 100
                elif current_mapping.status == "pending":
                    status = "partially_mapped"
                    confidence = current_mapping.confidence_score or 0.0
                    quality_score = confidence * 70  # Lower quality for pending
                    completeness_percentage = 50
                else:  # rejected
                    status = "unmapped"
                    confidence = None
                    quality_score = 0
                    completeness_percentage = 0
                
                mapped_to = current_mapping.source_field if status == "mapped" else None
                mapping_type = current_mapping.mapping_type if status == "mapped" else None
            else:
                status = "unmapped"
                confidence = None
                quality_score = 0
                completeness_percentage = 0
                mapped_to = None
                mapping_type = None
            
            # Generate AI suggestion for unmapped fields
            ai_suggestion = None
            if status == "unmapped":
                if attr_key == "asset_name":
                    ai_suggestion = "Look for fields containing 'name', 'hostname', 'asset', or 'identifier'"
                elif attr_key == "asset_type":
                    ai_suggestion = "Look for fields indicating server, application, database, or device type"
                elif attr_key == "environment":
                    ai_suggestion = "Look for fields indicating prod, test, dev, or environment classification"
            
            attribute_status = {
                "name": attr_key,
                "description": attr_config["description"],
                "category": attr_config["category"],
                "required": attr_config["required"],
                "status": status,
                "mapped_to": mapped_to,
                "source_field": mapped_to,
                "confidence": confidence,
                "quality_score": quality_score,
                "completeness_percentage": completeness_percentage,
                "mapping_type": mapping_type,
                "ai_suggestion": ai_suggestion,
                "business_impact": attr_config["business_impact"],
                "migration_critical": attr_config["migration_critical"]
            }
            
            attributes_status.append(attribute_status)
        
        # Calculate overall statistics
        total_attributes = len(critical_attributes)
        mapped_count = len([a for a in attributes_status if a["status"] == "mapped"])
        pending_count = len([a for a in attributes_status if a["status"] == "partially_mapped"])
        unmapped_count = len([a for a in attributes_status if a["status"] == "unmapped"])
        
        migration_critical_count = len([a for a in attributes_status if a["migration_critical"]])
        migration_critical_mapped = len([a for a in attributes_status if a["migration_critical"] and a["status"] == "mapped"])
        
        overall_completeness = round((mapped_count / total_attributes) * 100) if total_attributes > 0 else 0
        
        mapped_attributes = [a for a in attributes_status if a["status"] == "mapped"]
        avg_quality_score = round(sum(a["quality_score"] for a in mapped_attributes) / len(mapped_attributes)) if mapped_attributes else 0
        
        # Assessment readiness check
        assessment_ready = migration_critical_mapped >= 3  # Need at least 3 critical attributes mapped
        
        return {
            "attributes": attributes_status,
            "statistics": {
                "total_attributes": total_attributes,
                "mapped_count": mapped_count,
                "pending_count": pending_count,
                "unmapped_count": unmapped_count,
                "migration_critical_count": migration_critical_count,
                "migration_critical_mapped": migration_critical_mapped,
                "overall_completeness": overall_completeness,
                "avg_quality_score": avg_quality_score,
                "assessment_ready": assessment_ready
            },
            "recommendations": {
                "next_priority": "Map asset identification fields (name, hostname) first",
                "assessment_readiness": f"Map {max(0, 3 - migration_critical_mapped)} more critical field(s) to proceed",
                "quality_improvement": "Focus on high-confidence mappings for better analysis accuracy"
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get critical attributes status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 