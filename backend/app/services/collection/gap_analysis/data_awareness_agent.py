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

# SKIP_FILE_LENGTH_CHECK
# TODO: Modularize this file - currently 578 lines (exceeds 400 limit)
# Split into: data_sources.py, gap_detection.py, llm_caller.py, batch_processor.py
"""

import logging
from typing import Any, Dict, List

from app.models.asset.models import Asset
from app.services.collection.gap_analysis.models import IntelligentGap
from app.services.multi_model_service import multi_model_service, TaskComplexity
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

# ✅ FIX Bug #21: Process assets in batches to prevent LLM response truncation
# Per ADR-035: Large prompts with 50+ assets cause LLM to truncate JSON responses
# Processing in batches of 5 assets ensures responses fit within token limits
ASSETS_PER_BATCH = 5


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

        ✅ FIX Bug #21: Process assets in batches to prevent LLM response truncation.
        Per ADR-035, large prompts cause truncated JSON responses. We now process
        assets in batches of ASSETS_PER_BATCH and merge results.

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
        """
        if not assets:
            raise ValueError("Assets list cannot be empty")

        if intelligent_gaps is None:
            raise ValueError("Intelligent gaps dictionary cannot be None")

        total_assets = len(assets)
        num_batches = (total_assets + ASSETS_PER_BATCH - 1) // ASSETS_PER_BATCH

        logger.info(
            f"🔍 DataAwarenessAgent: Creating data map for flow_id={flow_id}, "
            f"assets={total_assets}, batches={num_batches}, "
            f"client_account_id={client_account_id}, engagement_id={engagement_id}"
        )

        # ✅ FIX Bug #21: Process assets in batches to prevent LLM response truncation
        all_asset_results = []
        all_common_gaps = set()
        all_common_data_sources = set()

        for batch_idx in range(num_batches):
            start_idx = batch_idx * ASSETS_PER_BATCH
            end_idx = min(start_idx + ASSETS_PER_BATCH, total_assets)
            batch_assets = assets[start_idx:end_idx]

            logger.info(
                f"📦 Processing batch {batch_idx + 1}/{num_batches} "
                f"(assets {start_idx + 1}-{end_idx} of {total_assets})"
            )

            try:
                batch_result = await self._process_asset_batch(
                    flow_id=flow_id,
                    batch_assets=batch_assets,
                    intelligent_gaps=intelligent_gaps,
                    batch_num=batch_idx + 1,
                    total_batches=num_batches,
                )

                # Merge batch results
                all_asset_results.extend(batch_result.get("assets", []))

                # Collect cross-asset patterns
                patterns = batch_result.get("cross_asset_patterns", {})
                all_common_gaps.update(patterns.get("common_gaps", []))
                all_common_data_sources.update(patterns.get("common_data_sources", []))

                logger.info(
                    f"✅ Batch {batch_idx + 1}/{num_batches} complete: "
                    f"{len(batch_result.get('assets', []))} assets processed"
                )

            except Exception as e:
                logger.error(
                    f"❌ Batch {batch_idx + 1}/{num_batches} failed: {e}",
                    exc_info=True,
                )
                # Continue with other batches, don't fail entire flow
                continue

        # Merge all results into final data map
        data_map = {
            "flow_id": flow_id,
            "assets": all_asset_results,
            "cross_asset_patterns": {
                "common_gaps": list(all_common_gaps),
                "common_data_sources": list(all_common_data_sources),
                "recommendations": self._generate_recommendations(
                    all_common_gaps, all_common_data_sources
                ),
            },
        }

        logger.info(
            f"✅ DataAwarenessAgent: Created data map with "
            f"{len(data_map.get('assets', []))} assets from {num_batches} batches"
        )

        return data_map

    async def _process_asset_batch(
        self,
        flow_id: str,
        batch_assets: List[Asset],
        intelligent_gaps: Dict[str, List[IntelligentGap]],
        batch_num: int,
        total_batches: int,
    ) -> Dict[str, Any]:
        """
        Process a single batch of assets through the LLM.

        ✅ FIX Bug #21: This method handles a small batch of assets (default 5)
        to ensure the LLM response fits within token limits.

        Args:
            flow_id: Collection flow UUID
            batch_assets: List of Asset objects in this batch (max ASSETS_PER_BATCH)
            intelligent_gaps: Full gaps dictionary
            batch_num: Current batch number (1-indexed)
            total_batches: Total number of batches

        Returns:
            Dict with batch results in same format as full data map
        """
        # Build LLM prompt for this batch only
        prompt = f"""
You are a Data Awareness Agent analyzing asset data coverage across 6 sources.

**Batch Context**:
- Flow ID: {flow_id}
- Batch: {batch_num} of {total_batches}
- Assets in this batch: {len(batch_assets)}

**Data Sources Analyzed**:
1. Standard Columns (assets.{{field}})
2. Custom Attributes (custom_attributes JSONB)
3. Enrichment Data (asset_tech_debt, asset_performance_metrics, asset_cost_optimization)
4. Environment Field (assets.environment string)
5. Canonical Applications (canonical_applications junction)
6. Related Assets (asset_dependencies propagation)

**Assets and Gaps**:
{self._format_assets_and_gaps(batch_assets, intelligent_gaps)}

**Task**:
Create a data awareness map for ONLY these {len(batch_assets)} assets showing:
1. For each asset, which data sources have coverage (as percentages)
2. Which gaps are TRUE gaps (no data in ANY source)
3. Which fields have data-exists-elsewhere (with source and value)
4. Common gaps across these assets

**Output Format** (JSON - COMPLETE AND VALID):
{{
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
                {{"field": "field_name", "priority": "critical", "section": "infrastructure"}}
            ],
            "data_exists_elsewhere": [
                {{"field": "field_name", "found_in": "source.path", "value": "value"}}
            ]
        }}
    ],
    "cross_asset_patterns": {{
        "common_gaps": ["field1", "field2"],
        "common_data_sources": ["custom_attributes"]
    }}
}}

**Critical**: Return ONLY valid, COMPLETE JSON. No markdown, no truncation.
Include ALL {len(batch_assets)} assets in the response.
"""

        # Call multi_model_service for LLM generation
        logger.debug(
            f"Calling multi_model_service for batch {batch_num}/{total_batches}"
        )

        response_data = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="data_analysis",
            complexity=TaskComplexity.SIMPLE,
            system_message=(
                "You are a data awareness agent. Analyze asset data coverage "
                "and return ONLY valid, COMPLETE JSON without markdown formatting. "
                "Ensure the JSON is properly closed with all brackets matched."
            ),
        )

        response_text = response_data.get("response", "")

        if not response_text:
            raise Exception(f"Empty response for batch {batch_num}")

        logger.debug(
            f"Batch {batch_num} response: {len(response_text)} characters, "
            f"tokens_used={response_data.get('tokens_used', 0)}"
        )

        # Parse LLM response
        return self._parse_llm_response(response_text, batch_num)

    def _parse_llm_response(self, response_text: str, batch_num: int) -> Dict[str, Any]:
        """
        Parse LLM response with robust error handling.

        Args:
            response_text: Raw LLM response string
            batch_num: Batch number for logging

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If JSON parsing fails
        """
        import json
        import re

        # Strip markdown code blocks if present (per ADR-029)
        cleaned = re.sub(r"```json\s*|\s*```", "", response_text).strip()

        # ✅ FIX Bug #15 (LLM JSON Parsing with Literal Ellipsis)
        cleaned = re.sub(r":\s*\.\.\.(\s*[,}])", r": []\1", cleaned)
        cleaned = re.sub(r",\s*\.\.\.\s*,", ", ", cleaned)
        cleaned = re.sub(r",\s*\.\.\.\s*\]", "]", cleaned)

        # ✅ FIX Bug #20 (Truncated LLM Response Repair)
        cleaned = self._repair_truncated_json(cleaned)

        try:
            data_map = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Batch {batch_num} JSON parsing failed: {e}")
            logger.error(f"Cleaned response: {cleaned[:500]}...")

            try:
                import dirtyjson

                data_map = dirtyjson.loads(cleaned)
                logger.warning(f"Batch {batch_num} used dirtyjson fallback")
            except Exception as dirtyjson_error:
                logger.error(f"Batch {batch_num} dirtyjson failed: {dirtyjson_error}")
                raise ValueError(f"Unable to parse batch {batch_num} JSON: {e}") from e

        # Sanitize for JSON serialization
        data_map = sanitize_for_json(data_map)

        return data_map

    def _generate_recommendations(
        self, common_gaps: set, common_data_sources: set
    ) -> List[str]:
        """
        Generate recommendations based on aggregated cross-asset patterns.

        Args:
            common_gaps: Set of common gap field names
            common_data_sources: Set of common data source names

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if "custom_attributes" in common_data_sources:
            recommendations.append(
                "Use custom_attributes for additional fields - already well-populated"
            )

        if common_gaps:
            gap_list = ", ".join(list(common_gaps)[:5])
            recommendations.append(
                f"Common missing fields across assets: {gap_list} - "
                "consider bulk data import"
            )

        if "enrichment_data" not in common_data_sources:
            recommendations.append(
                "Populate enrichment_data tables for resilience and tech debt info"
            )

        if not recommendations:
            recommendations.append("Data coverage is good across all sources")

        return recommendations

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

    def _repair_truncated_json(self, json_str: str) -> str:
        """
        Attempt to repair truncated JSON by closing unclosed brackets.

        LLM responses often get truncated mid-JSON due to token limits (per ADR-035).
        This method attempts to repair the JSON by:
        1. Removing trailing incomplete strings (e.g., "value": "incomplete...)
        2. Removing trailing incomplete keys (e.g., "field":)
        3. Closing unclosed brackets in the correct order

        Args:
            json_str: Potentially truncated JSON string

        Returns:
            Repaired JSON string (best effort)

        Example:
            Input:  '{"assets": [{"name": "Test", "gaps": ['
            Output: '{"assets": [{"name": "Test", "gaps": []}]}'
        """
        import re

        # Remove trailing incomplete string values (e.g., "field": "incompletetext...)
        # Match pattern: "key": "value... (without closing quote)
        json_str = re.sub(r',?\s*"[^"]*":\s*"[^"]*$', "", json_str)

        # Remove trailing incomplete values after colon (e.g., "field": 123... or "field": tru)
        json_str = re.sub(r',?\s*"[^"]*":\s*[^,\]\}]*$', "", json_str)

        # Remove trailing comma before attempting to close brackets
        json_str = re.sub(r",\s*$", "", json_str)

        # Count unclosed brackets
        open_braces = json_str.count("{") - json_str.count("}")
        open_brackets = json_str.count("[") - json_str.count("]")

        # Build closing sequence by analyzing the structure
        # We need to close in reverse order of how they were opened
        closing_sequence = []

        # Simple approach: close brackets then braces
        # This works for most LLM-generated JSON structures
        for _ in range(open_brackets):
            closing_sequence.append("]")
        for _ in range(open_braces):
            closing_sequence.append("}")

        # Append closing sequence
        if closing_sequence:
            logger.warning(
                f"🔧 Bug #20: Repaired truncated JSON by adding: {''.join(closing_sequence)}"
            )
            json_str = json_str + "".join(closing_sequence)

        return json_str
