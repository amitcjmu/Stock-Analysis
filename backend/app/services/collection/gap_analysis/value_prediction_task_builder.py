"""
Gap Value Prediction Task Builder

Builds AI agent tasks for predicting actual VALUES for data gaps.
This is Phase 3 (Agentic Gap Resolution) - different from Phase 2 (gap discovery).
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_gap_value_prediction_task(
    gaps: List[Dict[str, Any]],
    assets: List[Any],
    asset_context: Dict[str, Any],
) -> str:
    """Build task for AI to predict VALUES for existing gaps.

    Args:
        gaps: List of gap dictionaries to predict values for
        assets: List of Asset objects for context
        asset_context: Filtered asset data (from context_filter)

    Returns:
        Task description string for CrewAI agent
    """
    # Build asset lookup for context
    asset_lookup = {str(a.id): a for a in assets}

    # Group gaps by asset
    gaps_by_asset = {}
    for gap in gaps:
        asset_id = str(gap.get("asset_id"))
        if asset_id not in gaps_by_asset:
            gaps_by_asset[asset_id] = []
        gaps_by_asset[asset_id].append(gap)

    # Build comprehensive context for each asset's gaps
    assets_with_gaps = []
    for asset_id, asset_gaps in gaps_by_asset.items():
        asset = asset_lookup.get(asset_id)
        if not asset:
            continue

        # Extract available data from asset
        asset_data = {
            "id": str(asset.id),
            "name": asset.name,
            "asset_type": asset.asset_type,
            "operating_system": asset.operating_system,
            "os_version": asset.os_version,
            "environment": asset.environment,
            "datacenter": asset.datacenter,
            "custom_attributes": asset.custom_attributes or {},
            "technical_details": asset.technical_details or {},
        }

        # Add gaps needing value prediction
        asset_data["gaps_to_predict"] = [
            {
                "field_name": g.get("field_name"),
                "gap_category": g.get("gap_category"),
                "priority": g.get("priority"),
                "current_value": g.get("current_value"),
                "suggested_resolution": g.get("suggested_resolution"),
            }
            for g in asset_gaps
        ]

        assets_with_gaps.append(asset_data)

    return f"""
TASK: Predict actual VALUES for {len(gaps)} data gaps across {len(assets_with_gaps)} assets.

CRITICAL INSTRUCTIONS:
1. For each gap, predict the ACTUAL VALUE (not just a suggestion)
2. Base predictions on available asset data (custom_attributes, technical_details, etc.)
3. Provide confidence score (0.0-1.0) based on evidence strength
4. Explain WHY you predicted each value (reasoning)
5. Return ONLY valid JSON (no markdown, no explanations outside JSON)

ASSETS WITH GAPS TO PREDICT ({len(assets_with_gaps)} assets):
{json.dumps(assets_with_gaps, indent=2)}

PREDICTION GUIDELINES:

1. **Evidence-Based Confidence Scoring**:
   - 0.9-1.0: Strong direct evidence (e.g., custom_attributes.os = "RHEL 8")
   - 0.7-0.8: Moderate inference (e.g., environment="rhel-prod" → likely RHEL)
   - 0.5-0.6: Weak inference (e.g., datacenter pattern suggests OS)
   - 0.0-0.4: No evidence, best practice guess

2. **Prediction Examples**:
   ```
   Gap: "operating_system" missing
   Available: custom_attributes.environment = "linux-prod"
   Prediction: "Linux"
   Confidence: 0.75
   Reasoning: "Inferred from environment='linux-prod' custom attribute"
   ```

   ```
   Gap: "cpu_cores" missing
   Available: custom_attributes.vm_size = "Standard_D4s_v3"
   Prediction: "4"
   Confidence: 0.90
   Reasoning: "Azure VM size D4s_v3 specification includes 4 vCPUs"
   ```

   ```
   Gap: "technology_stack" missing
   Available: custom_attributes.runtime = "nodejs-16"
   Prediction: "Node.js 16"
   Confidence: 0.95
   Reasoning: "Direct evidence from custom_attributes.runtime field"
   ```

3. **When NO Evidence Exists**:
   - DO still make a prediction (industry standard/best practice)
   - Set confidence < 0.4
   - Explain: "No direct evidence - industry standard assumption"

4. **Field-Specific Prediction Logic**:
   - **operating_system**: Check custom_attributes, environment names, datacenter patterns
   - **technology_stack**: Check custom_attributes, asset_type, naming conventions
   - **cpu_cores/memory**: Check VM size names, custom_attributes, asset_type
   - **compliance**: Check environment (prod likely needs compliance), industry standards

RETURN JSON FORMAT (predict ALL {len(gaps)} gaps):
{{
    "predictions": [
        {{
            "asset_id": "EXACT_UUID_FROM_INPUT",
            "field_name": "EXACT_FIELD_FROM_INPUT",
            "predicted_value": "Actual predicted value (e.g., 'RHEL 8.5', '4', 'Node.js 16')",
            "prediction_confidence": 0.85,
            "prediction_reasoning": "Detailed explanation of why this value was predicted based on available evidence"
        }},
        ...
    ],
    "summary": {{
        "total_predictions": {len(gaps)},
        "high_confidence_count": 0,  // confidence >= 0.7
        "medium_confidence_count": 0,  // 0.4 <= confidence < 0.7
        "low_confidence_count": 0  // confidence < 0.4
    }}
}}

CRITICAL REMINDERS:
- Predict ALL {len(gaps)} gaps in a SINGLE response
- Use EXACT asset_id and field_name from input
- Provide SPECIFIC values, not generic suggestions
- Base confidence on ACTUAL available evidence
- DO NOT USE TOOLS - Return JSON directly
"""


def build_single_asset_value_prediction_task(
    asset_gaps: List[Dict[str, Any]],
    asset_context: Dict[str, Any],
) -> str:
    """Build prediction task for ONE asset (batched approach).

    Args:
        asset_gaps: Gaps for this asset only
        asset_context: Filtered asset context

    Returns:
        Task description for agent
    """
    return f"""
TASK: Predict VALUES for {len(asset_gaps)} data gaps for ONE asset.

ASSET CONTEXT:
{json.dumps(asset_context, indent=2)}

GAPS TO PREDICT ({len(asset_gaps)} gaps):
{json.dumps(asset_gaps, indent=2)}

INSTRUCTIONS:
1. Use available asset context to predict actual values
2. Assign confidence based on evidence strength (0.0-1.0)
3. Explain reasoning for each prediction
4. Return ONLY valid JSON

PREDICTION EXAMPLES:
- Gap: "os", custom_attributes has "environment": "rhel8-prod"
  → Prediction: "RHEL 8", Confidence: 0.85, Reasoning: "Inferred from environment name"

- Gap: "cpu_cores", technical_details has "vm_size": "Standard_D4s"
  → Prediction: "4", Confidence: 0.90, Reasoning: "Azure D4s VM has 4 vCPUs"

- Gap: "technology_stack", no evidence
  → Prediction: "Unknown", Confidence: 0.20, Reasoning: "No evidence available"

RETURN JSON:
{{
    "predictions": [
        {{
            "asset_id": "{asset_context.get('id')}",
            "field_name": "EXACT_FIELD_FROM_INPUT",
            "predicted_value": "Actual value",
            "prediction_confidence": 0.85,
            "prediction_reasoning": "Why this value was predicted"
        }}
    ],
    "summary": {{
        "total_predictions": {len(asset_gaps)}
    }}
}}

CRITICAL: Return ONLY valid JSON, no markdown, no explanations.
"""
