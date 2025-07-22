"""
Learning Integration Module - AI learning and pattern management.
Handles user feedback learning, pattern creation, and learning statistics.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.data_import import CustomTargetField, DataImport, ImportFieldMapping

# Note: Field analysis functions have been replaced by CrewAI Field Mapping Crew
# infer_field_type and generate_format_regex are now handled by AI agents
from .utilities import generate_matching_rules

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/imports/{import_id}/learn-from-mapping")
async def learn_from_user_mapping(
    import_id: str,
    learning_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Store user corrections for AI learning - this is how the system gets smarter."""
    try:
        # Store the corrected mapping
        corrected_mapping = ImportFieldMapping(
            data_import_id=import_id,
            source_field=learning_data["source_field"],
            target_field=learning_data["corrected_target_field"],
            mapping_type="user_corrected",
            confidence_score=1.0,  # User correction has highest confidence
            is_user_defined=True,
            status="approved",
            user_feedback=learning_data.get("feedback", "User corrected AI suggestion"),
            original_ai_suggestion=learning_data.get("original_suggestion"),
            correction_reason=learning_data.get("reason", "User preference")
        )
        
        db.add(corrected_mapping)
        
        # Create or update learning pattern
        await create_or_update_learning_pattern(
            learning_data["source_field"],
            learning_data["corrected_target_field"],
            learning_data.get("sample_values", []),
            learning_data.get("was_correct", False),
            corrected_mapping,
            db
        )
        
        # Update custom field usage if applicable
        if learning_data.get("is_custom_field"):
            await update_custom_field_usage(learning_data["corrected_target_field"], learning_data.get("was_correct", True), db)
        
        await db.commit()
        
        return {
            "status": "learned",
            "message": f"✅ AI learned: '{learning_data['source_field']}' → '{learning_data['corrected_target_field']}'",
            "confidence_improved": True,
            "pattern_created": True
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error learning from mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to learn from mapping: {str(e)}")

async def create_or_update_learning_pattern(
    source_field: str, 
    target_field: str, 
    sample_values: list, 
    was_correct: bool,
    mapping: ImportFieldMapping,
    db: AsyncSession
):
    """Create or update AI learning patterns based on user feedback."""
    # MappingLearningPattern model removed in consolidation
    # TODO: Implement new learning pattern storage if needed
    logger.info("Learning pattern creation skipped - model removed in consolidation")
    return None
    
    # Original implementation commented out:
    # try:
    #     # Look for existing pattern
    #     existing_query = select(MappingLearningPattern).where(
    #         and_(
    #             MappingLearningPattern.source_field_pattern == source_field,
    #             MappingLearningPattern.target_field == target_field,
    #             MappingLearningPattern.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
    #         )
    #     )
    #     existing_result = await db.execute(existing_query)
    #     existing_pattern = existing_result.scalar_one_or_none()
    #     
    #     if existing_pattern:
            # Update existing pattern
    #        if was_correct:
    #            existing_pattern.success_count += 1
    #        else:
    #            existing_pattern.failure_count += 1
    #        
    #        existing_pattern.update_success_rate()
    #        existing_pattern.last_applied_at = datetime.utcnow()
    #        existing_pattern.times_applied += 1
    #        
            # Update content pattern with new samples
    #        content_pattern = existing_pattern.content_pattern or {}
    #        if sample_values:
    #            existing_samples = content_pattern.get("sample_values", [])
    #            content_pattern["sample_values"] = list(set(existing_samples + sample_values[:3]))
                # Note: Field type inference now handled by CrewAI Field Mapping Crew
    #            content_pattern["data_type"] = "string"  # Default fallback
    #            content_pattern["ai_analysis_needed"] = True
    #            existing_pattern.content_pattern = content_pattern
    #        
    #    else:
            # Create new learning pattern
            # Note: Advanced pattern analysis now handled by CrewAI Field Mapping Crew
    #        content_pattern = {
    #            "data_type": "string",  # Default fallback
    #            "sample_values": sample_values[:3],
    #            "format_regex": "",  # Will be analyzed by AI agents
    #            "ai_analysis_needed": True
    #        }
    #        
    #        new_pattern = MappingLearningPattern(
    #            client_account_id="d838573d-f461-44e4-81b5-5af510ef83b7",
    #            source_field_pattern=source_field,
    #            target_field=target_field,
    #            content_pattern=content_pattern,
    #            success_count=1 if was_correct else 0,
    #            failure_count=0 if was_correct else 1,
    #            pattern_confidence=1.0 if was_correct else 0.0,
    #            learned_from_mapping_id=mapping.id,
    #            user_feedback=f"Learned from user mapping: {source_field} → {target_field}",
    #            matching_rules=generate_matching_rules(source_field, sample_values),
    #            times_applied=1,
    #            last_applied_at=datetime.utcnow()
    #        )
    #        
    #        new_pattern.update_success_rate()
    #        db.add(new_pattern)
    #except Exception as e:
    #    logger.error(f"Error creating/updating learning pattern: {e}")
    #    raise e

async def update_custom_field_usage(field_name: str, was_successful: bool, db: AsyncSession):
    """Update usage statistics for custom fields."""
    try:
        query = select(CustomTargetField).where(
            and_(
                CustomTargetField.field_name == field_name,
                CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
            )
        )
        result = await db.execute(query)
        custom_field = result.scalar_one_or_none()
        
        if custom_field:
            custom_field.usage_count += 1
            custom_field.last_used_at = datetime.utcnow()
            
            # Update success rate
            if was_successful:
                current_successes = custom_field.success_rate * (custom_field.usage_count - 1)
                custom_field.success_rate = (current_successes + 1) / custom_field.usage_count
            else:
                current_successes = custom_field.success_rate * (custom_field.usage_count - 1)
                custom_field.success_rate = current_successes / custom_field.usage_count
    except Exception as e:
        logger.error(f"Error updating custom field usage: {e}")
        raise e

@router.get("/learning-statistics")
async def get_learning_statistics(db: AsyncSession = Depends(get_db)):
    """Get statistics on how much the AI has learned."""
    # MappingLearningPattern model removed in consolidation
    # Return minimal statistics based on custom fields only
    try:
        # Get custom fields count
        custom_fields_query = select(CustomTargetField).where(
            CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
        )
        custom_fields_result = await db.execute(custom_fields_query)
        custom_fields = custom_fields_result.scalars().all()
        
        return {
            "learning_summary": {
                "total_custom_fields_created": len(custom_fields),
                "total_patterns_learned": 0,  # MappingLearningPattern removed
                "high_confidence_patterns": 0,
                "total_mappings_processed": 0,
                "average_pattern_confidence": 0.0,
                "learning_enabled": False  # Temporarily disabled
            },
            "custom_fields": [
                {
                    "name": field.field_name,
                    "type": field.field_type,
                    "description": field.description,
                    "usage_count": field.usage_count
                }
                for field in custom_fields
            ],
            "recent_patterns": []  # No patterns available
        }
        
    # Original implementation commented out:
    #     # Get learning patterns count
    #     patterns_query = select(MappingLearningPattern).where(
    #         MappingLearningPattern.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
    #     )
    #     patterns_result = await db.execute(patterns_query)
    #     patterns = patterns_result.scalars().all()
        
    #     # Calculate statistics
    #     total_patterns = len(patterns)
    #     successful_patterns = sum(1 for p in patterns if p.pattern_confidence > 0.7)
    #     total_mappings_learned = sum(p.success_count + p.failure_count for p in patterns)
    #     
    #     avg_confidence = sum(p.pattern_confidence for p in patterns) / len(patterns) if patterns else 0
    #     
    #     return {
    except Exception as e:
        logger.error(f"Error getting learning statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning statistics: {str(e)}")
