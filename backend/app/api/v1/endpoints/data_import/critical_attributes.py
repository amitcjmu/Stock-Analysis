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
        # Get the latest data import session for the current context
        latest_import_query = select(DataImport).where(
            and_(
                DataImport.client_account_id == context.client_account_id,
                DataImport.engagement_id == context.engagement_id
            )
        ).order_by(DataImport.created_at.desc()).limit(1)
        
        latest_import_result = await db.execute(latest_import_query)
        latest_import = latest_import_result.scalar_one_or_none()

        if not latest_import:
            # Return default zero-state if no import session found
            return {
                "attributes": [],
                "statistics": {
                    "total_attributes": 0, "mapped_count": 0, "pending_count": 0,
                    "unmapped_count": 0, "migration_critical_count": 0,
                    "migration_critical_mapped": 0, "overall_completeness": 0,
                    "avg_quality_score": 0, "assessment_ready": False
                },
                "recommendations": {"next_priority": "Start by importing CMDB data."},
                "last_updated": datetime.utcnow().isoformat()
            }

        # Get all field mappings for the latest import session
        mappings_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == latest_import.id
        )
        mappings_result = await db.execute(mappings_query)
        all_mappings = mappings_result.scalars().all()
        
        if not all_mappings:
             return {
                "attributes": [],
                "statistics": {
                    "total_attributes": 0, "mapped_count": 0, "pending_count": 0,
                    "unmapped_count": 0, "migration_critical_count": 0,
                    "migration_critical_mapped": 0, "overall_completeness": 0,
                    "avg_quality_score": 0, "assessment_ready": False
                },
                "recommendations": {"next_priority": "Start by importing CMDB data."},
                "last_updated": datetime.utcnow().isoformat()
            }

        # Process mappings to build status list
        attributes_status = []
        for mapping in all_mappings:
            status = "unmapped"
            if mapping.status == "approved":
                status = "mapped"
            elif mapping.status == "pending":
                status = "partially_mapped"
            
            attributes_status.append({
                "name": mapping.target_field,
                "description": f"Mapping for {mapping.source_field}",
                "category": "uncategorized",
                "required": False, # This info isn't in ImportFieldMapping
                "status": status,
                "mapped_to": mapping.source_field if status == "mapped" else None,
                "source_field": mapping.source_field,
                "confidence": mapping.confidence_score or 0,
                "quality_score": (mapping.confidence_score or 0) * 100,
                "completeness_percentage": 100 if status == "mapped" else (50 if status == "partially_mapped" else 0),
                "mapping_type": mapping.mapping_type,
                "ai_suggestion": None,
                "business_impact": "unknown",
                "migration_critical": mapping.is_critical_field # Assuming this field exists
            })

        # Calculate statistics based on dynamically fetched attributes
        total_attributes = len(attributes_status)
        mapped_count = len([a for a in attributes_status if a["status"] == "mapped"])
        migration_critical_count = len([a for a in attributes_status if a["migration_critical"]])
        migration_critical_mapped = len([a for a in attributes_status if a["migration_critical"] and a["status"] == "mapped"])
        
        pending_count = len([a for a in attributes_status if a["status"] == "partially_mapped"])
        unmapped_count = total_attributes - mapped_count - pending_count
        overall_completeness = round((mapped_count / total_attributes) * 100) if total_attributes > 0 else 0
        mapped_attributes = [a for a in attributes_status if a["status"] == "mapped"]
        avg_quality_score = round(sum(a["quality_score"] for a in mapped_attributes) / len(mapped_attributes)) if mapped_attributes else 0
        assessment_ready = migration_critical_mapped >= 3

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
                 "next_priority": "Review pending mappings and address unmapped fields.",
                "assessment_readiness": f"Map {max(0, 3 - migration_critical_mapped)} more critical field(s) to proceed.",
                "quality_improvement": "Ensure all critical fields are mapped with high confidence."
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get critical attributes status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}") 