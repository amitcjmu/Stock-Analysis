"""
Field mapping creator utility for creating individual field mappings.
"""

import logging
from typing import Any, Dict, List

from app.models.data_import import ImportFieldMapping

logger = logging.getLogger(__name__)


class FieldMappingCreator:
    """Utility for creating field mapping records."""

    def __init__(self, db_session, context):
        """Initialize with database session and request context."""
        self.db = db_session
        self.context = context

    def create_field_mapping(
        self,
        source_field: str,
        patterns: Dict[str, List[str]],
        import_uuid,
        client_account_uuid,
    ) -> Dict[str, Any]:
        """Create a single field mapping for a source field."""
        # Normalize field name for comparison
        normalized_source = (
            source_field.lower().replace(" ", "_").replace("-", "_").strip()
        )

        # Find best match from available target fields only
        target_field = None
        confidence_score = 0.0
        match_type = "suggested"

        # Look for exact and partial matches in available target fields
        for target, target_patterns in patterns.items():
            for pattern in target_patterns:
                if pattern.lower() == normalized_source:
                    # Exact match - highest priority
                    target_field = target
                    confidence_score = 0.95
                    match_type = "exact"
                    break
                elif (
                    pattern.lower() in normalized_source
                    or normalized_source in pattern.lower()
                ):
                    # Partial match - only update if better than current
                    if confidence_score < 0.7:
                        target_field = target
                        confidence_score = 0.7
                        match_type = "partial"

            if match_type == "exact":
                break

        # If no good match found, leave as unmapped for user to decide
        if not target_field:
            target_field = "UNMAPPED"
            confidence_score = 0.0
            match_type = "unmapped"
            logger.info(
                f"No target field match found for source field "
                f"'{source_field}', marking as UNMAPPED"
            )
        else:
            logger.info(
                f"Mapped source field '{source_field}' to target field "
                f"'{target_field}' (confidence: {confidence_score}, "
                f"type: {match_type})"
            )

        # Create the field mapping record
        mapping = ImportFieldMapping(
            data_import_id=import_uuid,
            client_account_id=client_account_uuid,
            engagement_id=self.context.engagement_id,
            source_field=source_field,
            target_field=target_field,
            match_type=match_type,
            confidence_score=confidence_score,
            status="suggested" if target_field != "UNMAPPED" else "pending",
            transformation_rules=None,
        )

        self.db.add(mapping)
        return {
            "source": source_field,
            "target": target_field,
            "confidence": confidence_score,
            "match_type": match_type,
        }
