"""
Mapping result summarizer utility.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MappingSummarizer:
    """Utility for summarizing mapping results."""

    @staticmethod
    def create_mapping_summary(
        mappings_created: List[Dict[str, Any]], import_id: str
    ) -> Dict[str, Any]:
        """Create a summary of mapping results."""
        # Log mapping summary
        exact_matches = sum(1 for m in mappings_created if m["match_type"] == "exact")
        partial_matches = sum(
            1 for m in mappings_created if m["match_type"] == "partial"
        )
        unmapped = sum(1 for m in mappings_created if m["match_type"] == "unmapped")

        logger.info(
            f"📊 Mapping summary: {exact_matches} exact, "
            f"{partial_matches} partial, {unmapped} unmapped"
        )

        logger.info(
            f"✅ Generated {len(mappings_created)} field mappings using "
            f"intelligent fallback"
        )

        return {
            "status": "success",
            "message": f"Generated {len(mappings_created)} field mappings",
            "mappings_created": len(mappings_created),
            "import_id": str(import_id),
            "summary": {
                "exact_matches": exact_matches,
                "partial_matches": partial_matches,
                "unmapped": unmapped,
                "total": len(mappings_created),
            },
            "mappings": mappings_created[:10],  # Return first 10 as sample
        }
