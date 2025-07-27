"""
Agent Tools for Agentic Memory and Asset Enrichment

This module provides CrewAI tools that enable agents to:
1. Search discovered patterns for reasoning evidence
2. Query asset data with context awareness
3. Store new pattern discoveries
4. Learn from previous enrichment decisions

These tools replace rule-based logic with true agent reasoning,
honoring the principle: "ALL intelligence comes from CrewAI agents"
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, **kwargs):
            pass


try:
    from app.core.database import AsyncSessionLocal
    from app.models.agent_memory import (
        PatternType,
    )
    from app.models.asset import Asset
    from app.services.agentic_memory import MemoryQuery, ThreeTierMemoryManager

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class PatternSearchTool(BaseTool):
    """
    Tool for agents to search discovered patterns for evidence related to their hypothesis

    This tool enables agents to:
    - Search existing patterns by type, confidence, or content
    - Find evidence to support their reasoning
    - Learn from previous agent discoveries
    - Build upon validated patterns
    """

    def __init__(self, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        super().__init__(
            name="pattern_search",
            description="""Search discovered patterns for evidence related to your hypothesis.
Use this tool when you need to find patterns that support your analysis of assets.

Input should be a JSON object with:
- query: string describing what pattern evidence you're looking for
- pattern_types: list of pattern types to search (optional)
- min_confidence: minimum confidence threshold (0.0 to 1.0, default 0.6)
- validated_only: whether to only search human-validated patterns (default false)

Example: {"query": "database business value indicators",
                "pattern_types": ["business_value_indicator"], "min_confidence": 0.7}""",
        )

        # Store context after super init
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)

    def _run(self, input_data: str) -> str:
        """Search patterns based on agent query"""
        if not DATABASE_AVAILABLE:
            return "Pattern search not available - database not connected"

        try:
            import json

            params = (
                json.loads(input_data) if isinstance(input_data, str) else input_data
            )

            # Extract search parameters
            query_text = params.get("query", "")
            pattern_types_str = params.get("pattern_types", [])
            min_confidence = params.get("min_confidence", 0.6)
            validated_only = params.get("validated_only", False)

            # Convert pattern type strings to enums
            pattern_types = []
            if pattern_types_str:
                for pt_str in pattern_types_str:
                    try:
                        pattern_types.append(PatternType(pt_str))
                    except ValueError:
                        logger.warning(f"Unknown pattern type: {pt_str}")

            # Create memory query
            memory_query = MemoryQuery(
                query_text=query_text,
                memory_tiers=["semantic"],
                pattern_types=pattern_types,
                min_confidence=min_confidence,
                validated_only=validated_only,
                max_results=10,
            )

            # Search patterns
            import asyncio

            results = asyncio.run(self.memory_manager.query_memory(memory_query))

            if not results:
                return f"No patterns found matching query: {query_text}"

            # Format results for agent consumption
            pattern_summaries = []
            for result in results:
                if result.tier == "semantic":
                    pattern = result.content
                    summary = {
                        "pattern_name": pattern["name"],
                        "pattern_type": pattern["type"],
                        "description": pattern["description"],
                        "confidence": pattern["confidence"],
                        "validated": pattern["validated"],
                        "evidence_count": pattern["evidence_count"],
                        "pattern_logic": pattern["pattern_data"],
                    }
                    pattern_summaries.append(summary)

            response = {
                "found_patterns": len(pattern_summaries),
                "patterns": pattern_summaries[:5],  # Limit to top 5 for readability
                "search_summary": (
                    f"Found {len(pattern_summaries)} patterns matching '{query_text}' "
                    f"with confidence >= {min_confidence}"
                ),
            }

            return json.dumps(response, indent=2)

        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return f"Pattern search error: {str(e)}"


class AssetDataQueryTool(BaseTool):
    """
    Tool for agents to query asset data with context awareness

    This tool enables agents to:
    - Search assets by various criteria
    - Find similar assets for pattern recognition
    - Access multi-tenant isolated data
    - Gather evidence for enrichment decisions
    """

    def __init__(self, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        super().__init__(
            name="asset_data_query",
            description="""Query asset data to gather evidence for your analysis.
Use this tool when you need to examine assets to support your reasoning.

