"""
Section Question Generator - Tool-free question generation for collection flow.

Main generator class that orchestrates prompt building and LLM response parsing.
Refactored to keep under 400 lines per pre-commit requirements.

CC Generated for Issue #1113 - SectionQuestionGenerator (Modularized)
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

import json
import logging
from typing import Any, Dict, List, Optional

import dirtyjson

from app.services.collection.gap_analysis.models import IntelligentGap
from app.services.multi_model_service import multi_model_service, TaskComplexity
from app.utils.json_sanitization import sanitize_for_json
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class SectionQuestionGenerator:
    """
    Tool-Free Question Generator for Collection Flow Questionnaires.

    Generates intelligent questions based on TRUE gaps only, with data awareness
    context for intelligent option generation. NO TOOLS configured to eliminate
    4-10s redundant tool calls per section.

    Architecture:
    - Clear, unambiguous prompts (no conflicting instructions)
    - Cross-section deduplication (track questions across sections)
    - Direct JSON generation via multi_model_service (automatic observability)
    - ADR-029 compliant (JSON sanitization for NaN/Infinity)

    Usage:
        generator = SectionQuestionGenerator()
        questions = await generator.generate_questions_for_section(
            asset_name="WebApp-1",
            asset_id="uuid",
            section_name="infrastructure",
            gaps=[...],
            asset_data={...},
            previous_questions=[]
        )
    """

    def __init__(self):
        """Initialize generator with prompt builder."""
        self.prompt_builder = PromptBuilder()

    async def generate_questions_for_section(
        self,
        asset_name: str,
        asset_id: str,
        section_name: str,
        gaps: List[IntelligentGap],
        asset_data: Optional[Dict[str, Any]],
        previous_questions: List[str],
        client_account_id: int,
        engagement_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for a section based on TRUE gaps.

        Args:
            asset_name: Name of asset
            asset_id: Asset UUID
            section_name: Section name (e.g., "infrastructure")
            gaps: List of IntelligentGap objects (TRUE gaps only)
            asset_data: Data map from DataAwarenessAgent
            previous_questions: Questions already generated in other sections
            client_account_id: Multi-tenant client ID (for observability)
            engagement_id: Multi-tenant engagement ID (for observability)

        Returns:
            List of question dicts with field_id, question_text, input_type, etc.
        """
        if not gaps:
            logger.info(f"No TRUE gaps for {asset_name} in {section_name} - skipping")
            return []

        # Build prompt using PromptBuilder
        prompt = self.prompt_builder.build_prompt(
            asset_name=asset_name,
            section_name=section_name,
            gaps=gaps,
            asset_data=asset_data,
            previous_questions=previous_questions,
        )

        # Call multi_model_service for LLM generation (automatic observability)
        logger.debug(
            f"Calling multi_model_service for {section_name} questions "
            f"(asset: {asset_name}, gaps: {len(gaps)})"
        )

        response_data = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="section_question_generator",
            complexity=TaskComplexity.SIMPLE,  # Direct JSON generation
            system_message=(
                "You are a questionnaire generation agent. Generate clear, "
                "specific questions based on TRUE data gaps. Return ONLY valid "
                "JSON, no markdown formatting."
            ),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        # Parse LLM response with ADR-029 sanitization
        questions = self._parse_llm_response(
            response_data.get("content", "{}"), section_name, asset_name
        )

        logger.info(
            f"Generated {len(questions)} questions for {asset_name} in {section_name}"
        )

        return questions

    def _parse_llm_response(
        self, response: str, section_name: str, asset_name: str
    ) -> List[Dict[str, Any]]:
        """
        Parse LLM response with robust error handling (ADR-029).

        Handles:
        - Markdown code blocks (```json)
        - Malformed JSON (trailing commas, single quotes)
        - NaN/Infinity values from confidence scores
        - Missing fields

        Args:
            response: Raw LLM response string
            section_name: Section name (for logging)
            asset_name: Asset name (for logging)

        Returns:
            List of question dicts
        """
        import re

        # Strip markdown code blocks
        cleaned = re.sub(r"```json\s*|\s*```", "", response.strip())

        try:
            # Try standard JSON first
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback to dirtyjson for malformed JSON
            try:
                parsed = dirtyjson.loads(cleaned)
            except Exception as e:
                logger.error(
                    f"Failed to parse LLM response for {asset_name} in {section_name}: {e}"
                )
                logger.error(f"Response was: {cleaned[:500]}")
                return []

        # Sanitize NaN/Infinity values (ADR-029)
        parsed = sanitize_for_json(parsed)

        # Extract questions array
        questions = parsed.get("questions", [])

        if not isinstance(questions, list):
            logger.error(
                f"LLM response 'questions' is not a list for {asset_name} in {section_name}"
            )
            return []

        # Validate each question has required fields
        valid_questions = []
        for q in questions:
            if self._validate_question(q):
                valid_questions.append(q)
            else:
                logger.warning(
                    f"Invalid question format in {section_name}: {q.get('field_id', 'unknown')}"
                )

        return valid_questions

    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """
        Validate question has required fields.

        Args:
            question: Question dict from LLM

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["field_id", "question_text", "input_type"]
        return all(field in question for field in required_fields)
