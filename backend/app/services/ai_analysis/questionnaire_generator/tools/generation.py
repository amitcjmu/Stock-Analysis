"""
Questionnaire Generation Tools
Tools for generating adaptive questionnaire questions based on gaps.
"""

import logging
from typing import Any, Dict

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import section builder functions
from .section_builders import (
    create_basic_info_section,
    create_category_sections,
    create_fallback_section,
    group_attributes_by_category,
)

# Import question builder functions
from .question_builders import (
    generate_data_quality_question,
    generate_dependency_question,
    generate_fallback_question,
    generate_generic_question,
    generate_generic_technical_question,
    generate_missing_field_question,
    generate_unmapped_attribute_question,
)

logger = logging.getLogger(__name__)


class QuestionnaireGenerationInput(BaseModel):
    """Input schema for questionnaire generation"""

    data_gaps: Dict[str, Any] = Field(
        description="Dictionary containing missing_critical_fields and gap analysis data"
    )
    business_context: Dict[str, Any] = Field(
        default={}, description="Business context including engagement and client info"
    )


class QuestionnaireGenerationTool(BaseTool):
    """Tool for generating adaptive questionnaire questions based on gaps."""

    name: str = "questionnaire_generation"
    description: str = (
        "Generate adaptive questions based on asset gaps and context using 22 critical attributes"
    )
    args_schema: type[BaseModel] = QuestionnaireGenerationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _create_basic_info_section(self) -> dict:
        """Create basic information section."""
        return create_basic_info_section()

    def _process_missing_fields(self, missing_fields: dict) -> list:
        """Process missing fields and generate sections."""
        sections = []

        try:
            from app.services.crewai_flows.tools.critical_attributes_tool.base import (
                CriticalAttributesDefinition,
            )

            # Get the 22 critical attributes mapping
            attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()

            # Group missing attributes by category
            attrs_by_category = group_attributes_by_category(
                missing_fields, attribute_mapping
            )

            # Create organized sections by category
            sections = create_category_sections(attrs_by_category)

            logger.info(
                f"Generated {len(sections)} sections using 22 critical attributes"
            )

        except ImportError as e:
            logger.warning(
                f"Critical attributes system not available, using fallback: {e}"
            )
            fallback_section = create_fallback_section(missing_fields)
            if fallback_section:
                sections.append(fallback_section)

        return sections

    async def _arun(
        self,
        data_gaps: Dict[str, Any],
        business_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Async method for generating comprehensive questionnaires from data gaps.

        This is the PRIMARY method called by agents. It generates multiple sections
        with targeted questions based on gap analysis.

        Args:
            data_gaps: Dict containing missing_critical_fields, unmapped_attributes, etc.
            business_context: Context about the engagement, assets, etc.

        Returns:
            Structured dict with status and questionnaires containing sections and questions
        """
        try:
            logger.info(
                f"Generating questionnaires from data gaps for {business_context.get('total_assets', 0)} assets"
            )

            sections = []

            # Section 1: Basic Information (always included)
            sections.append(self._create_basic_info_section())

            # Section 2-N: Generate comprehensive sections using 22 critical attributes
            missing_fields = data_gaps.get("missing_critical_fields", {})

            # Defensive type checking: Ensure missing_fields is a dict, not a list
            # Root cause: Sometimes agents or data transformations may return list format
            if isinstance(missing_fields, list):
                logger.warning(
                    f"missing_critical_fields is a list (length={len(missing_fields)}), "
                    "converting to dict format expected by group_attributes_by_category"
                )
                # Convert list to dict with single asset entry
                # This handles cases where gaps are aggregated without asset_id mapping
                missing_fields = (
                    {"aggregated": missing_fields} if missing_fields else {}
                )

            if missing_fields:
                missing_field_sections = self._process_missing_fields(missing_fields)
                sections.extend(missing_field_sections)

            # Section 3: Data Quality Issues
            quality_issues = data_gaps.get("data_quality_issues", {})
            if quality_issues:
                quality_questions = []
                for asset_id, issue_data in quality_issues.items():
                    asset_context = {
                        "asset_id": asset_id,
                        "asset_name": f"Asset {asset_id[:8]}",
                        "quality_issue": (
                            f"Completeness: {issue_data.get('completeness', 0):.0%}, "
                            f"Confidence: {issue_data.get('confidence', 0):.0%}"
                        ),
                    }
                    question = self._generate_data_quality_question({}, asset_context)
                    quality_questions.append(question)

                if quality_questions:
                    sections.append(
                        {
                            "section_id": "data_quality",
                            "section_title": "Data Quality Verification",
                            "section_description": "Please verify or correct the following information",
                            "questions": quality_questions,
                        }
                    )

            # Section 4: Unmapped Attributes
            unmapped = data_gaps.get("unmapped_attributes", {})
            if unmapped:
                unmapped_questions = []
                for asset_id, attributes in unmapped.items():
                    for attr in attributes[
                        :5
                    ]:  # Limit to 5 per asset to avoid overwhelming
                        asset_context = {
                            "asset_id": asset_id,
                            "asset_name": f"Asset {asset_id[:8]}",
                            "attribute_name": attr.get("field"),
                            "attribute_value": attr.get("value"),
                            "suggested_mapping": attr.get("potential_mapping"),
                        }
                        question = self._generate_unmapped_attribute_question(
                            {}, asset_context
                        )
                        unmapped_questions.append(question)

                if unmapped_questions:
                    sections.append(
                        {
                            "section_id": "unmapped_attributes",
                            "section_title": "Unmapped Data Fields",
                            "section_description": "Help us map the following fields from your data",
                            "questions": unmapped_questions,
                        }
                    )

            # Section 5: Technical Details (for assets with gaps)
            assets_with_gaps = data_gaps.get("assets_with_gaps", [])
            if assets_with_gaps:
                technical_questions = []
                for asset_id in assets_with_gaps[:3]:  # Limit to first 3 assets
                    asset_context = {
                        "asset_id": asset_id,
                        "asset_name": f"Asset {asset_id[:8]}",
                        "asset_type": "application",  # Default, should come from actual asset data
                    }
                    question = self._generate_technical_detail_question(
                        {}, asset_context
                    )
                    technical_questions.append(question)

                if technical_questions:
                    sections.append(
                        {
                            "section_id": "technical_details",
                            "section_title": "Technical Details",
                            "section_description": "Additional technical information needed for migration planning",
                            "questions": technical_questions,
                        }
                    )

            # Return structured response
            result = {
                "status": "success",
                "questionnaires": sections,  # Note: using 'questionnaires' key as expected by parser
                "metadata": {
                    "total_sections": len(sections),
                    "total_questions": sum(len(s["questions"]) for s in sections),
                    "assets_analyzed": business_context.get("total_assets", 0),
                    "assets_with_gaps": len(assets_with_gaps),
                },
            }

            logger.info(
                f"Generated {len(sections)} sections with {result['metadata']['total_questions']} total questions"
            )
            return result

        except Exception as e:
            logger.error(f"Error in _arun questionnaire generation: {e}", exc_info=True)
            # Return error response
            return {"status": "error", "error": str(e), "questionnaires": []}

    def _run(
        self,
        data_gaps: Dict[str, Any],
        business_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for _arun method.

        Args:
            data_gaps: Dict containing missing_critical_fields and gap analysis data
            business_context: Business context including engagement and client info

        Returns:
            Generated questionnaire structure
        """
        import asyncio

        # Use async implementation
        return asyncio.run(self._arun(data_gaps, business_context or {}))

    def _generate_missing_field_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for missing critical field."""
        return generate_missing_field_question(asset_analysis, asset_context)

    def _generate_unmapped_attribute_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for unmapped attribute."""
        return generate_unmapped_attribute_question(asset_analysis, asset_context)

    def _generate_data_quality_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for data quality issue."""
        return generate_data_quality_question(asset_analysis, asset_context)

    def _generate_dependency_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for dependency information."""
        return generate_dependency_question(asset_analysis, asset_context)

    def _generate_technical_detail_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for missing technical details."""
        asset_type = asset_context.get("asset_type", "application").lower()

        if asset_type == "database":
            return self._generate_database_technical_question(asset_context)
        elif asset_type == "application":
            return self._generate_application_technical_question(asset_context)
        elif asset_type == "server":
            return self._generate_server_technical_question(asset_context)
        else:
            return self._generate_generic_technical_question(asset_context)

    def _generate_database_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical questions specific to database assets."""
        from .question_generators import generate_database_technical_question

        return generate_database_technical_question(asset_context)

    def _generate_application_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical questions specific to application assets."""
        from .question_generators import generate_application_technical_question

        return generate_application_technical_question(asset_context)

    def _generate_server_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical questions specific to server assets."""
        from .question_generators import generate_server_technical_question

        return generate_server_technical_question(asset_context)

    def _generate_generic_technical_question(
        self, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate generic technical question for unknown asset types."""
        return generate_generic_technical_question(asset_context)

    def _generate_generic_question(
        self, gap_type: str, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate generic question for unknown gap types."""
        return generate_generic_question(gap_type, asset_context)

    def _generate_fallback_question(
        self, gap_type: str, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback question when generation fails."""
        return generate_fallback_question(gap_type, asset_context)