Input should be a JSON object with:
- asset_type: filter by asset type (optional)
- technology_stack: filter by technology (optional)
- environment: filter by environment (optional)
- business_criticality: filter by criticality (optional)
- limit: maximum number of results (default 10)
- include_fields: list of specific fields to include in results

Example: {"asset_type": "database", "environment": "production", "limit": 5,
"include_fields": ["name", "technology_stack", "business_criticality"]}""",
        )

        # Store context after super init
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    def _run(self, input_data: str) -> str:
        """Query assets based on agent criteria"""
        if not DATABASE_AVAILABLE:
            return "Asset query not available - database not connected"

        try:
            import json

            params = (
                json.loads(input_data) if isinstance(input_data, str) else input_data
            )

            # Extract query parameters
            asset_type = params.get("asset_type")
            technology_stack = params.get("technology_stack")
            environment = params.get("environment")
            business_criticality = params.get("business_criticality")
            limit = params.get("limit", 10)
            include_fields = params.get(
                "include_fields",
                [
                    "name",
                    "asset_type",
                    "technology_stack",
                    "environment",
                    "business_criticality",
                ],
            )

            import asyncio

            return asyncio.run(
                self._query_assets_async(
                    asset_type,
                    technology_stack,
                    environment,
                    business_criticality,
                    limit,
                    include_fields,
                )
            )

        except Exception as e:
            logger.error(f"Asset query failed: {e}")
            return f"Asset query error: {str(e)}"

    async def _query_assets_async(
        self,
        asset_type,
        technology_stack,
        environment,
        business_criticality,
        limit,
        include_fields,
    ):
        """Async asset query implementation"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select

            # Build query with multi-tenant filtering
            query = select(Asset).where(
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
            )

            # Apply filters
            if asset_type:
                query = query.where(Asset.asset_type == asset_type)
            if technology_stack:
                query = query.where(
                    Asset.technology_stack.ilike(f"%{technology_stack}%")
                )
            if environment:
                query = query.where(Asset.environment == environment)
            if business_criticality:
                query = query.where(Asset.business_criticality == business_criticality)

            # Apply limit
            query = query.limit(limit)

            # Execute query
            result = await session.execute(query)
            assets = result.scalars().all()

            if not assets:
                return "No assets found matching the specified criteria"

            # Format results
            asset_data = []
            for asset in assets:
                asset_dict = {}
                for field in include_fields:
                    if hasattr(asset, field):
                        value = getattr(asset, field)
                        # Convert UUID to string for JSON serialization
                        if hasattr(value, "hex"):
                            value = str(value)
                        asset_dict[field] = value
                asset_data.append(asset_dict)

            response = {
                "found_assets": len(asset_data),
                "assets": asset_data,
                "query_summary": f"Found {len(asset_data)} assets matching criteria",
            }

            import json

            return json.dumps(response, indent=2, default=str)


