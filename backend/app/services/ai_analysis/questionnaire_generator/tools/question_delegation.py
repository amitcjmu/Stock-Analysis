"""
Question Generation Delegation
Delegates question generation to appropriate specialized generators.
"""

from typing import Any, Dict

from .question_builders import (
    generate_data_quality_question,
    generate_dependency_question,
    generate_fallback_question,
    generate_generic_question,
    generate_generic_technical_question,
    generate_missing_field_question,
    generate_unmapped_attribute_question,
)


class QuestionDelegation:
    """Handles delegation of question generation to specialized generators."""

    def generate_missing_field_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for missing critical field."""
        return generate_missing_field_question(asset_analysis, asset_context)

    def generate_unmapped_attribute_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for unmapped attribute."""
        return generate_unmapped_attribute_question(asset_analysis, asset_context)

    def generate_data_quality_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for data quality issue."""
        return generate_data_quality_question(asset_analysis, asset_context)

    def generate_dependency_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for dependency information."""
        return generate_dependency_question(asset_analysis, asset_context)

    def generate_technical_detail_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for missing technical details."""
        asset_type = asset_context.get("asset_type", "application").lower()

        if asset_type == "database":
            return self.generate_database_technical_question(asset_context)
        elif asset_type == "application":
            return self.generate_application_technical_question(asset_context)
        elif asset_type == "server":
            return self.generate_server_technical_question(asset_context)
        else:
            return self.generate_generic_technical_question(asset_context)

    def generate_database_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical questions specific to database assets."""
        from .question_generators import generate_database_technical_question

        return generate_database_technical_question(asset_context)

    def generate_application_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical questions specific to application assets."""
        from .question_generators import generate_application_technical_question

        return generate_application_technical_question(asset_context)

    def generate_server_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical questions specific to server assets."""
        from .question_generators import generate_server_technical_question

        return generate_server_technical_question(asset_context)

    def generate_generic_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate generic technical question for unknown asset types."""
        return generate_generic_technical_question(asset_context)

    def generate_generic_question(
        self, gap_type: str, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate generic question for unknown gap types."""
        return generate_generic_question(gap_type, asset_context)

    def generate_fallback_question(
        self, gap_type: str, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback question when generation fails."""
        return generate_fallback_question(gap_type, asset_context)
