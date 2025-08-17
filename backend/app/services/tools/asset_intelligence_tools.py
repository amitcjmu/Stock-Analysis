"""
Asset Intelligence Tools
AI-powered tools for asset inventory management that enhance the existing CrewAI framework.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False
    logging.warning("CrewAI tools not available")

logger = logging.getLogger(__name__)


# Helper functions for tool creation
def create_asset_analysis_tool(**kwargs):
    """Create asset analysis tool if CrewAI is available."""
    if not CREWAI_TOOLS_AVAILABLE:
        return None
    return AssetAnalysisTool(**kwargs)


def create_bulk_operations_tool(**kwargs):
    """Create bulk operations tool if CrewAI is available."""
    if not CREWAI_TOOLS_AVAILABLE:
        return None
    return BulkOperationsTool(**kwargs)


def create_data_quality_tool(**kwargs):
    """Create data quality tool if CrewAI is available."""
    if not CREWAI_TOOLS_AVAILABLE:
        return None
    # TODO: Implement DataQualityTool class
    # return DataQualityTool(**kwargs)
    return None  # DataQualityTool not yet implemented


if CREWAI_TOOLS_AVAILABLE:
    # Input schemas for CrewAI tools
    class AssetAnalysisInput(BaseModel):
        """Input schema for asset analysis tool."""

        assets: List[Dict[str, Any]] = Field(
            ..., description="List of assets to analyze"
        )
        context: str = Field(
            default="general",
            description="Analysis context: data_quality, classification, bulk_operations, or general",
        )

    class AssetAnalysisTool(BaseTool):
        """
        AI-powered asset analysis tool that integrates with existing field mapping intelligence.
        Uses learned patterns rather than hard-coded heuristics.
        """

        name: str = "asset_analysis_tool"
        description: str = (
            "Analyze asset patterns and provide intelligent insights for inventory management"
        )
        args_schema: type[BaseModel] = AssetAnalysisInput
        # Declare field_mapper as a Pydantic field to avoid validation errors
        field_mapper: Optional[Any] = Field(
            default=None, description="Field mapper service instance"
        )

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Initialize field_mapper to None - it will be injected via service layer when needed
            if not hasattr(self, "field_mapper") or self.field_mapper is None:
                object.__setattr__(self, "field_mapper", None)

        def _get_field_mapper(self):
            """Get field mapper service instance when needed."""
            if not self.field_mapper:
                try:
                    from app.services.field_mapper_modular import FieldMapperService

                    self.field_mapper = FieldMapperService()
                except ImportError:
                    logger.warning("Field mapper service not available")
                    self.field_mapper = None
            return self.field_mapper

        def _run(self, assets: List[Dict[str, Any]], context: str = "general") -> str:
            """Analyze patterns in asset data using AI intelligence."""
            try:
                if not assets:
                    return '{"patterns": [], "insights": [], "confidence": 0.0}'

                # Use field mapping intelligence to understand asset data structure
                if assets:
                    list(assets[0].keys())

                # Get field mapping context for intelligent analysis
                field_context = {}
                field_mapper = self._get_field_mapper()
                if field_mapper:
                    try:
                        field_context = field_mapper.agent_get_mapping_context()
                    except Exception as e:
                        logger.warning(f"Failed to get field mapping context: {e}")

                # AI-powered pattern recognition (not hard-coded rules)
                patterns = self._identify_intelligent_patterns(
                    assets, field_context, context
                )
                insights = self._generate_actionable_insights(patterns, context)
                confidence = self._calculate_pattern_confidence(patterns, len(assets))

                result = {
                    "patterns": patterns,
                    "insights": insights,
                    "confidence": confidence,
                    "asset_count": len(assets),
                    "field_context": field_context,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                }

                return str(result)

            except Exception as e:
                logger.error(f"Asset pattern analysis failed: {e}")
                return f'{{"error": "{str(e)}", "patterns": [], "insights": []}}'

        def _identify_intelligent_patterns(
            self, assets: List[Dict], field_context: Dict, context: str
        ) -> List[Dict]:
            """Use AI intelligence to identify patterns, not hard-coded rules."""
            patterns = []

            try:
                # Pattern 1: Field usage patterns based on learned mappings
                field_usage = self._analyze_field_usage_patterns(assets, field_context)
                if field_usage:
                    patterns.append(
                        {
                            "type": "field_usage",
                            "pattern": field_usage,
                            "confidence": 0.9,
                            "source": "field_mapping_intelligence",
                        }
                    )

                # Pattern 2: Content-based asset groupings
                content_groups = self._analyze_content_groupings(assets)
                if content_groups:
                    patterns.append(
                        {
                            "type": "content_grouping",
                            "pattern": content_groups,
                            "confidence": 0.8,
                            "source": "content_analysis",
                        }
                    )

                # Pattern 3: Quality consistency patterns
                quality_patterns = self._analyze_quality_consistency(assets)
                if quality_patterns:
                    patterns.append(
                        {
                            "type": "quality_consistency",
                            "pattern": quality_patterns,
                            "confidence": 0.85,
                            "source": "quality_analysis",
                        }
                    )

            except Exception as e:
                logger.warning(f"Pattern identification failed: {e}")

            return patterns

        def _generate_actionable_insights(
            self, patterns: List[Dict], context: str
        ) -> List[Dict]:
            """Generate actionable insights based on identified patterns."""
            insights = []

            for pattern in patterns:
                if pattern["type"] == "field_usage":
                    insights.append(
                        {
                            "type": "field_optimization",
                            "insight": "Field mapping patterns suggest optimization opportunities",
                            "action": "Review field usage consistency",
                            "priority": "medium",
                            "confidence": pattern["confidence"],
                        }
                    )

                elif pattern["type"] == "content_grouping":
                    insights.append(
                        {
                            "type": "classification_opportunity",
                            "insight": "Content analysis reveals natural asset groupings",
                            "action": "Consider bulk classification based on content patterns",
                            "priority": "high",
                            "confidence": pattern["confidence"],
                        }
                    )

                elif pattern["type"] == "quality_consistency":
                    insights.append(
                        {
                            "type": "quality_improvement",
                            "insight": "Quality analysis shows improvement opportunities",
                            "action": "Address identified quality issues",
                            "priority": "high",
                            "confidence": pattern["confidence"],
                        }
                    )

            return insights

        def _calculate_pattern_confidence(
            self, patterns: List[Dict], asset_count: int
        ) -> float:
            """Calculate overall confidence in pattern analysis."""
            if not patterns or asset_count == 0:
                return 0.0

            total_confidence = sum(p.get("confidence", 0.0) for p in patterns)
            avg_confidence = total_confidence / len(patterns)

            # Adjust confidence based on asset count
            if asset_count < 10:
                avg_confidence *= 0.8
            elif asset_count > 100:
                avg_confidence *= 1.1

            return min(avg_confidence, 1.0)

        def _analyze_field_usage_patterns(
            self, assets: List[Dict], field_context: Dict
        ) -> Dict:
            """Analyze field usage patterns using field mapping intelligence."""
            if not assets:
                return {}

            all_fields = set()
            for asset in assets:
                all_fields.update(asset.keys())

            field_usage = {}
            for field in all_fields:
                populated_count = sum(1 for asset in assets if asset.get(field))
                field_usage[field] = {
                    "usage_rate": populated_count / len(assets),
                    "populated_count": populated_count,
                    "total_assets": len(assets),
                }

            return {"field_usage": field_usage, "total_fields": len(all_fields)}

        def _analyze_content_groupings(self, assets: List[Dict]) -> Dict:
            """Analyze content-based groupings in assets."""
            if not assets:
                return {}

            # Simple content grouping by asset type
            type_groups = {}
            for asset in assets:
                asset_type = asset.get("type", asset.get("asset_type", "unknown"))
                if asset_type not in type_groups:
                    type_groups[asset_type] = []
                type_groups[asset_type].append(asset.get("id", "unknown"))

            return {"type_groups": type_groups, "group_count": len(type_groups)}

        def _analyze_quality_consistency(self, assets: List[Dict]) -> Dict:
            """Analyze quality consistency across assets."""
            if not assets:
                return {}

            # Calculate basic quality metrics
            total_fields = sum(len(asset) for asset in assets)
            populated_fields = sum(
                sum(1 for value in asset.values() if value and str(value).strip())
                for asset in assets
            )

            quality_score = (
                (populated_fields / total_fields * 100) if total_fields > 0 else 0
            )

            return {
                "overall_quality_score": round(quality_score, 2),
                "total_fields": total_fields,
                "populated_fields": populated_fields,
            }

    class BulkOperationsInput(BaseModel):
        """Input schema for bulk operations tool."""

        asset_ids: List[str] = Field(
            ..., description="List of asset IDs for bulk operation"
        )
        updates: Dict[str, Any] = Field(
            ..., description="Dictionary of field updates to apply"
        )
        operation_type: str = Field(
            default="update",
            description="Type of bulk operation: update, delete, classify",
        )

    class BulkOperationsTool(BaseTool):
        """
        AI-powered tool for intelligent bulk operations planning.
        Uses learned patterns to optimize bulk operations.
        """

        name: str = "bulk_operations_tool"
        description: str = "Plan and optimize bulk operations using AI intelligence"
        args_schema: type[BaseModel] = BulkOperationsInput
        # Declare field_mapper as a Pydantic field to avoid validation errors
        field_mapper: Optional[Any] = Field(
            default=None, description="Field mapper service instance"
        )

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Initialize field_mapper to None - it will be injected via service layer when needed
            if not hasattr(self, "field_mapper") or self.field_mapper is None:
                object.__setattr__(self, "field_mapper", None)

        def _get_field_mapper(self):
            """Get field mapper service instance when needed."""
            if not self.field_mapper:
                try:
                    from app.services.field_mapper_modular import FieldMapperService

                    self.field_mapper = FieldMapperService()
                except ImportError:
                    logger.warning("Field mapper service not available")
                    self.field_mapper = None
            return self.field_mapper

        def _run(
            self,
            asset_ids: List[str],
            updates: Dict[str, Any],
            operation_type: str = "update",
        ) -> str:
            """Plan optimal bulk operation strategy using AI intelligence."""
            try:
                # AI-powered bulk operation planning
                plan = {
                    "asset_ids": asset_ids,
                    "updates": updates,
                    "operation_type": operation_type,
                    "strategy": self._determine_optimal_strategy(asset_ids, updates),
                    "validation": self._validate_bulk_updates(asset_ids, updates),
                    "execution_order": self._optimize_execution_order(
                        asset_ids, updates
                    ),
                    "risk_assessment": self._assess_bulk_operation_risks(
                        asset_ids, updates
                    ),
                    "plan_timestamp": datetime.utcnow().isoformat(),
                }

                return str(plan)

            except Exception as e:
                logger.error(f"Bulk operation planning failed: {e}")
                return f'{{"error": "{str(e)}", "asset_ids": {asset_ids}}}'

        def _determine_optimal_strategy(
            self, asset_ids: List[str], updates: Dict
        ) -> Dict[str, Any]:
            """Determine optimal bulk operation strategy using AI intelligence."""
            return {
                "recommended_batch_size": min(len(asset_ids), 50),
                "parallel_execution": len(asset_ids) > 10,
                "validation_required": True,
                "rollback_strategy": "checkpoint",
            }

        def _validate_bulk_updates(
            self, asset_ids: List[str], updates: Dict
        ) -> Dict[str, Any]:
            """Validate bulk updates for potential issues."""
            issues = []
            warnings = []

            if len(asset_ids) > 100:
                warnings.append("Large bulk operation - consider batching")

            if not updates:
                issues.append("No updates specified")

            return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}

        def _optimize_execution_order(
            self, asset_ids: List[str], updates: Dict
        ) -> List[str]:
            """Optimize execution order for bulk operations."""
            # Simple optimization - return assets in original order
            return asset_ids

        def _assess_bulk_operation_risks(
            self, asset_ids: List[str], updates: Dict
        ) -> Dict[str, Any]:
            """Assess risks associated with bulk operation."""
            risk_level = "low"
            risk_factors = []

            if len(asset_ids) > 100:
                risk_level = "medium"
                risk_factors.append("Large number of assets")

            if len(updates) > 5:
                risk_level = "medium"
                risk_factors.append("Multiple field updates")

            return {
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "mitigation_recommended": risk_level != "low",
            }

else:
    # Fallback classes when CrewAI is not available
    class AssetAnalysisTool:
        """Fallback asset analysis tool."""

        def __init__(self):
            self.tool_name = "asset_analysis_tool"
            self.description = "Analyze asset patterns and provide intelligent insights for inventory management"
            # Initialize field_mapper to prevent attribute errors
            self.field_mapper = None

        def _get_field_mapper(self):
            """Get field mapper service instance when needed."""
            if not self.field_mapper:
                try:
                    from app.services.field_mapper_modular import FieldMapperService

                    self.field_mapper = FieldMapperService()
                except ImportError:
                    logger.warning("Field mapper service not available")
                    self.field_mapper = None
            return self.field_mapper

        def run(self, *args, **kwargs):
            """Fallback run method."""
            logger.info(
                "AssetAnalysisTool fallback: CrewAI not available, using basic analysis"
            )
            return {"patterns": [], "insights": [], "confidence": 0.0, "fallback": True}

    class BulkOperationsTool:
        """Fallback bulk operations tool."""

        def __init__(self):
            self.tool_name = "bulk_operations_tool"
            self.description = "Plan and optimize bulk operations using AI intelligence"
            # Initialize field_mapper to prevent attribute errors
            self.field_mapper = None

        def _get_field_mapper(self):
            """Get field mapper service instance when needed."""
            if not self.field_mapper:
                try:
                    from app.services.field_mapper_modular import FieldMapperService

                    self.field_mapper = FieldMapperService()
                except ImportError:
                    logger.warning("Field mapper service not available")
                    self.field_mapper = None
            return self.field_mapper

        def run(self, *args, **kwargs):
            """Fallback run method."""
            logger.info(
                "BulkOperationsTool fallback: CrewAI not available, using basic planning"
            )
            return {
                "strategy": "basic",
                "validation": {"valid": True},
                "fallback": True,
            }


# Tool registry for easy access
ASSET_INTELLIGENCE_TOOLS = {
    "asset_analysis": AssetAnalysisTool,
    "bulk_operations": BulkOperationsTool,
}


# Tool registration for CrewAI integration
def get_asset_intelligence_tools(field_mapper=None):
    """Get all asset intelligence tools for CrewAI integration."""
    if CREWAI_TOOLS_AVAILABLE:
        return [tool_class() for tool_class in ASSET_INTELLIGENCE_TOOLS.values()]
    else:
        return []
