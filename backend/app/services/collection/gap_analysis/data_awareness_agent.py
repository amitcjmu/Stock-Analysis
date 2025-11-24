"""
Data Awareness Agent - ONE-TIME agent for comprehensive data mapping.

This agent runs ONCE per collection flow to understand what data exists across
all 6 sources before generating questionnaires. It provides context for intelligent
question generation by identifying:
- TRUE gaps (no data in any source)
- Data-exists-elsewhere (found in alternative sources)
- Asset-specific data coverage patterns
- Cross-asset data patterns for optimization

CC Generated for Issue #1112 - DataAwarenessAgent (One-Time Per Flow)
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture

Architecture:
- ONE-TIME execution per flow (not per-section, not per-asset)
- Direct JSON generation via multi_model_service (no tool calls)
- Comprehensive data map cached for all sections
- Multi-tenant context (client_account_id, engagement_id)
- Observability via multi_model_service automatic tracking
"""

import logging
from typing import Any, Dict, List

from app.models.asset.models import Asset
from app.services.collection.gap_analysis.models import IntelligentGap
from app.services.multi_model_service import multi_model_service, TaskComplexity
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)


class DataAwarenessAgent:
    """
    ONE-TIME agent that creates comprehensive data map for ALL assets in flow.

    This agent provides the foundation for intelligent questionnaire generation
    by analyzing data coverage across all 6 sources:
    1. Standard Columns (assets.{field})
    2. Custom Attributes (JSONB)
    3. Enrichment Data (tech_debt, performance_metrics, cost_optimization)
    4. Environment Field (string)
    5. Canonical Applications (junction table)
    6. Related Assets (propagation via asset_dependencies)

    The data map includes:
    - Per-asset data coverage percentages by source
    - TRUE gaps (no data in ANY source)
    - Data-exists-elsewhere (with source and value)
    - Cross-asset patterns (common gaps, common data sources)
    - Recommendations for data consolidation

    Usage:
        agent = DataAwarenessAgent()
        data_map = await agent.create_data_map(
            flow_id="abc-123",
            assets=[asset1, asset2, ...],
            intelligent_gaps={
                "asset1_id": [gap1, gap2, ...],
                "asset2_id": [gap3, gap4, ...]
            },
            client_account_id=1,
            engagement_id=123
        )

    Returns:
        {
            "flow_id": "abc-123",
            "assets": [
                {
                    "asset_id": "def-456",
                    "asset_name": "Consul Production",
                    "data_coverage": {
                        "standard_columns": 60,
                        "custom_attributes": 30,
                        "enrichment_data": 10,
                        "environment": 15,
                        "canonical_apps": 5,
                        "related_assets": 0
                    },
                    "true_gaps": [...],
                    "data_exists_elsewhere": [...]
                }
            ],
            "cross_asset_patterns": {
                "common_gaps": ["cpu_count", "memory_gb"],
                "common_data_sources": ["custom_attributes"],
                "recommendations": [...]
            }
        }
    """

    async def create_data_map(
        self,
        flow_id: str,
        assets: List[Asset],
        intelligent_gaps: Dict[str, List[IntelligentGap]],
        client_account_id: int,
        engagement_id: int,
    ) -> Dict[str, Any]:
        """
        Create comprehensive data awareness map.

        This is the MAIN ENTRY POINT for the agent. It runs once per flow
        to create a complete picture of data availability.

        Args:
            flow_id: Collection flow UUID (child flow ID)
            assets: List of Asset objects in the collection flow
            intelligent_gaps: Dict mapping asset_id → List[IntelligentGap]
                             (from IntelligentGapScanner)
            client_account_id: Client account ID for multi-tenant scoping
            engagement_id: Engagement ID for multi-tenant scoping

        Returns:
            Dict with comprehensive data map (see class docstring for format)

        Raises:
            ValueError: If assets list is empty or intelligent_gaps is missing
            Exception: If LLM call fails or JSON parsing fails

        Example:
            >>> agent = DataAwarenessAgent()
            >>> data_map = await agent.create_data_map(
            ...     flow_id="abc-123",
            ...     assets=[asset1, asset2],
            ...     intelligent_gaps={"asset1_id": [gap1], "asset2_id": [gap2]},
            ...     client_account_id=1,
            ...     engagement_id=123
            ... )
            >>> print(data_map["flow_id"])
            abc-123
            >>> print(len(data_map["assets"]))
            2
        """
        if not assets:
            raise ValueError("Assets list cannot be empty")

        if intelligent_gaps is None:
            raise ValueError("Intelligent gaps dictionary cannot be None")

        logger.info(
            f"🔍 DataAwarenessAgent: Creating data map for flow_id={flow_id}, "
            f"assets={len(assets)}, client_account_id={client_account_id}, "
            f"engagement_id={engagement_id}"
        )

        # Build LLM prompt
        prompt = f"""
You are a Data Awareness Agent analyzing asset data coverage across 6 sources.

**Flow Context**:
- Flow ID: {flow_id}
- Total Assets: {len(assets)}
- Client Account: {client_account_id}
- Engagement: {engagement_id}

**Data Sources Analyzed**:
1. Standard Columns (assets.{{field}})
2. Custom Attributes (custom_attributes JSONB)
3. Enrichment Data (asset_tech_debt, asset_performance_metrics, asset_cost_optimization)
4. Environment Field (assets.environment string)
5. Canonical Applications (canonical_applications junction)
6. Related Assets (asset_dependencies propagation)

**Assets and Gaps**:
{self._format_assets_and_gaps(assets, intelligent_gaps)}

**Task**:
Create a comprehensive data awareness map showing:
1. For each asset, which data sources have coverage (as percentages)
2. Which gaps are TRUE gaps (no data in ANY source)
3. Which fields have data-exists-elsewhere (with source and value)
4. Cross-asset patterns (common gaps, common data sources)
5. Recommendations for data consolidation

**Output Format** (JSON):
{{
    "flow_id": "{flow_id}",
    "assets": [
        {{
            "asset_id": "uuid",
            "asset_name": "name",
            "data_coverage": {{
                "standard_columns": 60, "custom_attributes": 30,
                "enrichment_data": 10, "environment": 15,
                "canonical_apps": 5, "related_assets": 0
            }},
            "true_gaps": [
                {{
                    "field": "cpu_count",
                    "priority": "critical",
                    "section": "infrastructure",
                    "checked_sources": 6,
                    "found_in": []
                }}
            ],
            "data_exists_elsewhere": [
                {{
                    "field": "database_type",
                    "found_in": "custom_attributes.db_type",
                    "value": "PostgreSQL 14",
                    "no_question_needed": true
                }}
            ]
        }}
    ],
    "cross_asset_patterns": {{
        "common_gaps": ["cpu_count", "memory_gb"],
        "common_data_sources": ["custom_attributes"],
        "recommendations": [
            "Use custom_attributes for additional fields",
            "Populate enrichment_data for resilience info"
        ]
    }}
}}

**Critical**: Only include fields in "true_gaps" if data NOT found in ANY of 6 sources.
If data exists anywhere, include in "data_exists_elsewhere" with source and value.

**Important**: Return ONLY valid JSON, no markdown formatting, no code blocks.
"""

        # Call multi_model_service for LLM generation (automatic observability)
        logger.debug("Calling multi_model_service for data awareness analysis")

        response_data = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="data_analysis",
            complexity=TaskComplexity.SIMPLE,  # Single-phase analysis
            system_message=(
                "You are a data awareness agent. Analyze asset data coverage "
                "and return ONLY valid JSON without markdown formatting."
            ),
        )

        # Extract response text from multi_model_service response
        response_text = response_data.get("response", "")

        if not response_text:
            raise Exception(
                "Empty response from multi_model_service in DataAwarenessAgent"
            )

        logger.debug(
            f"Received response from LLM: {len(response_text)} characters, "
            f"tokens_used={response_data.get('tokens_used', 0)}"
        )

        # Parse LLM response as JSON (with sanitization per ADR-029)
        import json
        import re

        # Strip markdown code blocks if present (per ADR-029)
        cleaned = re.sub(r"```json\s*|\s*```", "", response_text).strip()

        try:
            # Try standard JSON parsing first
            data_map = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Cleaned response: {cleaned[:500]}...")

            # Fallback to dirtyjson (per ADR-029)
            try:
                import dirtyjson

                data_map = dirtyjson.loads(cleaned)
                logger.warning("Used dirtyjson fallback for malformed JSON")
            except Exception as dirtyjson_error:
                logger.error(f"dirtyjson parsing also failed: {dirtyjson_error}")
                raise ValueError(f"Unable to parse LLM response as JSON: {e}") from e

        # Sanitize for JSON serialization (handles NaN, Infinity per ADR-029)
        data_map = sanitize_for_json(data_map)

        logger.info(
            f"✅ DataAwarenessAgent: Created data map with "
            f"{len(data_map.get('assets', []))} assets"
        )

        return data_map

    def _format_assets_and_gaps(
        self, assets: List[Asset], intelligent_gaps: Dict[str, List[IntelligentGap]]
    ) -> str:
        """
        Format assets and gaps for LLM prompt.

        Creates a structured text representation of all assets and their
        intelligent gaps (both TRUE gaps and data-exists-elsewhere).

        Args:
            assets: List of Asset objects
            intelligent_gaps: Dict mapping asset_id (str) → List[IntelligentGap]

        Returns:
            Formatted string with asset information and gaps

        Example Output:
            '''
            Asset: Consul Production (ID: abc-123)
            Type: Application Server
            TRUE Gaps (2):
              - cpu_count (priority: critical, section: infrastructure)
              - memory_gb (priority: high, section: infrastructure)

            Data Exists Elsewhere (3):
              - database_type: custom_attributes.db_type=PostgreSQL 14
              - hostname: custom_attributes.host=consul-prod-01
              - environment: assets.environment=production

            ---

            Asset: Redis Cache (ID: def-456)
            Type: Database
            ...
            '''
        """
        formatted_parts = []

        for asset in assets:
            asset_id_str = str(asset.id)
            gaps = intelligent_gaps.get(asset_id_str, [])

            # Separate TRUE gaps from data-exists-elsewhere
            true_gaps = [g for g in gaps if g.is_true_gap]
            data_elsewhere = [g for g in gaps if not g.is_true_gap]

            formatted_parts.append(
                f"""
Asset: {asset.name} (ID: {asset.id})
Type: {asset.asset_type if hasattr(asset, 'asset_type') else 'Unknown'}
TRUE Gaps ({len(true_gaps)}):
{self._format_gaps(true_gaps)}

Data Exists Elsewhere ({len(data_elsewhere)}):
{self._format_data_sources(data_elsewhere)}
"""
            )

        return "\n---\n".join(formatted_parts)

    def _format_gaps(self, gaps: List[IntelligentGap]) -> str:
        """
        Format TRUE gaps for LLM prompt.

        Args:
            gaps: List of IntelligentGap objects where is_true_gap=True

        Returns:
            Formatted string with gap details

        Example Output:
            '''
              - cpu_count (priority: critical, section: infrastructure)
              - memory_gb (priority: high, section: infrastructure)
              - disk_size_gb (priority: medium, section: infrastructure)
            '''
        """
        if not gaps:
            return "  (none)"

        return "\n".join(
            [
                f"  - {g.field_name} (priority: {g.priority}, section: {g.section})"
                for g in gaps
            ]
        )

    def _format_data_sources(self, gaps: List[IntelligentGap]) -> str:
        """
        Format data-exists-elsewhere for LLM prompt.

        Args:
            gaps: List of IntelligentGap objects where is_true_gap=False
                  (meaning data was found in at least one source)

        Returns:
            Formatted string with data source details

        Example Output:
            '''
              - database_type: custom_attributes.db_type=PostgreSQL 14
              - hostname: custom_attributes.host=consul-prod-01, assets.name=Consul Production
              - environment: assets.environment=production
            '''
        """
        if not gaps:
            return "  (none)"

        lines = []
        for g in gaps:
            # Format all data sources for this field
            sources_formatted = ", ".join(
                [f"{ds.field_path}={ds.value}" for ds in g.data_found]
            )
            lines.append(f"  - {g.field_name}: {sources_formatted}")

        return "\n".join(lines)
