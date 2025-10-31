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

# Import helper modules
from .asset_helpers import AssetHelpers
from .questionnaire_caching import QuestionnaireCaching
from .question_delegation import QuestionDelegation

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
        self._asset_helpers = AssetHelpers()
        self._caching = QuestionnaireCaching()
        self._delegation = QuestionDelegation()

    def _create_basic_info_section(self) -> dict:
        """Create basic information section."""
        return create_basic_info_section()

    def _process_missing_fields(
        self, missing_fields: dict, business_context: dict = None
    ) -> list:
        """Process missing fields and generate sections with asset context.

        Args:
            missing_fields: Dict mapping asset_id -> list of missing attribute names
            business_context: Business context including existing_assets with OS data

        Returns:
            List of section dictionaries with categorized questions
        """
        sections = []

        try:
            from app.services.crewai_flows.tools.critical_attributes_tool.base import (
                CriticalAttributesDefinition,
            )

            # Get the 22 critical attributes mapping
            attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()

            # Extract assets data from business_context for OS-aware question generation
            # The serializer provides comprehensive asset data including operating_system
            assets_data = None
            if business_context:
                assets_data = business_context.get("existing_assets", [])
                logger.info(
                    f"Received {len(assets_data) if assets_data else 0} assets with context "
                    f"for OS-aware question generation"
                )

            # Group missing attributes by category with asset context
            attrs_by_category = group_attributes_by_category(
                missing_fields, attribute_mapping, assets_data
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
                # Pass business_context for OS-aware question generation
                missing_field_sections = self._process_missing_fields(
                    missing_fields, business_context
                )
                sections.extend(missing_field_sections)

            # Section 3: Data Quality Issues
            quality_issues = data_gaps.get("data_quality_issues", {})
            if quality_issues:
                quality_questions = []
                for asset_id, issue_data in quality_issues.items():
                    # CRITICAL FIX: Use actual asset name instead of UUID prefix
                    asset_name = await self._asset_helpers.get_asset_name(
                        asset_id, business_context
                    )
                    asset_context = {
                        "asset_id": asset_id,
                        "asset_name": asset_name,
                        "quality_issue": (
                            f"Completeness: {issue_data.get('completeness', 0):.0%}, "
                            f"Confidence: {issue_data.get('confidence', 0):.0%}"
                        ),
                    }
                    question = self._delegation.generate_data_quality_question(
                        {}, asset_context
                    )
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
                    # CRITICAL FIX: Use actual asset name instead of UUID prefix
                    asset_name = await self._asset_helpers.get_asset_name(
                        asset_id, business_context
                    )
                    for attr in attributes[
                        :5
                    ]:  # Limit to 5 per asset to avoid overwhelming
                        asset_context = {
                            "asset_id": asset_id,
                            "asset_name": asset_name,
                            "attribute_name": attr.get("field"),
                            "attribute_value": attr.get("value"),
                            "suggested_mapping": attr.get("potential_mapping"),
                        }
                        question = (
                            self._delegation.generate_unmapped_attribute_question(
                                {}, asset_context
                            )
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

            # REMOVED: Section 5 - Technical Details (legacy fallback)
            # This section generated free-form text questions that cannot be processed by 6R engine.
            # All critical technical information is now captured via structured MCQ questions
            # in the critical attributes framework (architecture, tech stack, dependencies, etc.)

            # Return structured response
            # Extract assets_with_gaps from data_gaps for metadata
            assets_with_gaps = data_gaps.get("assets_with_gaps", [])

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

    async def generate_questions_for_asset(
        self,
        asset_id: str,
        asset_type: str,
        gaps: list,
        client_account_id: int,
        engagement_id: int,
        db_session,
        business_context: Dict[str, Any] = None,
    ) -> list:
        """
        Generate questions for asset with caching.

        Checks cache first, generates only if needed.
        Per BULK_UPLOAD_ENRICHMENT_ARCHITECTURE_ANALYSIS.md Part 6.2:
        Enables 90% cache hit rate for similar assets.

        Args:
            asset_id: Asset UUID
            asset_type: Type of asset (database, server, application)
            gaps: List of missing field names
            client_account_id: Client account ID
            engagement_id: Engagement ID
            db_session: Database session
            business_context: Optional business context

        Returns:
            List of question dictionaries
        """
        # Create gap pattern signature
        gap_pattern = self._caching.create_gap_pattern(gaps)

        # Get memory manager
        memory_manager = self._caching.get_memory_manager(db_session)

        # Check cache FIRST
        cached_result = await memory_manager.retrieve_questionnaire_template(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            asset_type=asset_type,
            gap_pattern=gap_pattern,
        )

        if cached_result.get("cache_hit"):
            logger.info(
                f"✅ Cache HIT for {asset_type}_{gap_pattern} "
                f"(usage_count: {cached_result.get('usage_count', 0)})"
            )

            # Customize questions for this asset
            asset_name = await self._asset_helpers.get_asset_name(
                asset_id, business_context
            )
            customized_questions = self._caching.customize_questions(
                cached_result.get("questions", []), asset_id, asset_name
            )

            return customized_questions

        # Cache MISS - generate fresh (deterministic, not LLM-based)
        logger.info(
            f"❌ Cache MISS - generating deterministically for {asset_type}_{gap_pattern}"
        )

        # Generate questions using existing deterministic logic
        # This calls the existing _arun method which builds questions from data_gaps
        data_gaps = {
            "missing_critical_fields": {asset_id: gaps},
            "assets_with_gaps": [asset_id],
        }

        generation_result = await self._arun(
            data_gaps=data_gaps, business_context=business_context or {}
        )

        # Extract sections and questions from result
        # Per Qodo Bot review: Preserve section structure instead of flattening
        questionnaire_sections = []
        questions = []
        if generation_result.get("status") == "success":
            questionnaire_sections = generation_result.get("questionnaires", [])
            for section in questionnaire_sections:
                questions.extend(section.get("questions", []))

        # Store in cache for future use with preserved section structure
        if questions and questionnaire_sections:
            await memory_manager.store_questionnaire_template(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                asset_type=asset_type,
                gap_pattern=gap_pattern,
                questions=questions,  # Flat list for backward compatibility
                metadata={
                    "generated_by": "QuestionGenerationTool",
                    "asset_id": asset_id,
                    "gap_count": len(gaps),
                    "sections": questionnaire_sections,  # Preserve section structure
                    "section_count": len(questionnaire_sections),
                },
            )

            logger.info(
                f"✅ Stored {len(questions)} questions in {len(questionnaire_sections)} sections "
                f"for cache key {asset_type}_{gap_pattern}"
            )

        return questions
