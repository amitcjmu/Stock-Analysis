"""
Discovery flow service for critical attributes analysis
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport, ImportFieldMapping
from .utils import agent_determine_criticality

logger = logging.getLogger(__name__)


async def get_agentic_critical_attributes(
    context: RequestContext, data_import: DataImport, db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    Get critical attributes from agentic discovery flow results.

    This function checks if the discovery flow has already analyzed the data
    and determined critical attributes using agent intelligence.
    """
    try:
        # Use the proper CrewAI Flow service instead of modular approach
        from app.services.crewai_flow_service import CrewAIFlowService

        # Check if there are existing discovery flow results for this import
        CrewAIFlowService()

        # Get the discovery flow for this data import
        discovery_flow = await _find_discovery_flow(data_import, db)

        if not discovery_flow:
            logger.warning("⚠️ No discovery flow found through any lookup method")
            return None

        logger.info(f"🤖 Found discovery flow: {discovery_flow.flow_id}")

        # Get field mappings from discovery flow or database
        field_mappings, confidence_scores = await _get_field_mappings(
            discovery_flow, data_import, db
        )

        if not field_mappings:
            logger.warning("⚠️ No field mappings available from any source")
            return None

        # Calculate enhanced analysis and build response
        return await _build_critical_attributes_response(
            field_mappings, confidence_scores, discovery_flow
        )

    except ImportError:
        logger.warning(
            "Discovery flow service not available - falling back to basic analysis"
        )
    except Exception as e:
        logger.error(f"Failed to get agentic results: {e}")

    return None


async def _find_discovery_flow(data_import: DataImport, db: AsyncSession):
    """Find discovery flow using multiple lookup methods"""
    from app.models.discovery_flow import DiscoveryFlow

    # First try direct data_import_id lookup
    flow_query = select(DiscoveryFlow).where(
        DiscoveryFlow.data_import_id == data_import.id
    )
    flow_result = await db.execute(flow_query)
    discovery_flow = flow_result.scalar_one_or_none()

    if discovery_flow:
        return discovery_flow

    # If not found by data_import_id, try lookup through master flow relationship
    if data_import.master_flow_id:
        logger.info(
            f"🔍 Discovery flow not found by data_import_id, trying master flow lookup for: "
            f"{data_import.master_flow_id}"
        )

        # Look for discovery flow with matching master_flow_id
        master_flow_query = select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == data_import.master_flow_id
        )
        master_flow_result = await db.execute(master_flow_query)
        discovery_flow = master_flow_result.scalar_one_or_none()

        if discovery_flow:
            logger.info(
                f"✅ Found discovery flow through master flow relationship: {discovery_flow.flow_id}"
            )
            return discovery_flow

        # Additional fallback: Look for discovery flows through configuration
        discovery_flow = await _find_discovery_flow_by_config(data_import, db)
        if discovery_flow:
            return discovery_flow

    return None


async def _find_discovery_flow_by_config(data_import: DataImport, db: AsyncSession):
    """Find discovery flow through configuration-based lookup"""
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

    logger.info(
        "🔍 No discovery flow found by master_flow_id, trying configuration-based lookup"
    )

    # Use parameterized query to prevent SQL injection
    config_query = (
        select(CrewAIFlowStateExtensions)
        .where(sql_text("flow_configuration::text LIKE :search_pattern"))
        .params(search_pattern=f"%{data_import.id}%")
    )
    config_result = await db.execute(config_query)
    master_flows_with_import = config_result.scalars().all()

    for master_flow in master_flows_with_import:
        # Check if there's a discovery flow linked to this master flow
        linked_flow_query = select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == master_flow.flow_id
        )
        linked_flow_result = await db.execute(linked_flow_query)
        discovery_flow = linked_flow_result.scalar_one_or_none()

        if discovery_flow:
            logger.info(
                f"✅ Found discovery flow through configuration-based lookup: {discovery_flow.flow_id}"
            )
            return discovery_flow

    return None


