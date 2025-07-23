"""
Agentic Asset Enrichment - Unified Intelligence Integration

This module orchestrates the complete agentic asset enrichment process by integrating:
1. BusinessValueAgent - for business value assessment and scoring
2. RiskAssessmentAgent - for security, operational, and compliance risk analysis
3. ModernizationAgent - for cloud readiness and modernization strategy analysis

The enrichment process:
- Replaces rule-based asset categorization with true agent reasoning
- Uses the three-tier memory system for continuous learning
- Applies discovered patterns and records new insights
- Provides comprehensive asset intelligence for migration planning

This module integrates directly with the UnifiedDiscoveryFlow's data cleansing phase
to provide intelligent asset analysis instead of basic data processing.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Import memory management
from app.services.agentic_memory import ThreeTierMemoryManager

from .agent_reasoning_patterns import AgentReasoningEngine

# Import agentic intelligence modules
from .business_value_agent import BusinessValueAgent
from .modernization_agent import ModernizationAgent
from .risk_assessment_agent import RiskAssessmentAgent

logger = logging.getLogger(__name__)


class AgenticAssetEnrichment:
    """
    Unified agentic asset enrichment orchestrator that coordinates all three intelligence agents.

    This class:
    - Orchestrates BusinessValue, Risk, and Modernization agents
    - Manages parallel execution for performance optimization
    - Consolidates agent insights into comprehensive asset profiles
    - Integrates with the three-tier memory system for learning
    - Provides fallback mechanisms for robust operation
    """

    def __init__(
        self,
        crewai_service,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        flow_id: Optional[uuid.UUID] = None,
    ):
        self.crewai_service = crewai_service
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_id = flow_id

        # Initialize memory system
        self.memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)

        # Initialize agent reasoning engine for fallbacks
        self.reasoning_engine = AgentReasoningEngine(
            self.memory_manager, client_account_id, engagement_id
        )

        # Initialize intelligence agents
        self.business_value_agent = BusinessValueAgent(
            crewai_service, client_account_id, engagement_id, flow_id
        )

        self.risk_assessment_agent = RiskAssessmentAgent(
            crewai_service, client_account_id, engagement_id, flow_id
        )

        self.modernization_agent = ModernizationAgent(
            crewai_service, client_account_id, engagement_id, flow_id
        )

        logger.info(
            "✅ Agentic Asset Enrichment orchestrator initialized with 3 intelligence agents"
        )

    async def enrich_asset_complete(
        self, asset_data: Dict[str, Any], enable_parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete agentic enrichment of a single asset using all three agents.

        Args:
            asset_data: Asset data to enrich
            enable_parallel: Whether to run agents in parallel (default: True)

        Returns:
            Fully enriched asset with business value, risk, and modernization analysis
        """

        asset_name = asset_data.get("name", "unknown")
        logger.info(f"🧠 Starting complete agentic enrichment for asset: {asset_name}")

        try:
            if enable_parallel:
                # Run all three agents in parallel for performance
                business_analysis, risk_analysis, modernization_analysis = (
                    await self._run_agents_parallel(asset_data)
                )
            else:
                # Run agents sequentially (safer but slower)
                business_analysis, risk_analysis, modernization_analysis = (
                    await self._run_agents_sequential(asset_data)
                )

            # Consolidate all agent insights
            enriched_asset = self._consolidate_agent_insights(
                asset_data, business_analysis, risk_analysis, modernization_analysis
            )

            # Calculate overall enrichment score
            enriched_asset["overall_enrichment_score"] = self._calculate_overall_score(
                business_analysis, risk_analysis, modernization_analysis
            )

            # Add enrichment metadata
            enriched_asset.update(
                {
                    "enrichment_status": "agentic_complete",
                    "enrichment_method": "three_agent_analysis",
                    "last_enriched_at": datetime.utcnow().isoformat(),
                    "enrichment_agents": [
                        "BusinessValueAgent",
                        "RiskAssessmentAgent",
                        "ModernizationAgent",
                    ],
                    "memory_patterns_discovered": self._count_patterns_discovered(
                        business_analysis, risk_analysis, modernization_analysis
                    ),
                    "agentic_confidence_score": self._calculate_confidence_score(
                        business_analysis, risk_analysis, modernization_analysis
                    ),
                }
            )

            logger.info(f"✅ Complete agentic enrichment completed for {asset_name}")
            logger.info(
                f"   - Business Value: {business_analysis.get('business_value_score', 'N/A')}/10"
            )
            logger.info(
                f"   - Risk Level: {risk_analysis.get('risk_assessment', 'N/A')}"
            )
            logger.info(
                f"   - Cloud Readiness: {modernization_analysis.get('cloud_readiness_score', 'N/A')}/100"
            )

            return enriched_asset

        except Exception as e:
            logger.error(f"❌ Complete agentic enrichment failed for {asset_name}: {e}")
            return self._create_fallback_enrichment(asset_data, str(e))

    async def enrich_assets_batch(
        self,
        assets: List[Dict[str, Any]],
        batch_size: int = 5,
        enable_parallel: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Enrich multiple assets in batches for optimal performance.

        Args:
            assets: List of assets to enrich
            batch_size: Number of assets to process simultaneously
            enable_parallel: Whether to use parallel agent execution

        Returns:
            List of enriched assets
        """

        logger.info(
            f"🧠 Starting batch agentic enrichment for {len(assets)} assets (batch size: {batch_size})"
        )

        enriched_assets = []

        # Process assets in batches
        for i in range(0, len(assets), batch_size):
            batch = assets[i : i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (len(assets) + batch_size - 1) // batch_size

            logger.info(
                f"📦 Processing batch {batch_number}/{total_batches} ({len(batch)} assets)"
            )

            # Process batch concurrently
            batch_tasks = [
                self.enrich_asset_complete(asset, enable_parallel) for asset in batch
            ]

            try:
                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                # Process results and handle exceptions
                for asset, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(
                            f"❌ Asset enrichment failed for {asset.get('name')}: {result}"
                        )
                        enriched_assets.append(
                            self._create_fallback_enrichment(asset, str(result))
                        )
                    else:
                        enriched_assets.append(result)

                logger.info(f"✅ Batch {batch_number} completed")

            except Exception as e:
                logger.error(f"❌ Batch {batch_number} failed: {e}")
                # Add fallback enrichments for failed batch
                for asset in batch:
                    enriched_assets.append(
                        self._create_fallback_enrichment(asset, str(e))
                    )

        success_count = sum(
            1
            for asset in enriched_assets
            if asset.get("enrichment_status") == "agentic_complete"
        )
        logger.info(
            f"✅ Batch enrichment completed: {success_count}/{len(assets)} assets successfully enriched"
        )

        return enriched_assets

    async def _run_agents_parallel(
        self, asset_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Run all three agents in parallel for performance"""

        logger.debug(f"🔀 Running agents in parallel for {asset_data.get('name')}")

        # Create tasks for all three agents
        business_task = self.business_value_agent.analyze_asset_business_value(
            asset_data
        )
        risk_task = self.risk_assessment_agent.analyze_asset_risk(asset_data)
        modernization_task = self.modernization_agent.analyze_modernization_potential(
            asset_data
        )

        # Execute all agents concurrently
        results = await asyncio.gather(
            business_task, risk_task, modernization_task, return_exceptions=True
        )

        # Handle any agent failures
        business_analysis = (
            results[0]
            if not isinstance(results[0], Exception)
            else self._create_fallback_business_analysis(asset_data)
        )
        risk_analysis = (
            results[1]
            if not isinstance(results[1], Exception)
            else self._create_fallback_risk_analysis(asset_data)
        )
        modernization_analysis = (
            results[2]
            if not isinstance(results[2], Exception)
            else self._create_fallback_modernization_analysis(asset_data)
        )

        return business_analysis, risk_analysis, modernization_analysis

    async def _run_agents_sequential(
        self, asset_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Run agents sequentially (safer but slower)"""

        logger.debug(f"🔄 Running agents sequentially for {asset_data.get('name')}")

        # Business Value Analysis
        try:
            business_analysis = (
                await self.business_value_agent.analyze_asset_business_value(asset_data)
            )
        except Exception as e:
            logger.warning(f"Business value analysis failed: {e}")
            business_analysis = self._create_fallback_business_analysis(asset_data)

        # Risk Assessment
        try:
            risk_analysis = await self.risk_assessment_agent.analyze_asset_risk(
                asset_data
            )
        except Exception as e:
            logger.warning(f"Risk assessment failed: {e}")
            risk_analysis = self._create_fallback_risk_analysis(asset_data)

        # Modernization Analysis
        try:
            modernization_analysis = (
                await self.modernization_agent.analyze_modernization_potential(
                    asset_data
                )
            )
        except Exception as e:
            logger.warning(f"Modernization analysis failed: {e}")
            modernization_analysis = self._create_fallback_modernization_analysis(
                asset_data
            )

        return business_analysis, risk_analysis, modernization_analysis

    def _consolidate_agent_insights(
        self,
        asset_data: Dict[str, Any],
        business_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        modernization_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Consolidate insights from all three agents into a unified asset profile"""

        # Start with original asset data
        enriched_asset = {**asset_data}

        # Business Value Intelligence
        enriched_asset.update(
            {
                "business_value_score": business_analysis.get("business_value_score"),
                "business_value_reasoning": business_analysis.get("reasoning"),
                "business_value_confidence": business_analysis.get("confidence_level"),
                "business_value_recommendations": business_analysis.get(
                    "recommendations", []
                ),
            }
        )

        # Risk Intelligence
        enriched_asset.update(
            {
                "risk_assessment": risk_analysis.get("risk_assessment"),
                "security_risk_score": risk_analysis.get("security_risk_score"),
                "operational_risk_score": risk_analysis.get("operational_risk_score"),
                "compliance_risk_score": risk_analysis.get("compliance_risk_score"),
                "risk_analysis_reasoning": risk_analysis.get("primary_threats"),
                "vulnerability_summary": risk_analysis.get("vulnerability_summary"),
                "risk_mitigation_actions": risk_analysis.get("immediate_actions", []),
                "risk_recommendations": risk_analysis.get(
                    "longterm_recommendations", []
                ),
            }
        )

        # Modernization Intelligence
        enriched_asset.update(
            {
                "cloud_readiness_score": modernization_analysis.get(
                    "cloud_readiness_score"
                ),
                "modernization_potential": modernization_analysis.get(
                    "modernization_potential"
                ),
                "recommended_migration_strategy": modernization_analysis.get(
                    "recommended_strategy"
                ),
                "migration_effort_estimate": modernization_analysis.get(
                    "migration_effort"
                ),
                "architecture_assessment": modernization_analysis.get(
                    "architecture_assessment"
                ),
                "containerization_readiness": modernization_analysis.get(
                    "containerization_readiness"
                ),
                "modernization_recommendations": modernization_analysis.get(
                    "immediate_steps", []
                ),
                "migration_roadmap": modernization_analysis.get("migration_strategy"),
                "expected_modernization_benefits": modernization_analysis.get(
                    "expected_benefits", []
                ),
            }
        )

        # Generate comprehensive summary
        enriched_asset["agentic_intelligence_summary"] = (
            self._generate_intelligence_summary(
                business_analysis, risk_analysis, modernization_analysis
            )
        )

        return enriched_asset

    def _calculate_overall_score(
        self,
        business_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        modernization_analysis: Dict[str, Any],
    ) -> float:
        """Calculate an overall enrichment score combining all three dimensions"""

        # Normalize scores to 0-100 scale
        business_score = (business_analysis.get("business_value_score", 5) / 10) * 100

        # Risk score (inverted - lower risk = higher score)
        risk_level = risk_analysis.get("risk_assessment", "medium")
        risk_score_map = {"low": 90, "medium": 60, "high": 30, "critical": 10}
        risk_score = risk_score_map.get(risk_level, 60)

        modernization_score = modernization_analysis.get("cloud_readiness_score", 50)

        # Weighted average (business value 40%, risk 30%, modernization 30%)
        overall_score = (
            (business_score * 0.4) + (risk_score * 0.3) + (modernization_score * 0.3)
        )

        return round(overall_score, 1)

    def _count_patterns_discovered(
        self,
        business_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        modernization_analysis: Dict[str, Any],
    ) -> int:
        """Count total patterns discovered across all agents"""

        count = 0
        count += (
            business_analysis.get("patterns_discovered", 0)
            if isinstance(business_analysis.get("patterns_discovered"), int)
            else 0
        )
        count += (
            risk_analysis.get("patterns_discovered", 0)
            if isinstance(risk_analysis.get("patterns_discovered"), int)
            else 0
        )
        count += (
            modernization_analysis.get("patterns_discovered", 0)
            if isinstance(modernization_analysis.get("patterns_discovered"), int)
            else 0
        )

        return count

    def _calculate_confidence_score(
        self,
        business_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        modernization_analysis: Dict[str, Any],
    ) -> float:
        """Calculate overall confidence score across all agent analyses"""

        confidence_scores = []

        # Convert confidence levels to numeric scores
        confidence_map = {"high": 0.9, "medium": 0.6, "low": 0.3}

        business_conf = confidence_map.get(
            business_analysis.get("confidence_level", "medium"), 0.6
        )
        risk_conf = confidence_map.get(
            risk_analysis.get("confidence_level", "medium"), 0.6
        )
        modernization_conf = confidence_map.get(
            modernization_analysis.get("technical_confidence", "medium"), 0.6
        )

        confidence_scores = [business_conf, risk_conf, modernization_conf]

        return round(sum(confidence_scores) / len(confidence_scores), 2)

    def _generate_intelligence_summary(
        self,
        business_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        modernization_analysis: Dict[str, Any],
    ) -> str:
        """Generate a comprehensive intelligence summary"""

        business_score = business_analysis.get("business_value_score", 5)
        risk_level = risk_analysis.get("risk_assessment", "medium")
        cloud_readiness = modernization_analysis.get("cloud_readiness_score", 50)

        summary = f"Asset analysis complete - Business Value: {business_score}/10, "
        summary += f"Risk Level: {risk_level.title()}, "
        summary += f"Cloud Readiness: {cloud_readiness}/100. "

        # Add key insights
        if business_score >= 8:
            summary += (
                "High business value asset requiring careful migration planning. "
            )

        if risk_level in ["high", "critical"]:
            summary += "Significant security/operational risks identified requiring immediate attention. "

        if cloud_readiness >= 80:
            summary += "Excellent modernization candidate with high cloud readiness."
        elif cloud_readiness >= 60:
            summary += "Good modernization potential with moderate effort required."
        else:
            summary += (
                "Limited modernization readiness - consider lift-and-shift approach."
            )

        return summary

    # Fallback Methods

    def _create_fallback_enrichment(
        self, asset_data: Dict[str, Any], error_message: str
    ) -> Dict[str, Any]:
        """Create fallback enrichment when all agents fail"""

        enriched_asset = {**asset_data}
        enriched_asset.update(
            {
                "business_value_score": 5,
                "risk_assessment": "medium",
                "cloud_readiness_score": 50,
                "enrichment_status": "fallback",
                "enrichment_error": error_message,
                "enrichment_method": "fallback_defaults",
                "last_enriched_at": datetime.utcnow().isoformat(),
                "agentic_intelligence_summary": "Agentic analysis failed - using default assessments",
            }
        )

        return enriched_asset

    def _create_fallback_business_analysis(
        self, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback business value analysis"""
        return {
            "business_value_score": 5,
            "confidence_level": "low",
            "reasoning": "Business value analysis failed - using default medium value",
            "recommendations": ["Standard migration approach"],
        }

    def _create_fallback_risk_analysis(
        self, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback risk analysis"""
        return {
            "risk_assessment": "medium",
            "security_risk_score": 5,
            "operational_risk_score": 5,
            "compliance_risk_score": 5,
            "confidence_level": "low",
            "primary_threats": "Risk analysis failed - using default medium risk",
            "immediate_actions": ["Review security configuration"],
        }

    def _create_fallback_modernization_analysis(
        self, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback modernization analysis"""
        return {
            "cloud_readiness_score": 50,
            "modernization_potential": "medium",
            "recommended_strategy": "lift-and-shift",
            "migration_effort": "medium",
            "technical_confidence": "low",
            "architecture_assessment": "Modernization analysis failed - using default assessment",
        }


# Main Integration Functions for Discovery Flow


async def enrich_assets_with_agentic_intelligence(
    assets: List[Dict[str, Any]],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None,
    batch_size: int = 3,
    enable_parallel_agents: bool = True,
) -> List[Dict[str, Any]]:
    """
    Main function to enrich assets with complete agentic intelligence.

    This function replaces rule-based asset categorization in the discovery flow
    with true agent reasoning using BusinessValue, Risk, and Modernization agents.

    Args:
        assets: List of assets to enrich
        crewai_service: CrewAI service instance
        client_account_id: Multi-tenant client context
        engagement_id: Multi-tenant engagement context
        flow_id: Optional flow context for pattern discovery
        batch_size: Number of assets to process simultaneously
        enable_parallel_agents: Whether to run agents in parallel per asset

    Returns:
        List of assets enriched with agentic intelligence
    """

    logger.info(
        f"🧠 Starting complete agentic asset enrichment for {len(assets)} assets"
    )

    # Initialize the agentic enrichment orchestrator
    enrichment_orchestrator = AgenticAssetEnrichment(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    # Perform batch enrichment
    enriched_assets = await enrichment_orchestrator.enrich_assets_batch(
        assets=assets, batch_size=batch_size, enable_parallel=enable_parallel_agents
    )

    # Log final statistics
    successful_enrichments = sum(
        1
        for asset in enriched_assets
        if asset.get("enrichment_status") == "agentic_complete"
    )
    logger.info("✅ Agentic asset enrichment completed:")
    logger.info(f"   - Total assets: {len(enriched_assets)}")
    logger.info(f"   - Successful enrichments: {successful_enrichments}")
    logger.info(
        f"   - Success rate: {(successful_enrichments/len(enriched_assets)*100):.1f}%"
    )

    return enriched_assets


async def enrich_single_asset_with_agentic_intelligence(
    asset_data: Dict[str, Any],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    Enrich a single asset with complete agentic intelligence.

    This function provides the full three-agent analysis for a single asset,
    useful for detailed analysis or API endpoints.
    """

    enrichment_orchestrator = AgenticAssetEnrichment(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    return await enrichment_orchestrator.enrich_asset_complete(asset_data)
