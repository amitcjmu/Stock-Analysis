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
        client_account_id: str = "",
        engagement_id: str = "",
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
            client_account_id: Multi-tenant client UUID string (for observability)
            engagement_id: Multi-tenant engagement UUID string (for observability)

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

        # ✅ Fix Bug #19: multi_model_service.generate_response() does not accept
        # client_account_id/engagement_id parameters - kept in method signature
        # for potential future observability integration
        response_data = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="section_question_generator",
            complexity=TaskComplexity.SIMPLE,  # Direct JSON generation
            system_message=(
                "You are a questionnaire generation agent. Generate clear, "
                "specific questions based on TRUE data gaps. Return ONLY valid "
                "JSON, no markdown formatting."
            ),
        )

        # Parse LLM response with ADR-029 sanitization
        # ✅ Fix Bug #24: multi_model_service returns "response" not "content"
        # The service's _execute_openai_call returns {"response": content, ...}
        # not {"content": content, ...} as originally assumed
        llm_content = response_data.get("response") or response_data.get(
            "content", "{}"
        )
        questions = self._parse_llm_response(llm_content, section_name, asset_name)

        # CRITICAL FIX: Inject asset_id and asset_name into each question's metadata
        # This allows frontend to properly group questions by asset (Issue #1200)
        for question in questions:
            if "metadata" not in question:
                question["metadata"] = {}
            question["metadata"]["asset_id"] = asset_id
            question["metadata"]["asset_name"] = asset_name

        logger.info(
            f"Generated {len(questions)} questions for {asset_name} in {section_name}"
        )

        return questions

    def _sanitize_escape_sequences(self, text: str) -> str:
        """
        Sanitize invalid escape sequences in LLM JSON responses.

        Bug #26: LLMs sometimes return invalid escape sequences like \\X, \\x (lowercase
        hex without valid hex digits), or other non-standard escapes that break JSON parsing.

        Valid JSON escape sequences: \\", \\\\, \\/, \\b, \\f, \\n, \\r, \\t, \\uXXXX

        Args:
            text: Raw text that may contain invalid escape sequences

        Returns:
            Text with invalid escape sequences fixed
        """
        import re

        # Use negative lookahead to find backslashes NOT followed by valid escape sequences.
        # Valid sequences: " \ / b f n r t or u followed by 4 hex digits (unicode).
        # Any other backslash-character pair gets the backslash escaped.
        def fix_invalid_escape(match: re.Match) -> str:
            # The matched group is the character immediately following the backslash
            return r"\\" + match.group(1)

        # Pattern: backslash NOT followed by valid escape chars or unicode sequence
        result = re.sub(
            r'\\(?![\\"/bfnrt]|u[0-9a-fA-F]{4})(.)', fix_invalid_escape, text
        )

        return result

    def _repair_truncated_json(self, text: str) -> str:
        """
        Attempt to repair truncated JSON by closing open brackets and braces.

        Bug #29: LLM responses sometimes get truncated mid-JSON, causing parse failures.
        This function tries to close any unclosed structures to allow partial parsing.

        Args:
            text: Potentially truncated JSON string

        Returns:
            Repaired JSON string (may still be invalid, but worth trying)
        """
        # Count open vs closed brackets and braces
        open_braces = text.count("{") - text.count("}")
        open_brackets = text.count("[") - text.count("]")

        # If we have unclosed structures, the JSON is likely truncated
        if open_braces > 0 or open_brackets > 0:
            logger.warning(
                f"Detected truncated JSON: {open_braces} unclosed braces, "
                f"{open_brackets} unclosed brackets. Attempting repair..."
            )

            # Try to find a good cut-off point (last complete object in array)
            # Look for the last complete object ending with "}"

            # Find the last complete question object (ends with })
            # Pattern: look for "},\n" or "}\n" or just "}" followed by incomplete data
            last_complete = text.rfind("},")
            if last_complete > 0:
                # Cut at the last complete object and close the array/object
                text = text[: last_complete + 1]
                text = text.rstrip(",")  # Remove trailing comma

            # Close any open brackets/braces
            text += "]" * open_brackets
            text += "}" * open_braces

        return text

    def _parse_llm_response(
        self, response: str, section_name: str, asset_name: str
    ) -> List[Dict[str, Any]]:
        """
        Parse LLM response with robust error handling (ADR-029).

        Handles:
        - Markdown code blocks (```json)
        - Malformed JSON (trailing commas, single quotes)
        - NaN/Infinity values from confidence scores
        - Invalid escape sequences (Bug #26: \\X, \\x, etc.)
        - Truncated JSON (Bug #29: closing unclosed brackets/braces)
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

        # Bug #26: Sanitize invalid escape sequences before parsing
        # LLMs sometimes return \X, \x, \. etc. which are not valid JSON escapes
        cleaned = self._sanitize_escape_sequences(cleaned)

        try:
            # Try standard JSON first
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback to dirtyjson for malformed JSON
            try:
                parsed = dirtyjson.loads(cleaned)
            except Exception:
                # Bug #29: Try repairing truncated JSON
                try:
                    repaired = self._repair_truncated_json(cleaned)
                    parsed = dirtyjson.loads(repaired)
                    logger.info(
                        f"Successfully parsed repaired JSON for {asset_name} in {section_name}"
                    )
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
        Validate question has required fields and enforces MCQ format.

        CRITICAL: All questions MUST be MCQ format (select/radio) with options.
        Free-text inputs produce noisy data that's hard to validate and use
        in assessment gap analysis.

        Args:
            question: Question dict from LLM

        Returns:
            True if valid MCQ question, False otherwise
        """
        required_fields = ["field_id", "question_text", "input_type"]
        if not all(field in question for field in required_fields):
            return False

        # ENFORCE MCQ FORMAT: Reject free-text input types
        input_type = question.get("input_type", "").lower()
        allowed_types = ["select", "radio", "multiselect", "multi_select"]

        if input_type not in allowed_types:
            logger.warning(
                f"Rejecting non-MCQ question '{question.get('field_id')}' "
                f"with input_type '{input_type}' - only select/radio allowed"
            )
            return False

        # ENFORCE OPTIONS: MCQ questions must have predefined options
        options = question.get("options")
        if not options or not isinstance(options, list) or len(options) < 2:
            logger.warning(
                f"Rejecting question '{question.get('field_id')}' "
                f"without valid options array (MCQ requires 2+ options)"
            )
            return False

        return True
