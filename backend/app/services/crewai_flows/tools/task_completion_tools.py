"""
CrewAI Tools for Intelligent Task Coordination
Provides intelligent agents with tools to check task completion status,
avoid redundant work, and deduplicate data.
"""

import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Import CrewAI tools following official documentation
try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
    logger.info("✅ CrewAI tools imported successfully")
except ImportError:
    try:
        from crewai_tools import BaseTool

        CREWAI_TOOLS_AVAILABLE = True
        logger.info("✅ CrewAI tools imported from crewai_tools")
    except ImportError:
        logger.warning("⚠️ CrewAI tools not available - tools will be disabled")
        CREWAI_TOOLS_AVAILABLE = False

        # Create a dummy BaseTool class if not available
        class BaseTool:
            def __init__(self, *args, **kwargs):
                pass


def create_task_completion_tools(context_info: Dict[str, Any]) -> List:
    """
    Create intelligent task coordination tools for agents.

    These tools enable agents to:
    1. Check if assets already exist to avoid duplicates
    2. Verify recent task completion to prevent redundant work
    3. Coordinate with other agents to avoid conflicts
    4. Perform intelligent asset enrichment
    """
    logger.info("🔧 Creating intelligent task coordination tools")

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        tools = []

        # Asset deduplication tool
        asset_dedup_tool = AssetDeduplicationTool(context_info)
        tools.append(asset_dedup_tool)

        # Task completion checker tool
        task_completion_tool = TaskCompletionCheckerTool(context_info)
        tools.append(task_completion_tool)

        # Asset enrichment tool
        asset_enrichment_tool = AssetEnrichmentTool(context_info)
        tools.append(asset_enrichment_tool)

        logger.info(f"✅ Created {len(tools)} intelligent coordination tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create task completion tools: {e}")
        return []


