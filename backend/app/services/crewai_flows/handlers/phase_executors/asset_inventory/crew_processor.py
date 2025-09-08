"""
Crew Processing Logic
Handles crew result processing and input preparation for asset inventory.
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CrewProcessor:
    """Handles crew input preparation and result processing"""

    def __init__(self, state):
        self.state = state

    def prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for the crew"""
        cleaned_data = getattr(self.state, "cleaned_data", [])
        raw_data = getattr(self.state, "raw_data", [])
        field_mappings = getattr(self.state, "field_mappings", {})

        logger.info(
            f"🔍 Asset inventory crew input: {len(cleaned_data)} cleaned_data, {len(raw_data)} raw_data"
        )
        logger.info(
            f"🔍 Field mappings available: {list(field_mappings.keys()) if field_mappings else 'None'}"
        )

        # If cleaned_data is empty but raw_data exists, use raw_data with field mappings
        if not cleaned_data and raw_data:
            logger.info(
                "🔧 Using raw_data since cleaned_data is empty - applying field mappings"
            )

            # Apply field mappings to raw data to create cleaned data
            processed_data = []
            for item in raw_data:
                cleaned_item = {}
                # Apply field mappings
                for source_field, target_field in field_mappings.items():
                    if source_field in item:
                        cleaned_item[target_field] = item[source_field]

                # Also keep original data for reference
                cleaned_item["_original"] = item
                processed_data.append(cleaned_item)

            logger.info(f"✅ Processed {len(processed_data)} items with field mappings")
            return {"cleaned_data": processed_data}

        return {"cleaned_data": cleaned_data}

    def get_crew_context(self) -> Dict[str, Any]:
        """Get context for deduplication tools"""
        # Add context info needed for deduplication tools
        context_info = {
            "client_account_id": getattr(self.state, "client_account_id", None),
            "engagement_id": getattr(self.state, "engagement_id", None),
            "user_id": getattr(self.state, "user_id", None),
            "flow_id": getattr(self.state, "flow_id", None),
        }

        logger.info(
            f"🔧 Providing context for deduplication tools: "
            f"client={context_info['client_account_id']}, "
            f"engagement={context_info['engagement_id']}"
        )

        return {"context_info": context_info}

    def process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process asset inventory crew result and extract asset data - NO FALLBACKS"""
        logger.info(f"🔍 Processing asset inventory crew result: {type(crew_result)}")

        if hasattr(crew_result, "raw") and crew_result.raw:
            logger.info(f"📄 Asset inventory crew raw output: {crew_result.raw}")

            # Try to parse JSON from crew output
            try:
                if "{" in crew_result.raw and "}" in crew_result.raw:
                    start = crew_result.raw.find("{")
                    end = crew_result.raw.rfind("}") + 1
                    json_str = crew_result.raw[start:end]
                    parsed_result = json.loads(json_str)

                    if any(
                        key in parsed_result
                        for key in ["servers", "applications", "devices", "assets"]
                    ):
                        logger.info("✅ Found structured asset data in crew output")
                        return parsed_result
                    else:
                        logger.error(
                            f"❌ Crew returned JSON but missing required keys. Got: {list(parsed_result.keys())}"
                        )
                        raise ValueError(
                            "Asset inventory crew returned JSON without required asset categories"
                        )
                else:
                    logger.error(
                        f"❌ Crew output does not contain valid JSON structure: {crew_result.raw}"
                    )
                    raise ValueError("Asset inventory crew did not return JSON output")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Failed to parse JSON from crew output: {e}")
                logger.error(f"❌ Raw crew output: {crew_result.raw}")
                raise RuntimeError(f"Asset inventory crew output parsing failed: {e}")

        elif isinstance(crew_result, dict):
            # Validate that required keys exist
            if any(
                key in crew_result
                for key in ["servers", "applications", "devices", "assets"]
            ):
                logger.info("✅ Crew returned valid dict with asset data")
                return crew_result
            else:
                logger.error(
                    f"❌ Crew returned dict but missing required asset keys. Got: {list(crew_result.keys())}"
                )
                raise ValueError(
                    "Asset inventory crew returned dict without required asset categories"
                )

        else:
            logger.error(f"❌ Unexpected crew result format: {type(crew_result)}")
            logger.error(f"❌ Crew result: {crew_result}")
            raise RuntimeError(
                f"Asset inventory crew returned unexpected result type: {type(crew_result)}"
            )
