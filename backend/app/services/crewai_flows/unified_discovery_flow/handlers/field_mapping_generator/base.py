"""
Base Field Mapping Generator

Contains core functionality and base class for field mapping generation.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FieldMappingGeneratorBase:
    """Base class for field mapping generation functionality"""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime

        return datetime.utcnow().isoformat()

    def _validate_field_mapping(self, mapping: Dict[str, Any]) -> bool:
        """Validate a single field mapping"""
        try:
            required_fields = ["source_field", "target_field"]

            for field in required_fields:
                if not mapping.get(field):
                    return False

            return True

        except Exception:
            return False

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for mapping"""
        try:
            # Convert to lowercase and replace spaces/special chars with underscores
            normalized = field_name.lower().replace(" ", "_").replace("-", "_")
            # Remove special characters except underscores
            import re

            normalized = re.sub(r"[^a-zA-Z0-9_]", "_", normalized)
            # Remove multiple consecutive underscores
            normalized = re.sub(r"_+", "_", normalized)
            # Remove leading/trailing underscores
            normalized = normalized.strip("_")
            return normalized

        except Exception:
            return field_name

    def _suggest_target_field(self, source_field: str, analysis: Dict[str, Any]) -> str:
        """Suggest target field based on source field and analysis"""
        try:
            # Simple field name normalization
            normalized = self._normalize_field_name(source_field)
            return normalized

        except Exception:
            return source_field
