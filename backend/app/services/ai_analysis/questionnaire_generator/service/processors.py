"""
Questionnaire Processors
Handles questionnaire result processing and validation.
"""

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class QuestionnaireProcessor:
    """Handles questionnaire result processing"""

    def __init__(self, agents: List[Any], tasks: List[Any], name: str):
        self.agents = agents
        self.tasks = tasks
        self.name = name

    def _parse_raw_results(self, raw_results: Any) -> Dict[str, Any]:
        """Parse and normalize raw results into a dictionary."""
        if isinstance(raw_results, str):
            try:
                import re

                # First attempt: direct JSON parsing
                try:
                    return json.loads(raw_results)
                except json.JSONDecodeError:
                    pass

                # Second attempt: extract JSON from text
                json_match = re.search(r"\{.*\}", raw_results, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass

                # Third attempt: structured text parsing
                from ..utils import parse_text_results

                return parse_text_results(raw_results)

            except Exception as e:
                logger.warning(f"Failed to parse raw results: {e}")
                return {
                    "sections": [],
                    "error": "Failed to parse results",
                    "raw_content": str(raw_results),
                }
        elif isinstance(raw_results, dict):
            return raw_results
        elif isinstance(raw_results, list):
            return {"sections": raw_results}
        else:
            return {"sections": [], "raw_content": str(raw_results)}

    def _validate_result_structure(self, parsed_results: Any) -> Dict[str, Any]:
        """Validate and normalize the result structure."""
        if not isinstance(parsed_results, dict):
            return {"sections": []}

        # Ensure we have sections
        sections = parsed_results.get("sections", [])
        if not isinstance(sections, list):
            sections = []

        # Validate each section
        validated_sections = []
        for section in sections:
            if isinstance(section, dict):
                # Ensure required fields
                validated_section = {
                    "section_id": section.get(
                        "section_id", f"section_{len(validated_sections)}"
                    ),
                    "section_title": section.get("section_title", "Generated Section"),
                    "section_description": section.get("section_description", ""),
                    "questions": section.get("questions", []),
                    "validation_rules": section.get("validation_rules", {}),
                    "metadata": section.get("metadata", {}),
                }

                # Validate questions
                validated_questions = []
                for question in validated_section["questions"]:
                    if isinstance(question, dict) and question.get("field_id"):
                        validated_questions.append(question)

                validated_section["questions"] = validated_questions

                # Only add sections with questions
                if validated_questions:
                    validated_sections.append(validated_section)

        return {
            "sections": validated_sections,
            "metadata": parsed_results.get("metadata", {}),
            "status": "success" if validated_sections else "empty_results",
        }

    def _calculate_questionnaire_metrics(self, sections: List[Dict]) -> Dict[str, int]:
        """Calculate metrics for the generated questionnaire."""
        total_questions = sum(len(section.get("questions", [])) for section in sections)
        total_sections = len(sections)

        # Count question types
        question_types = {}
        required_questions = 0

        for section in sections:
            for question in section.get("questions", []):
                field_type = question.get("field_type", "text")
                question_types[field_type] = question_types.get(field_type, 0) + 1

                if question.get("required", False):
                    required_questions += 1

        return {
            "total_sections": total_sections,
            "total_questions": total_questions,
            "required_questions": required_questions,
            "optional_questions": total_questions - required_questions,
            "question_types": question_types,
        }

    def _generate_quality_assessment(self, sections: List[Dict]) -> Dict[str, float]:
        """Generate quality assessment scores."""
        if not sections:
            return {"overall_score": 0.0, "completeness": 0.0, "clarity": 0.0}

        # Import assessment functions
        from ..utils import (
            assess_question_quality,
            assess_user_experience,
            assess_business_alignment,
        )

        try:
            question_quality = assess_question_quality(sections)
            user_experience = assess_user_experience(sections)
            business_alignment = assess_business_alignment(sections)

            overall_score = (
                question_quality + user_experience + business_alignment
            ) / 3

            return {
                "overall_score": overall_score,
                "question_quality": question_quality,
                "user_experience": user_experience,
                "business_alignment": business_alignment,
            }
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return {"overall_score": 0.5, "completeness": 0.5, "clarity": 0.5}

    def _build_final_result(
        self,
        sections: List[Dict],
        metrics: Dict[str, int],
        quality_scores: Dict[str, float],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the final processed result."""
        return {
            "questionnaires": sections,  # For backward compatibility
            "sections": sections,
            "metrics": metrics,
            "quality_assessment": quality_scores,
            "metadata": {
                **metadata,
                "processing_timestamp": logger._get_timestamp(),
                "processor_name": self.name,
                "agent_count": len(self.agents),
                "task_count": len(self.tasks),
            },
            "status": "success" if sections else "no_questionnaires_generated",
            "total_questionnaires": len(sections),
            "summary": {
                "sections_generated": len(sections),
                "total_questions": metrics.get("total_questions", 0),
                "quality_score": quality_scores.get("overall_score", 0.0),
            },
        }

    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """
        Process raw results from questionnaire generation.

        Args:
            raw_results: Raw results from agents/crew execution

        Returns:
            Processed and validated questionnaire results
        """
        try:
            # Parse raw results
            parsed_results = self._parse_raw_results(raw_results)

            # Validate structure
            validated_results = self._validate_result_structure(parsed_results)

            sections = validated_results["sections"]

            # Calculate metrics
            metrics = self._calculate_questionnaire_metrics(sections)

            # Generate quality assessment
            quality_scores = self._generate_quality_assessment(sections)

            # Build final result
            final_result = self._build_final_result(
                sections, metrics, quality_scores, validated_results.get("metadata", {})
            )

            logger.info(
                f"Processed questionnaire results: {len(sections)} sections, "
                f"{metrics['total_questions']} questions, "
                f"quality score: {quality_scores.get('overall_score', 0.0):.2f}"
            )

            return final_result

        except Exception as e:
            logger.error(f"Error processing questionnaire results: {e}")
            return {
                "status": "processing_failed",
                "error": str(e),
                "questionnaires": [],
                "sections": [],
            }

    async def process_asset_batch_with_deduplication(
        self,
        assets: List[Dict[str, Any]],
        question_generator_tool,
        client_account_id: int,
        engagement_id: int,
        db_session,
        business_context: Dict[str, Any] = None,
    ) -> Dict[str, List]:
        """
        Process assets with deduplication.

        Groups by (asset_type, gap_pattern) for 70-80% reduction in generation operations.
        Per BULK_UPLOAD_ENRICHMENT_ARCHITECTURE_ANALYSIS.md Part 6.2.

        Args:
            assets: List of asset dicts with keys: asset_id, asset_type, missing_fields
            question_generator_tool: QuestionGenerationTool instance
            client_account_id: Client account ID
            engagement_id: Engagement ID
            db_session: Database session
            business_context: Optional business context

        Returns:
            Dict mapping asset_id to list of questions
        """
        if not assets:
            logger.warning("No assets provided for batch processing")
            return {}

        # Group by asset_type + gap_pattern
        asset_groups = defaultdict(list)
        for asset in assets:
            asset_id = asset.get("asset_id")
            asset_type = asset.get("asset_type", "application")
            missing_fields = asset.get("missing_fields", [])

            # Create gap pattern (sorted for consistency)
            gap_pattern = (
                "_".join(sorted(missing_fields)) if missing_fields else "no_gaps"
            )
            group_key = f"{asset_type}_{gap_pattern}"

            asset_groups[group_key].append(
                {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "missing_fields": missing_fields,
                    "asset_name": asset.get("asset_name"),
                }
            )

        # Log deduplication stats
        original_count = len(assets)
        deduplicated_count = len(asset_groups)
        deduplication_ratio = (
            (1 - deduplicated_count / original_count) * 100 if original_count > 0 else 0
        )

        logger.info(
            f"✅ Deduplicated {original_count} assets → {deduplicated_count} unique patterns "
            f"({deduplication_ratio:.0f}% reduction)"
        )

        # Generate questions ONCE per group, then apply to all assets in group
        questionnaires = {}

        for group_key, group_assets in asset_groups.items():
            # Use first asset as representative
            representative = group_assets[0]

            logger.info(
                f"Processing group '{group_key}' with {len(group_assets)} assets "
                f"(representative: {representative['asset_id'][:8]})"
            )

            # Generate questions once for the representative asset
            # This will check cache and generate if needed
            try:
                questions = await question_generator_tool.generate_questions_for_asset(
                    asset_id=representative["asset_id"],
                    asset_type=representative["asset_type"],
                    gaps=representative["missing_fields"],
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    db_session=db_session,
                    business_context=business_context,
                )

                # Track cache performance
                # Check if this was a cache hit (questions returned quickly from cache)
                # Note: The tool logs cache hits/misses internally
                if questions:
                    # Apply questions to ALL assets in group
                    for asset in group_assets:
                        # Customize for each asset (only changes asset name/ID)
                        customized_questions = (
                            question_generator_tool._customize_questions(
                                questions,
                                asset["asset_id"],
                                asset.get("asset_name"),
                            )
                        )
                        questionnaires[asset["asset_id"]] = customized_questions

                    logger.info(
                        f"✅ Applied {len(questions)} questions to {len(group_assets)} assets in group '{group_key}'"
                    )
                else:
                    logger.warning(f"⚠️ No questions generated for group '{group_key}'")
                    for asset in group_assets:
                        questionnaires[asset["asset_id"]] = []

            except Exception as e:
                logger.error(
                    f"❌ Error processing group '{group_key}': {e}", exc_info=True
                )
                # Assign empty questionnaires for failed group
                for asset in group_assets:
                    questionnaires[asset["asset_id"]] = []

        # Log summary statistics
        total_questions = sum(len(q) for q in questionnaires.values())
        avg_questions_per_asset = (
            total_questions / len(questionnaires) if questionnaires else 0
        )

        logger.info(
            f"📊 Batch processing complete: "
            f"{len(questionnaires)} assets processed, "
            f"{deduplicated_count} unique patterns, "
            f"{total_questions} total questions generated "
            f"({avg_questions_per_asset:.1f} avg per asset), "
            f"deduplication ratio: {deduplication_ratio:.0f}%"
        )

        return questionnaires