async def _get_field_mappings(
    discovery_flow, data_import: DataImport, db: AsyncSession
):
    """Get field mappings from JSON or database"""
    field_mappings = {}
    confidence_scores = {}

    if discovery_flow.field_mappings:
        field_mapping_data = discovery_flow.field_mappings
        # Check if field mappings are stored in the JSON structure
        if (
            isinstance(field_mapping_data, dict)
            and "field_mappings" in field_mapping_data
        ):
            field_mappings = field_mapping_data.get("field_mappings", {})
            confidence_scores = field_mapping_data.get("confidence_scores", {})
            logger.info("📊 Using field mappings from discovery flow JSON")
            return field_mappings, confidence_scores

    # If no field mappings from JSON, query the database
    logger.info("🔍 Querying import_field_mappings table for field mapping data")

    # Query field mappings from the database
    field_mappings_query = select(ImportFieldMapping).where(
        ImportFieldMapping.data_import_id == data_import.id
    )
    field_mappings_result = await db.execute(field_mappings_query)
    db_field_mappings = field_mappings_result.scalars().all()

    if db_field_mappings:
        logger.info(f"📊 Found {len(db_field_mappings)} field mappings in database")

        # Convert database mappings to the format expected by the rest of the code
        for mapping in db_field_mappings:
            # Only include mapped fields (not UNMAPPED ones)
            if mapping.target_field and mapping.target_field != "UNMAPPED":
                field_mappings[mapping.source_field] = mapping.target_field
                confidence_scores[mapping.source_field] = (
                    mapping.confidence_score or 0.7
                )

        logger.info(
            f"📊 Processed {len(field_mappings)} valid field mappings (excluding UNMAPPED)"
        )
    else:
        logger.warning("⚠️ No field mappings found in database")

    return field_mappings, confidence_scores


async def _build_critical_attributes_response(
    field_mappings: Dict[str, str], confidence_scores: Dict[str, float], discovery_flow
) -> Dict[str, Any]:
    """Build the critical attributes response structure"""
    # Calculate enhanced analysis based on available data
    enhanced_analysis = {
        "confidence": 0.8 if field_mappings else 0.0,
        "total_fields": len(field_mappings),
    }

    # If we have JSON metadata, use those values
    if discovery_flow.field_mappings and isinstance(
        discovery_flow.field_mappings, dict
    ):
        enhanced_analysis["confidence"] = discovery_flow.field_mappings.get(
            "confidence", enhanced_analysis["confidence"]
        )
        enhanced_analysis["total_fields"] = discovery_flow.field_mappings.get(
            "total_fields", enhanced_analysis["total_fields"]
        )

    # Use agent intelligence to determine criticality
    attributes_status = []

    for source_field, target_field in field_mappings.items():
        # Agent determines criticality based on learned patterns
        criticality_analysis = agent_determine_criticality(
            source_field, target_field, enhanced_analysis
        )

        attributes_status.append(
            {
                "name": target_field,
                "description": f"Agent-mapped from {source_field}",
                "category": criticality_analysis["category"],
                "required": criticality_analysis["required"],
                "status": "mapped",
                "mapped_to": source_field,
                "source_field": source_field,
                "confidence": confidence_scores.get(source_field, 0.85),
                "quality_score": criticality_analysis["quality_score"],
                "completeness_percentage": 100,
                "mapping_type": "agent_intelligent",
                "ai_suggestion": criticality_analysis["ai_reasoning"],
                "business_impact": criticality_analysis["business_impact"],
                "migration_critical": criticality_analysis["migration_critical"],
            }
        )

    # Calculate agent-driven statistics
    total_attributes = len(attributes_status)
    mapped_count = len([a for a in attributes_status if a["status"] == "mapped"])
    migration_critical_count = len(
        [a for a in attributes_status if a["migration_critical"]]
    )
    migration_critical_mapped = len(
        [
            a
            for a in attributes_status
            if a["migration_critical"] and a["status"] == "mapped"
        ]
    )

    overall_completeness = (
        round((mapped_count / total_attributes) * 100) if total_attributes > 0 else 0
    )
    avg_quality_score = (
        round(
            sum(a["quality_score"] for a in attributes_status) / len(attributes_status)
        )
        if attributes_status
        else 0
    )
    assessment_ready = migration_critical_mapped >= 3

    return {
        "attributes": attributes_status,
        "statistics": {
            "total_attributes": total_attributes,
            "mapped_count": mapped_count,
            "pending_count": 0,
            "unmapped_count": 0,
            "migration_critical_count": migration_critical_count,
            "migration_critical_mapped": migration_critical_mapped,
            "overall_completeness": overall_completeness,
            "avg_quality_score": avg_quality_score,
            "assessment_ready": assessment_ready,
        },
        "recommendations": {
            "next_priority": "Review agent-identified critical attributes and proceed with assessment",
            "assessment_readiness": (
                f"Agent analysis complete. {migration_critical_mapped} critical fields mapped."
            ),
            "quality_improvement": "AI agents have optimized field mappings based on learned patterns",
        },
        "agent_status": {
            "discovery_flow_active": False,
            "field_mapping_crew_status": "completed",
            "learning_system_status": "updated",
        },
        "agent_insights": {
            "field_mapping_confidence": enhanced_analysis.get("confidence", 0.85),
            "total_fields_analyzed": enhanced_analysis.get("total_fields", 0),
            "mapping_method": "agent_intelligent_mapping",
            "learning_patterns_used": True,
        },
        "last_updated": datetime.utcnow().isoformat(),
    }