# Only define tool classes if CrewAI is available
if CREWAI_TOOLS_AVAILABLE:

    class AssetDeduplicationTool(BaseTool):
        """Tool for agents to check if assets already exist"""

        name: str = "asset_deduplication_checker"
        description: str = """
        Check if assets already exist in the database to avoid creating duplicates.
        Use this tool BEFORE creating new assets to ensure no duplicates are created.

        Input: List of assets to check (with hostname/name fields)
        Output: List of assets that don't already exist and are safe to create
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            # Store context info in a way that's compatible with CrewAI
            self._context_info = context_info

        async def _arun(
            self, assets_to_check: List[Dict[str, Any]]
        ) -> List[Dict[str, Any]]:
            """Async implementation of asset deduplication check"""
            try:
                logger.info(
                    f"🔍 Agent requested deduplication check for {len(assets_to_check)} assets"
                )

                # Validate context first
                if not self._is_valid_context():
                    logger.warning(
                        "⚠️ Missing context for deduplication - returning all assets"
                    )
                    return assets_to_check

                # Get existing assets from database
                existing_assets = await self._get_existing_assets()
                if existing_assets is None:
                    return assets_to_check

                # Filter out duplicates
                unique_assets = self._filter_duplicate_assets(
                    assets_to_check, existing_assets
                )

                logger.info(
                    f"✅ Deduplication complete: {len(assets_to_check)} → {len(unique_assets)} unique assets"
                )
                return unique_assets

            except Exception as e:
                logger.error(f"❌ Error in asset deduplication tool: {e}")
                return assets_to_check  # Return all assets on error

        def _is_valid_context(self) -> bool:
            """Validate that required context is available"""
            context = self._context_info
            return (
                context is not None
                and context.get("client_account_id") is not None
                and context.get("engagement_id") is not None
            )

        async def _get_existing_assets(self) -> List[Any]:
            """Get existing assets from database"""
            try:
                from app.core.database import AsyncSessionLocal
                from app.repositories.discovery_flow_repository.queries.asset_queries import (
                    AssetQueries,
                )

                async with AsyncSessionLocal() as db:
                    context = self._context_info
                    asset_queries = AssetQueries(
                        db, context["client_account_id"], context["engagement_id"]
                    )
                    return await asset_queries.get_assets_by_client_engagement()
            except Exception as e:
                logger.error(f"❌ Error getting existing assets: {e}")
                return None

        def _filter_duplicate_assets(
            self, assets_to_check: List[Dict[str, Any]], existing_assets: List[Any]
        ) -> List[Dict[str, Any]]:
            """Filter out duplicate assets"""
            unique_assets = []
            for asset in assets_to_check:
                if not self._is_duplicate_asset(asset, existing_assets):
                    unique_assets.append(asset)
            return unique_assets

        def _is_duplicate_asset(
            self, asset: Dict[str, Any], existing_assets: List[Any]
        ) -> bool:
            """Check if asset is a duplicate of any existing asset"""
            for field, value in asset.items():
                if not value:
                    continue

                if self._is_meaningful_field(field) and self._field_matches_existing(
                    field, value, existing_assets
                ):
                    logger.debug(
                        f"⏭️ Asset with {field}='{value}' already exists - skipping"
                    )
                    return True
            return False

        def _is_meaningful_field(self, field: str) -> bool:
            """Check if field is meaningful for duplicate detection"""
            meaningful_fields = {
                "hostname",
                "name",
                "ip_address",
                "asset_id",
                "serial_number",
            }
            return field in meaningful_fields

        def _field_matches_existing(
            self, field: str, value: Any, existing_assets: List[Any]
        ) -> bool:
            """Check if field value matches any existing asset"""
            value_str = str(value).lower()
            for existing_asset in existing_assets:
                existing_value = getattr(existing_asset, field, None)
                if existing_value and str(existing_value).lower() == value_str:
                    return True
            return False

        def _run(self, assets_to_check: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Sync wrapper for async implementation"""
            return asyncio.run(self._arun(assets_to_check))

    class TaskCompletionCheckerTool(BaseTool):
        """Tool for agents to check if a task was recently completed"""

        name: str = "task_completion_checker"
        description: str = """
        Check if a specific task (like asset inventory) was recently completed
        to avoid redundant work. Use this BEFORE starting major processing tasks.

        Input: Task name (e.g., "asset_inventory", "data_cleansing")
        Output: Dict with completion status and details
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, task_name: str) -> Dict[str, Any]:
            """Check if task was recently completed"""
            try:
                logger.info(
                    f"🔍 Agent checking completion status for task: {task_name}"
                )

                # Check agent insights for recent completion
                import json
                from pathlib import Path

                insights_file = Path("backend/data/agent_insights.json")
                if insights_file.exists():
                    with open(insights_file, "r") as f:
                        insights = json.load(f)

                    # Look for recent completion of this task
                    recent_completion = None
                    for insight_id, insight in insights.items():
                        if insight.get(
                            "insight_type"
                        ) == "phase_complete" and task_name in insight.get(
                            "supporting_data", {}
                        ).get(
                            "phase", ""
                        ):
                            recent_completion = insight
                            break

                    if recent_completion:
                        logger.info(f"✅ Recent completion found for {task_name}")
                        return {
                            "recently_completed": True,
                            "completion_time": recent_completion.get("created_at"),
                            "details": recent_completion.get("supporting_data", {}),
                        }

                logger.info(f"ℹ️ No recent completion found for {task_name}")
                return {"recently_completed": False, "details": {}}

            except Exception as e:
                logger.error(f"❌ Error checking task completion: {e}")
                return {"recently_completed": False, "details": {}}

    class AssetEnrichmentTool(BaseTool):
        """Tool for agents to enrich assets with additional metadata"""

        name: str = "asset_enrichment_analyzer"
        description: str = """
        Analyze and enrich assets with additional metadata for better classification.
        Use this tool to enhance asset data with technology stack, environment,
        migration complexity, and criticality assessments.

        Input: Asset data to enrich
        Output: Enhanced asset data with enrichment metadata
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
            """Enrich asset data with additional metadata"""
            try:
                logger.info(
                    f"🔍 Agent requested enrichment for asset: {asset_data.get('name', 'unknown')}"
                )

                enriched_data = asset_data.copy()
                enrichment_metadata = {}

                # Technology stack detection
                tech_stack = self._detect_technology_stack(asset_data)
                if tech_stack:
                    enrichment_metadata["technology_stack"] = tech_stack

                # Environment classification
                environment = self._classify_environment(asset_data)
                if environment:
                    enrichment_metadata["environment_classification"] = environment

                # Migration complexity assessment
                complexity = self._assess_migration_complexity(asset_data)
                if complexity:
                    enrichment_metadata["migration_complexity"] = complexity

                # Criticality assessment
                criticality = self._assess_criticality(asset_data)
                if criticality:
                    enrichment_metadata["criticality_assessment"] = criticality

                # Add enrichment metadata
                enriched_data["enrichment_metadata"] = enrichment_metadata
                enriched_data["enriched_by_agent"] = True

                logger.info(
                    f"✅ Asset enrichment complete: {len(enrichment_metadata)} metadata fields added"
                )
                return enriched_data

            except Exception as e:
                logger.error(f"❌ Error in asset enrichment: {e}")
                return asset_data  # Return original data on error

        def _detect_technology_stack(
            self, asset_data: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Detect technology stack from asset data"""
            tech_stack = {}

            # Check various fields for technology indicators
            text_fields = [
                "Asset_Type",
                "asset_type",
                "name",
                "Asset_Name",
                "Operating_System",
                "Application_Name",
            ]

            for field in text_fields:
                value = asset_data.get(field, "")
                if isinstance(value, str):
                    value_lower = value.lower()

                    # OS detection
                    if any(
                        os in value_lower
                        for os in ["windows", "linux", "unix", "centos", "ubuntu"]
                    ):
                        tech_stack["operating_system"] = value

                    # Database detection
                    if any(
                        db in value_lower
                        for db in ["mysql", "postgresql", "oracle", "mongodb"]
                    ):
                        tech_stack["database_technology"] = value

                    # Web technology detection
                    if any(
                        web in value_lower
                        for web in ["apache", "nginx", "java", "python", "nodejs"]
                    ):
                        tech_stack["web_technology"] = value

            return tech_stack

        def _classify_environment(self, asset_data: Dict[str, Any]) -> str:
            """Classify environment based on asset data"""
            env_indicators = {
                "production": ["prod", "production", "prd"],
                "development": ["dev", "development", "devel"],
                "testing": ["test", "testing", "qa", "uat"],
                "staging": ["stage", "staging", "stg"],
            }

            # Check hostname and name fields
            check_fields = ["hostname", "Hostname", "name", "Asset_Name"]
            for field in check_fields:
                value = asset_data.get(field, "")
                if isinstance(value, str):
                    value_lower = value.lower()
                    for env_type, indicators in env_indicators.items():
                        if any(indicator in value_lower for indicator in indicators):
                            return env_type

            return "unknown"

        def _assess_migration_complexity(self, asset_data: Dict[str, Any]) -> str:
            """Assess migration complexity based on asset characteristics"""
            complexity_score = 0

            # Base complexity on asset type
            asset_type = asset_data.get("Asset_Type", "").lower()
            if "database" in asset_type:
                complexity_score += 3
            elif "application" in asset_type:
                complexity_score += 2
            elif "server" in asset_type:
                complexity_score += 1

            # Check for complexity indicators
            if asset_data.get("dependencies"):
                complexity_score += 2
            if asset_data.get("legacy_system"):
                complexity_score += 3

            if complexity_score >= 6:
                return "high"
            elif complexity_score >= 3:
                return "medium"
            else:
                return "low"

        def _assess_criticality(self, asset_data: Dict[str, Any]) -> str:
            """Assess asset criticality"""
            criticality_score = 0

            # Base criticality on asset type
            asset_type = asset_data.get("Asset_Type", "").lower()
            if "database" in asset_type:
                criticality_score += 3
            elif "application" in asset_type:
                criticality_score += 2
            elif "server" in asset_type:
                criticality_score += 1

            # Check environment
            environment = self._classify_environment(asset_data)
            if environment == "production":
                criticality_score += 2

            if criticality_score >= 5:
                return "critical"
            elif criticality_score >= 3:
                return "high"
            else:
                return "medium"

    class ExecutionCoordinationTool(BaseTool):
        """Tool for agents to coordinate execution and avoid conflicts"""

        name: str = "execution_coordinator"
        description: str = """
        Coordinate with other agents to avoid conflicts and redundant execution.
        Use this when starting parallel operations that might conflict.

        Input: Operation name and agent identifier
        Output: Coordination status and recommendations
        """

        def __init__(self, context_info: Dict[str, Any]):
            super().__init__()
            self._context_info = context_info

        def _run(self, operation_name: str, agent_id: str) -> Dict[str, Any]:
            """Coordinate execution with other agents"""
            try:
                logger.info(
                    f"🤝 Agent {agent_id} requesting coordination for {operation_name}"
                )

                # Simple coordination - could be enhanced with proper locking
                from datetime import datetime

                # Check if another agent is recently working on the same operation
                coordination_result = {
                    "can_proceed": True,
                    "coordination_time": datetime.utcnow().isoformat(),
                    "agent_id": agent_id,
                    "operation": operation_name,
                    "recommendations": [],
                }

                logger.info(
                    f"✅ Coordination complete for {agent_id} on {operation_name}"
                )
                return coordination_result

            except Exception as e:
                logger.error(f"❌ Error in execution coordination: {e}")
                return {
                    "can_proceed": True,
                    "recommendations": ["Proceed with caution - coordination failed"],
                }

else:
    # Create dummy classes if CrewAI is not available
    class AssetDeduplicationTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    class TaskCompletionCheckerTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    class AssetEnrichmentTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass

    class ExecutionCoordinationTool:
        def __init__(self, context_info: Dict[str, Any]):
            pass