class PatternRecordingTool(BaseTool):
    """
    Tool for agents to record new pattern discoveries

    This tool enables agents to:
    - Store patterns they discover during analysis
    - Build institutional memory for future reasoning
    - Record confidence levels and evidence
    - Enable pattern validation workflows
    """

    def __init__(
        self,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        agent_name: str,
        flow_id: Optional[uuid.UUID] = None,
    ):
        super().__init__(
            name="pattern_recording",
            description="""Record a new pattern you've discovered during asset analysis.
Use this tool when you identify a repeatable pattern that could help future analysis.

Input should be a JSON object with:
- pattern_type: type of pattern (e.g., 'business_value_indicator', 'risk_factor')
- pattern_name: descriptive name for the pattern
- pattern_description: detailed description of when this pattern applies
- pattern_logic: the actual pattern rules/criteria as a JSON object
- confidence_score: your confidence in this pattern (0.0 to 1.0)
- evidence_assets: list of asset IDs that support this pattern (optional)

Example: {"pattern_type": "business_value_indicator",
"pattern_name": "Production Database Critical Business Value",
"pattern_description": "Production databases with high utilization indicate critical business value",
"pattern_logic": {"environment": "production", "asset_type": "database",
"cpu_utilization_percent": ">= 70"}, "confidence_score": 0.85}""",
        )

        # Store context after super init
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.agent_name = agent_name
        self.flow_id = flow_id
        self.memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)

    def _run(self, input_data: str) -> str:
        """Record a new pattern discovery"""
        if not DATABASE_AVAILABLE:
            return "Pattern recording not available - database not connected"

        try:
            import json

            params = (
                json.loads(input_data) if isinstance(input_data, str) else input_data
            )

            # Extract pattern parameters
            pattern_type_str = params.get("pattern_type")
            pattern_name = params.get("pattern_name")
            pattern_description = params.get("pattern_description")
            pattern_logic = params.get("pattern_logic", {})
            confidence_score = params.get("confidence_score", 0.7)
            evidence_assets_str = params.get("evidence_assets", [])

            # Validate required fields
            if not all([pattern_type_str, pattern_name, pattern_description]):
                return (
                    "Error: pattern_type, pattern_name, and pattern_description "
                    "are required"
                )

            # Convert pattern type string to enum
            try:
                pattern_type = PatternType(pattern_type_str)
            except ValueError:
                valid_types = [pt.value for pt in PatternType]
                return f"Error: Unknown pattern type '{pattern_type_str}'. Valid types: {valid_types}"

            # Convert evidence asset IDs
            evidence_assets = []
            for asset_id_str in evidence_assets_str:
                try:
                    evidence_assets.append(uuid.UUID(asset_id_str))
                except ValueError:
                    logger.warning(f"Invalid asset ID format: {asset_id_str}")

            # Store pattern
            import asyncio

            pattern = asyncio.run(
                self.memory_manager.store_pattern_discovery(
                    agent_name=self.agent_name,
                    pattern_type=pattern_type,
                    pattern_name=pattern_name,
                    pattern_description=pattern_description,
                    pattern_logic=pattern_logic,
                    confidence_score=confidence_score,
                    evidence_assets=evidence_assets,
                    flow_id=self.flow_id,
                )
            )

            if pattern:
                response = {
                    "status": "success",
                    "pattern_id": str(pattern.id),
                    "message": f"Pattern '{pattern_name}' recorded successfully with confidence {confidence_score}",
                    "next_steps": "Pattern is pending validation and will be available for future agent reasoning",
                }
                return json.dumps(response, indent=2)
            else:
                return "Error: Failed to record pattern - database operation failed"

        except Exception as e:
            logger.error(f"Pattern recording failed: {e}")
            return f"Pattern recording error: {str(e)}"


