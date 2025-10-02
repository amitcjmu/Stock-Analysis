"""
Asset Intelligence and Validation Tools
Tools for gathering intelligence about assets including patterns and relationships.
"""

import logging
from typing import Any, Dict, List

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AssetIntelligenceInput(BaseModel):
    """Input schema for asset intelligence tool."""

    asset_id: str = Field(..., description="ID of the asset to analyze")
    asset_collection: List[Dict[str, Any]] = Field(
        ..., description="Collection of all assets for relationship analysis"
    )


class AssetIntelligenceTool(BaseTool):
    """
    CrewAI tool for gathering intelligence about assets.

    This tool must inherit from BaseTool to be compatible with CrewAI's Agent validation.
    It analyzes asset patterns, relationships, and provides intelligence for questionnaire generation.

    TODO: Future enhancement - delegate to Asset Intelligence Agent for agentic-first architecture
    """

    name: str = "asset_intelligence"
    description: str = (
        "Gather comprehensive intelligence about assets including patterns and relationships"
    )
    args_schema: type[BaseModel] = AssetIntelligenceInput

    def _run(
        self, asset_id: str, asset_collection: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Gather intelligence about an asset including patterns and relationships.

        Args:
            asset_id: ID of the asset to analyze
            asset_collection: Collection of all assets for relationship analysis

        Returns:
            Intelligence report about the asset
        """
        # Find the target asset
        target_asset = None
        for asset in asset_collection:
            if str(asset.get("asset_id", "")) == str(asset_id):
                target_asset = asset
                break

        if not target_asset:
            return {
                "asset_id": asset_id,
                "error": "Asset not found in collection",
                "intelligence": {},
            }

        # Find similar assets
        similar_assets = self._find_similar_assets(target_asset, asset_collection)

        # Identify common gaps
        common_gaps = self._identify_common_gaps(asset_collection)

        # Analyze migration patterns
        migration_patterns = self._analyze_migration_patterns(asset_collection)

        # Generate recommendations
        recommendations = self._recommend_questions(
            target_asset, similar_assets, common_gaps
        )

        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            target_asset, similar_assets, asset_collection
        )

        return {
            "asset_id": asset_id,
            "asset_type": target_asset.get("asset_type", "unknown"),
            "similar_assets": similar_assets,
            "common_gaps": common_gaps,
            "migration_patterns": migration_patterns,
            "recommendations": recommendations,
            "confidence_score": confidence_score,
            "intelligence_metadata": {
                "total_assets_analyzed": len(asset_collection),
                "similar_assets_found": len(similar_assets),
                "pattern_strength": len(migration_patterns),
            },
        }

    def _find_similar_assets(
        self, target_asset: Dict[str, Any], asset_collection: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find assets similar to the target asset."""
        similar_assets = []
        target_type = target_asset.get("asset_type", "").lower()
        target_tech_stack = target_asset.get("technology_stack", "").lower()

        for asset in asset_collection:
            if asset.get("asset_id") == target_asset.get("asset_id"):
                continue  # Skip self

            similarity_score = 0

            # Check asset type
            if asset.get("asset_type", "").lower() == target_type:
                similarity_score += 3

            # Check technology stack
            asset_tech_stack = asset.get("technology_stack", "").lower()
            if asset_tech_stack and target_tech_stack:
                if (
                    asset_tech_stack in target_tech_stack
                    or target_tech_stack in asset_tech_stack
                ):
                    similarity_score += 2

            # Check environment
            if asset.get("environment") == target_asset.get("environment"):
                similarity_score += 1

            # Only include assets with reasonable similarity
            if similarity_score >= 2:
                similar_assets.append(
                    {
                        "asset_id": asset.get("asset_id"),
                        "asset_name": asset.get("asset_name"),
                        "asset_type": asset.get("asset_type"),
                        "similarity_score": similarity_score,
                        "technology_stack": asset.get("technology_stack"),
                    }
                )

        # Sort by similarity score (descending) and limit to top 5
        similar_assets.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_assets[:5]

    def _identify_common_gaps(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Identify commonly missing fields across assets."""
        gap_counts = {}
        total_assets = len(assets)

        critical_fields = [
            "business_owner",
            "technical_owner",
            "six_r_strategy",
            "migration_complexity",
            "dependencies",
            "operating_system",
        ]

        for field in critical_fields:
            missing_count = 0
            for asset in assets:
                if not asset.get(field):
                    missing_count += 1

            if missing_count > 0:
                gap_counts[field] = {
                    "missing_count": missing_count,
                    "percentage": (missing_count / total_assets) * 100,
                    "priority": (
                        "high" if missing_count / total_assets > 0.5 else "medium"
                    ),
                }

        return gap_counts

    def _analyze_migration_patterns(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze migration patterns across assets."""
        patterns = {
            "strategies": {},
            "complexity_distribution": {},
            "technology_trends": {},
        }

        for asset in assets:
            # Track 6R strategies
            strategy = asset.get("six_r_strategy")
            if strategy:
                patterns["strategies"][strategy] = (
                    patterns["strategies"].get(strategy, 0) + 1
                )

            # Track complexity
            complexity = asset.get("migration_complexity")
            if complexity:
                patterns["complexity_distribution"][complexity] = (
                    patterns["complexity_distribution"].get(complexity, 0) + 1
                )

            # Track technology stacks
            tech_stack = asset.get("technology_stack")
            if tech_stack:
                patterns["technology_trends"][tech_stack] = (
                    patterns["technology_trends"].get(tech_stack, 0) + 1
                )

        return patterns

    def _recommend_questions(
        self,
        target_asset: Dict[str, Any],
        similar_assets: List[Dict[str, Any]],
        common_gaps: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Recommend specific questions based on intelligence."""
        recommendations = []

        # Recommend questions for common gaps
        for gap_field, gap_info in common_gaps.items():
            if gap_info["percentage"] > 30:  # If >30% of assets are missing this field
                recommendations.append(
                    {
                        "type": "common_gap",
                        "field": gap_field,
                        "reason": f"Missing in {gap_info['percentage']:.0f}% of similar assets",
                        "priority": gap_info["priority"],
                    }
                )

        # Recommend questions based on similar assets
        if similar_assets:
            recommendations.append(
                {
                    "type": "similarity_based",
                    "reason": f"Found {len(similar_assets)} similar assets for pattern analysis",
                    "similar_asset_types": list(
                        set(asset["asset_type"] for asset in similar_assets)
                    ),
                    "priority": "medium",
                }
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_confidence(
        self,
        target_asset: Dict[str, Any],
        similar_assets: List[Dict[str, Any]],
        all_assets: List[Dict[str, Any]],
    ) -> float:
        """Calculate confidence score for the analysis."""
        confidence_factors = []

        # Factor 1: Number of similar assets found
        if len(similar_assets) >= 3:
            confidence_factors.append(0.8)
        elif len(similar_assets) >= 1:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)

        # Factor 2: Data completeness of target asset
        required_fields = ["asset_name", "asset_type", "technology_stack"]
        completeness = sum(
            1 for field in required_fields if target_asset.get(field)
        ) / len(required_fields)
        confidence_factors.append(completeness)

        # Factor 3: Size of total asset collection
        collection_size_score = min(
            1.0, len(all_assets) / 50
        )  # Normalize to 1.0 at 50+ assets
        confidence_factors.append(collection_size_score)

        # Calculate weighted average
        return sum(confidence_factors) / len(confidence_factors)
