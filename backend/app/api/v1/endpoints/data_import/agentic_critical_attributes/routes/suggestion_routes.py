"""
Agentic suggestion route handlers.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db

from ..models.attribute_schemas import AttributeSuggestion, CriticalAttribute
from ..services.attribute_analyzer import AttributeAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suggestions")


def get_attribute_analyzer(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> AttributeAnalyzer:
    """Dependency injection for attribute analyzer."""
    return AttributeAnalyzer(db, context)


@router.get("/attribute-suggestions", response_model=List[AttributeSuggestion])
async def get_attribute_suggestions(
    import_id: Optional[str] = None,
    min_confidence: float = 0.5,
    analyzer: AttributeAnalyzer = Depends(get_attribute_analyzer),
):
    """Get AI-generated attribute suggestions for field mapping."""
    try:
        from ..models.attribute_schemas import AttributeAnalysisRequest

        # Create analysis request
        request = AttributeAnalysisRequest(
            import_id=import_id,
            use_latest_import=import_id is None,
            include_crew_analysis=True,
            analysis_depth="standard",
        )

        # Get analysis results
        analysis_result = await analyzer.analyze_critical_attributes(request)

        # Filter suggestions by confidence
        filtered_suggestions = [
            suggestion
            for suggestion in analysis_result.suggestions
            if suggestion.confidence_score >= min_confidence
        ]

        logger.info(
            f"Returning {len(filtered_suggestions)} suggestions (min confidence: {min_confidence})"
        )
        return filtered_suggestions

    except Exception as e:
        logger.error(f"Error getting attribute suggestions: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get attribute suggestions"
        )


@router.get("/critical-attributes", response_model=List[CriticalAttribute])
async def get_critical_attributes(
    import_id: Optional[str] = None,
    min_importance: float = 0.6,
    analyzer: AttributeAnalyzer = Depends(get_attribute_analyzer),
):
    """Get critical attributes identified by AI analysis."""
    try:
        from ..models.attribute_schemas import AttributeAnalysisRequest

        # Create analysis request
        request = AttributeAnalysisRequest(
            import_id=import_id,
            use_latest_import=import_id is None,
            include_crew_analysis=True,
            analysis_depth="comprehensive",
        )

        # Get analysis results
        analysis_result = await analyzer.analyze_critical_attributes(request)

        # Filter attributes by importance
        critical_attributes = [
            attr
            for attr in analysis_result.attributes
            if attr.importance >= min_importance
        ]

        # Sort by importance (descending)
        critical_attributes.sort(key=lambda x: x.importance, reverse=True)

        logger.info(
            f"Returning {len(critical_attributes)} critical attributes (min importance: {min_importance})"
        )
        return critical_attributes

    except Exception as e:
        logger.error(f"Error getting critical attributes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get critical attributes")


@router.get("/mapping-recommendations/{field_name}")
async def get_field_mapping_recommendations(
    field_name: str,
    import_id: Optional[str] = None,
    analyzer: AttributeAnalyzer = Depends(get_attribute_analyzer),
):
    """Get specific mapping recommendations for a field."""
    try:
        from ..models.attribute_schemas import AttributeAnalysisRequest

        # Get analysis results
        request = AttributeAnalysisRequest(
            import_id=import_id,
            use_latest_import=import_id is None,
            include_crew_analysis=True,
        )

        analysis_result = await analyzer.analyze_critical_attributes(request)

        # Find recommendations for the specific field
        field_suggestions = [
            suggestion
            for suggestion in analysis_result.suggestions
            if suggestion.source_field.lower() == field_name.lower()
        ]

        field_attributes = [
            attr
            for attr in analysis_result.attributes
            if attr.name.lower() == field_name.lower()
        ]

        if not field_suggestions and not field_attributes:
            return {
                "field_name": field_name,
                "found": False,
                "message": "No recommendations found for this field",
                "suggestions": [],
            }

        # Combine information
        recommendations = []

        for suggestion in field_suggestions:
            rec = {
                "target_field": suggestion.suggested_target,
                "confidence": suggestion.confidence_score,
                "importance": suggestion.importance_score,
                "reasoning": suggestion.reasoning,
                "migration_priority": suggestion.migration_priority,
            }
            recommendations.append(rec)

        for attribute in field_attributes:
            rec = {
                "target_fields": attribute.mapping_suggestions,
                "confidence": attribute.confidence,
                "importance": attribute.importance,
                "reasoning": attribute.reasoning,
                "migration_impact": attribute.migration_impact,
                "data_type": attribute.data_type,
                "sample_values": attribute.sample_values,
            }
            recommendations.append(rec)

        return {
            "field_name": field_name,
            "found": True,
            "recommendations": recommendations,
            "total_suggestions": len(recommendations),
        }

    except Exception as e:
        logger.error(f"Error getting field mapping recommendations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get mapping recommendations"
        )


@router.get("/confidence-metrics")
async def get_suggestion_confidence_metrics(
    import_id: Optional[str] = None,
    analyzer: AttributeAnalyzer = Depends(get_attribute_analyzer),
):
    """Get confidence metrics for AI suggestions."""
    try:
        from ..models.attribute_schemas import AttributeAnalysisRequest

        # Get analysis results
        request = AttributeAnalysisRequest(
            import_id=import_id,
            use_latest_import=import_id is None,
            include_crew_analysis=True,
        )

        analysis_result = await analyzer.analyze_critical_attributes(request)

        # Calculate confidence metrics
        suggestions = analysis_result.suggestions
        attributes = analysis_result.attributes

        if not suggestions and not attributes:
            return {
                "total_items": 0,
                "confidence_distribution": {},
                "average_confidence": 0.0,
            }

        # Confidence distribution for suggestions
        suggestion_confidences = [s.confidence_score for s in suggestions]
        attribute_confidences = [a.confidence for a in attributes]

        all_confidences = suggestion_confidences + attribute_confidences

        # Calculate distribution
        high_confidence = len([c for c in all_confidences if c >= 0.8])
        medium_confidence = len([c for c in all_confidences if 0.5 <= c < 0.8])
        low_confidence = len([c for c in all_confidences if c < 0.5])

        avg_confidence = (
            sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        )

        return {
            "total_items": len(all_confidences),
            "confidence_distribution": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence,
            },
            "average_confidence": avg_confidence,
            "suggestion_count": len(suggestions),
            "attribute_count": len(attributes),
            "analysis_mode": analysis_result.execution_mode,
        }

    except Exception as e:
        logger.error(f"Error getting confidence metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get confidence metrics")