class AssetEnrichmentTool(BaseTool):
    """
    Tool for agents to enrich assets with business intelligence

    This tool enables agents to:
    - Update asset business value scores based on reasoning
    - Set risk assessments and modernization potential
    - Record their reasoning for audit and learning
    - Update enrichment status tracking
    """

    def __init__(
        self, client_account_id: uuid.UUID, engagement_id: uuid.UUID, agent_name: str
    ):
        super().__init__(
            name="asset_enrichment",
            description="""Enrich an asset with business intelligence based on your analysis.
Use this tool to update asset fields with your reasoned conclusions.

Input should be a JSON object with:
- asset_id: UUID of the asset to enrich
- business_value_score: business value score 1-10 (optional)
- risk_assessment: risk level 'low', 'medium', 'high', 'critical' (optional)
- modernization_potential: potential 'low', 'medium', 'high' (optional)
- cloud_readiness_score: cloud readiness 0-100 (optional)
- reasoning: detailed explanation of your analysis and conclusions

Example: {"asset_id": "123e4567-e89b-12d3-a456-426614174000", "business_value_score": 8,
"risk_assessment": "medium", "modernization_potential": "high",
"reasoning": "Production database with high utilization serving critical customer applications"}""",
        )

        # Store context after super init
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.agent_name = agent_name

    def _run(self, input_data: str) -> str:
        """Enrich asset with agent reasoning"""
        if not DATABASE_AVAILABLE:
            return "Asset enrichment not available - database not connected"

        try:
            import json

            params = (
                json.loads(input_data) if isinstance(input_data, str) else input_data
            )

            # Extract enrichment parameters
            asset_id_str = params.get("asset_id")
            business_value_score = params.get("business_value_score")
            risk_assessment = params.get("risk_assessment")
            modernization_potential = params.get("modernization_potential")
            cloud_readiness_score = params.get("cloud_readiness_score")
            reasoning = params.get("reasoning", "")

            # Validate asset ID
            if not asset_id_str:
                return "Error: asset_id is required"

            try:
                asset_id = uuid.UUID(asset_id_str)
            except ValueError:
                return f"Error: Invalid asset ID format: {asset_id_str}"

            # Validate score ranges
            if business_value_score is not None and not (
                1 <= business_value_score <= 10
            ):
                return "Error: business_value_score must be between 1 and 10"

            if cloud_readiness_score is not None and not (
                0 <= cloud_readiness_score <= 100
            ):
                return "Error: cloud_readiness_score must be between 0 and 100"

            # Validate categorical values
            valid_risk_levels = ["low", "medium", "high", "critical"]
            if risk_assessment and risk_assessment not in valid_risk_levels:
                return f"Error: risk_assessment must be one of {valid_risk_levels}"

            valid_modernization_levels = ["low", "medium", "high"]
            if (
                modernization_potential
                and modernization_potential not in valid_modernization_levels
            ):
                return f"Error: modernization_potential must be one of {valid_modernization_levels}"

            # Perform enrichment
            import asyncio

            result = asyncio.run(
                self._enrich_asset_async(
                    asset_id,
                    business_value_score,
                    risk_assessment,
                    modernization_potential,
                    cloud_readiness_score,
                    reasoning,
                )
            )

            return result

        except Exception as e:
            logger.error(f"Asset enrichment failed: {e}")
            return f"Asset enrichment error: {str(e)}"

    async def _enrich_asset_async(
        self,
        asset_id,
        business_value_score,
        risk_assessment,
        modernization_potential,
        cloud_readiness_score,
        reasoning,
    ):
        """Async asset enrichment implementation"""
        async with AsyncSessionLocal() as session:
            # Find asset with multi-tenant filtering
            asset = await session.get(Asset, asset_id)

            if not asset:
                return f"Error: Asset {asset_id} not found"

            # Verify multi-tenant access
            if (
                asset.client_account_id != self.client_account_id
                or asset.engagement_id != self.engagement_id
            ):
                return f"Error: Asset {asset_id} not accessible in current context"

            # Update enrichment fields
            changes_made = []

            if business_value_score is not None:
                asset.business_value_score = business_value_score
                changes_made.append(f"business_value_score: {business_value_score}")

            if risk_assessment:
                asset.risk_assessment = risk_assessment
                changes_made.append(f"risk_assessment: {risk_assessment}")

            if modernization_potential:
                asset.modernization_potential = modernization_potential
                changes_made.append(
                    f"modernization_potential: {modernization_potential}"
                )

            if cloud_readiness_score is not None:
                asset.cloud_readiness_score = cloud_readiness_score
                changes_made.append(f"cloud_readiness_score: {cloud_readiness_score}")

            # Update enrichment metadata
            asset.enrichment_reasoning = reasoning
            asset.last_enriched_at = datetime.utcnow()
            asset.last_enriched_by_agent = self.agent_name
            asset.enrichment_status = "agent_enriched"

            # Commit changes
            await session.commit()

            response = {
                "status": "success",
                "asset_id": str(asset_id),
                "asset_name": asset.name,
                "changes_made": changes_made,
                "enrichment_agent": self.agent_name,
                "enrichment_time": datetime.utcnow().isoformat(),
                "reasoning_recorded": bool(reasoning),
            }

            import json

            return json.dumps(response, indent=2)


def create_agent_tools(
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    agent_name: str,
    flow_id: Optional[uuid.UUID] = None,
) -> List[BaseTool]:
    """
    Create a complete set of agent tools for agentic asset enrichment

    Args:
        client_account_id: Multi-tenant client context
        engagement_id: Multi-tenant engagement context
        agent_name: Name of the agent using these tools
        flow_id: Optional flow context for pattern discovery

    Returns:
        List of configured agent tools
    """

    tools = []

    if CREWAI_TOOLS_AVAILABLE and DATABASE_AVAILABLE:
        try:
            tools.extend(
                [
                    PatternSearchTool(client_account_id, engagement_id),
                    AssetDataQueryTool(client_account_id, engagement_id),
                    PatternRecordingTool(
                        client_account_id, engagement_id, agent_name, flow_id
                    ),
                    AssetEnrichmentTool(client_account_id, engagement_id, agent_name),
                ]
            )
            logger.info(f"✅ Created {len(tools)} agent tools for {agent_name}")
        except Exception as e:
            logger.error(f"Failed to create agent tools: {e}")
            logger.warning("Agent tools not available - creation failed")
    else:
        logger.warning("Agent tools not available - missing dependencies")

    return tools
