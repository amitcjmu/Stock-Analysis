"""
Questionnaire Generation Tools
Tools for generating adaptive questionnaire questions based on gaps.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class QuestionnaireGenerationTool:
    """Tool for generating adaptive questionnaire questions based on gaps."""

    def __init__(self):
        self.name = "questionnaire_generation"
        self.description = "Generate adaptive questions based on asset gaps and context"

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
            basic_questions = []
            basic_questions.append(
                {
                    "field_id": "collection_date",
                    "question_text": "When was this information collected?",
                    "field_type": "date",
                    "required": False,
                    "category": "metadata",
                    "help_text": "Date when this data collection occurred",
                }
            )

            sections.append(
                {
                    "section_id": "basic_information",
                    "section_title": "Basic Information",
                    "section_description": "General information about the assets being collected",
                    "questions": basic_questions,
                }
            )

            # Section 2: Critical Missing Fields
            missing_fields = data_gaps.get("missing_critical_fields", {})
            if missing_fields:
                critical_questions = []
                for asset_id, fields in missing_fields.items():
                    for field in fields:
                        # Generate question for each missing field
                        asset_context = {
                            "asset_id": asset_id,
                            "asset_name": f"Asset {asset_id[:8]}",
                            "field_name": field,
                        }
                        question = self._generate_missing_field_question(
                            {}, asset_context
                        )
                        critical_questions.append(question)

                if critical_questions:
                    sections.append(
                        {
                            "section_id": "critical_fields",
                            "section_title": "Critical Missing Information",
                            "section_description": (
                                "Please provide the following critical information "
                                "required for migration planning"
                            ),
                            "questions": critical_questions,
                        }
                    )

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
        asset_analysis: Dict[str, Any],
        gap_type: str,
        asset_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate questions for a specific gap type and asset.

        Args:
            asset_analysis: Comprehensive analysis of the asset
            gap_type: Type of gap to address (e.g., 'missing_field', 'unmapped_attribute')
            asset_context: Context about the specific asset

        Returns:
            Generated question structure
        """
        try:
            if gap_type == "missing_field":
                return self._generate_missing_field_question(
                    asset_analysis, asset_context
                )
            elif gap_type == "unmapped_attribute":
                return self._generate_unmapped_attribute_question(
                    asset_analysis, asset_context
                )
            elif gap_type == "data_quality":
                return self._generate_data_quality_question(
                    asset_analysis, asset_context
                )
            elif gap_type == "dependency":
                return self._generate_dependency_question(asset_analysis, asset_context)
            elif gap_type == "technical_detail":
                return self._generate_technical_detail_question(
                    asset_analysis, asset_context
                )
            else:
                return self._generate_generic_question(gap_type, asset_context)

        except Exception as e:
            logger.error(f"Error generating question for gap {gap_type}: {e}")
            return self._generate_fallback_question(gap_type, asset_context)

    def _generate_missing_field_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for missing critical field."""
        field_name = asset_context.get("field_name", "unknown")
        asset_name = asset_context.get("asset_name", "the asset")

        # Map field names to user-friendly questions
        field_questions = {
            "business_owner": {
                "text": f"Who is the business owner responsible for {asset_name}?",
                "help_text": "Enter the name of the person or department that owns this asset "
                "from a business perspective",
                "type": "text",
                "validation": {"required": True, "min_length": 2},
            },
            "technical_owner": {
                "text": f"Who is the technical owner/team responsible for maintaining {asset_name}?",
                "help_text": "Enter the name of the technical team or individual responsible for this asset",
                "type": "text",
                "validation": {"required": True, "min_length": 2},
            },
            "six_r_strategy": {
                "text": f"What is the recommended migration strategy for {asset_name}?",
                "help_text": "Select the most appropriate 6R strategy for migrating this asset",
                "type": "select",
                "options": [
                    {"value": "rehost", "label": "Rehost (Lift & Shift)"},
                    {"value": "replatform", "label": "Replatform (Lift & Reshape)"},
                    {"value": "refactor", "label": "Refactor (Re-architect)"},
                    {"value": "repurchase", "label": "Repurchase (Replace with SaaS)"},
                    {"value": "retire", "label": "Retire (Decommission)"},
                    {"value": "retain", "label": "Retain (Keep as-is)"},
                ],
                "validation": {"required": True},
            },
            "migration_complexity": {
                "text": f"How complex is the migration for {asset_name}?",
                "help_text": "Assess the complexity based on dependencies, architecture, and technical debt",
                "type": "select",
                "options": [
                    {
                        "value": "low",
                        "label": "Low - Simple migration with minimal dependencies",
                    },
                    {
                        "value": "medium",
                        "label": "Medium - Moderate complexity with some dependencies",
                    },
                    {
                        "value": "high",
                        "label": "High - Complex with many dependencies and technical challenges",
                    },
                    {
                        "value": "very_high",
                        "label": "Very High - Extremely complex requiring significant refactoring",
                    },
                ],
                "validation": {"required": True},
            },
            "dependencies": {
                "text": f"What are the key dependencies for {asset_name}?",
                "help_text": (
                    "List other systems, databases, or services that this asset depends on or that depend on it"
                ),
                "type": "textarea",
                "validation": {"required": True, "min_length": 10},
            },
            "operating_system": {
                "text": f"What operating system does {asset_name} run on?",
                "help_text": "Specify the operating system and version if known",
                "type": "text",
                "validation": {"required": True, "min_length": 2},
            },
        }

        question_config = field_questions.get(
            field_name,
            {
                "text": f"Please provide information for the {field_name.replace('_', ' ')} field for {asset_name}",
                "help_text": f"This information is needed for {field_name.replace('_', ' ')}",
                "type": "text",
                "validation": {"required": True},
            },
        )

        return {
            "field_id": field_name,
            "question_text": question_config["text"],
            "field_type": question_config["type"],
            "required": question_config.get("validation", {}).get("required", True),
            "category": "missing_field",
            "options": question_config.get("options", []),
            "help_text": question_config["help_text"],
            "validation_rules": question_config.get("validation", {}),
            "priority": "high",
            "gap_type": "missing_field",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "metadata": {
                "field_name": field_name,
                "asset_name": asset_name,
                "gap_category": "missing_critical_field",
            },
        }

    def _generate_unmapped_attribute_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for unmapped attribute."""
        attribute_name = asset_context.get("attribute_name", "unknown")
        attribute_value = asset_context.get("attribute_value", "")
        asset_name = asset_context.get("asset_name", "the asset")
        suggested_mapping = asset_context.get("suggested_mapping", "custom_field")

        return {
            "field_id": f"unmapped_{attribute_name}",
            "question_text": (
                f"How should the '{attribute_name}' field (value: '{str(attribute_value)[:50]}...') "
                f"be mapped for {asset_name}?"
            ),
            "field_type": "select",
            "required": False,
            "category": "data_mapping",
            "options": [
                {
                    "value": suggested_mapping,
                    "label": f"Map to {suggested_mapping.replace('_', ' ')}",
                },
                {"value": "custom_attribute", "label": "Store as custom attribute"},
                {"value": "ignore", "label": "Ignore this field"},
                {"value": "manual_review", "label": "Requires manual review"},
            ],
            "help_text": f"This field was found in the imported data but wasn't automatically mapped. "
            f"Suggested mapping: {suggested_mapping}",
            "priority": "medium",
            "gap_type": "unmapped_attribute",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "metadata": {
                "attribute_name": attribute_name,
                "attribute_value": str(attribute_value)[:100],
                "suggested_mapping": suggested_mapping,
            },
        }

    def _generate_data_quality_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for data quality issue."""
        asset_name = asset_context.get("asset_name", "the asset")
        quality_issue = asset_context.get("quality_issue", "data quality concern")

        return {
            "field_id": f"data_quality_{asset_context.get('asset_id', 'unknown')}",
            "question_text": f"Please verify or provide correct information for {asset_name}",
            "field_type": "textarea",
            "required": True,
            "category": "data_validation",
            "help_text": f"Data quality issue detected: {quality_issue}. Please provide accurate information.",
            "priority": "medium",
            "gap_type": "data_quality",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
        }

    def _generate_dependency_question(
        self, asset_analysis: Dict[str, Any], asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate question for dependency information."""
        asset_name = asset_context.get("asset_name", "the asset")

        return {
            "field_id": f"dependencies_{asset_context.get('asset_id', 'unknown')}",
            "question_text": f"What systems or services does {asset_name} depend on?",
            "field_type": "textarea",
            "required": True,
            "category": "dependencies",
            "help_text": "List all systems, databases, APIs, or services that this asset depends on. "
            "Include both inbound and outbound dependencies.",
            "priority": "high",
            "gap_type": "dependency",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "validation_rules": {
                "min_length": 10,
                "required": True,
            },
            "metadata": {
                "dependency_type": "unknown",
                "analysis_required": True,
            },
        }

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
        asset_name = asset_context.get("asset_name", "the asset")

        return {
            "field_id": f"technical_{asset_context.get('asset_id', 'unknown')}",
            "question_text": f"Please provide technical details for {asset_name}",
            "field_type": "textarea",
            "required": True,
            "category": "technical_details",
            "help_text": (
                "Please provide any relevant technical information that would be helpful for migration planning"
            ),
            "priority": "medium",
            "gap_type": "technical_detail",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
        }

    def _generate_generic_question(
        self, gap_type: str, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate generic question for unknown gap types."""
        asset_name = asset_context.get("asset_name", "the asset")

        return {
            "field_id": f"{gap_type}_{asset_context.get('asset_id', 'unknown')}",
            "question_text": f"Please provide information about {gap_type.replace('_', ' ')} for {asset_name}",
            "field_type": "textarea",
            "required": True,
            "category": "general",
            "help_text": f"Additional information is needed for {gap_type.replace('_', ' ')}",
            "priority": "medium",
            "gap_type": gap_type,
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
        }

    def _generate_fallback_question(
        self, gap_type: str, asset_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback question when generation fails."""
        asset_name = asset_context.get("asset_name", "the asset")

        return {
            "field_id": f"fallback_{gap_type}_{asset_context.get('asset_id', 'unknown')}",
            "question_text": f"Please provide additional information for {asset_name}",
            "field_type": "textarea",
            "required": False,
            "category": "fallback",
            "priority": "low",
            "asset_specific": True,
            "asset_id": asset_context.get("asset_id"),
            "help_text": f"Unable to generate specific question for {gap_type}",
        }
