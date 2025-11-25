"""
Prompt Builder for SectionQuestionGenerator - Builds clear, unambiguous LLM prompts.

Extracted from main generator to keep files under 400 lines.

CC Generated for Issue #1113 - SectionQuestionGenerator Modularization
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.collection.gap_analysis.models import IntelligentGap

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds clear, unambiguous prompts for question generation."""

    def build_prompt(
        self,
        asset_name: str,
        section_name: str,
        gaps: List[IntelligentGap],
        asset_data: Optional[Dict[str, Any]],
        previous_questions: List[str],
    ) -> str:
        """
        Build prompt for LLM question generation.

        Args:
            asset_name: Name of asset being questioned
            section_name: Section name (e.g., "infrastructure", "resilience")
            gaps: List of TRUE gaps for this section
            asset_data: Data map from DataAwarenessAgent (for context)
            previous_questions: Questions already asked in other sections

        Returns:
            Prompt string with clear instructions
        """
        prompt = f"""You are generating questionnaire questions for asset "{asset_name}" in section "{section_name}".

**CRITICAL INSTRUCTIONS**:
1. Generate questions ONLY for the TRUE gaps listed below
2. Each gap has been verified as missing across ALL 6 data sources
3. Questions must be clear, specific, and actionable
4. NO DUPLICATE QUESTIONS: Check previous questions list before generating
5. Prioritize HIGH/CRITICAL gaps first
6. Target 5-8 questions (do NOT generate for ALL gaps if >8)

**TRUE Gaps for {section_name}** (Data NOT found in ANY source):
{self._format_section_gaps(gaps)}

**Data Awareness Context** (data that EXISTS - for intelligent options):
{self._format_data_coverage(asset_data)}

**Previous Questions** (DO NOT DUPLICATE):
{self._format_previous_questions(previous_questions)}

**Question Format Requirements**:
1. question_text: Clear, specific question (What is the...?)
2. input_type: "text", "select", "number", "boolean"
3. options: Array of intelligent options (use data context)
4. validation: Optional validation rules
5. help_text: Why this data is needed

**Output Format** (JSON only, no markdown):
{{
    "section": "{section_name}",
    "questions": [
        {{
            "field_id": "cpu_count",
            "question_text": "How many CPU cores does {asset_name} have?",
            "input_type": "number",
            "options": null,
            "validation": {{"min": 1, "max": 128}},
            "help_text": "Required for capacity planning and cost optimization",
            "priority": "critical"
        }},
        {{
            "field_id": "database_type",
            "question_text": "What database technology does {asset_name} use?",
            "input_type": "select",
            "options": ["PostgreSQL", "MySQL", "MongoDB", "Oracle", "SQL Server", "Other"],
            "validation": null,
            "help_text": "Used for migration strategy and compatibility analysis",
            "priority": "high"
        }}
    ]
}}

**IMPORTANT**: Return ONLY valid JSON, no markdown formatting, no code blocks.
"""
        return prompt

    def _format_data_coverage(self, asset_data: Optional[Dict[str, Any]]) -> str:
        """
        Format data coverage from DataAwarenessAgent into readable context.

        Args:
            asset_data: Data map entry for this asset

        Returns:
            Formatted string showing what data exists
        """
        if not asset_data:
            return "No existing data context available"

        lines = []

        # Show data coverage percentages
        if "data_coverage" in asset_data:
            coverage = asset_data["data_coverage"]
            lines.append("Data Coverage by Source:")
            for source, percent in coverage.items():
                if percent > 0:
                    lines.append(f"  - {source}: {percent}%")

        # Show data_exists_elsewhere samples
        if "data_exists_elsewhere" in asset_data:
            exists = asset_data["data_exists_elsewhere"]
            if exists:
                lines.append("\nData Found in Alternative Sources (use for options):")
                for item in exists[:5]:  # Limit to 5 examples
                    field = item.get("field", "unknown")
                    found_in = item.get("found_in", "unknown")
                    value = item.get("value", "unknown")
                    lines.append(f"  - {field}: {value} (from {found_in})")

        return "\n".join(lines) if lines else "No data coverage information available"

    def _format_section_gaps(self, gaps: List[IntelligentGap]) -> str:
        """
        Format gaps into readable list with priority.

        Args:
            gaps: List of IntelligentGap objects

        Returns:
            Formatted string with gap details
        """
        if not gaps:
            return "No TRUE gaps found for this section"

        lines = []
        # Sort by priority (critical > high > medium > low)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_gaps = sorted(gaps, key=lambda g: priority_order.get(g.priority, 4))

        for gap in sorted_gaps:
            lines.append(
                f"  - {gap.field_display_name} ({gap.field_id}) - "
                f"Priority: {gap.priority.upper()}, "
                f"Confidence: {gap.confidence:.2f}"
            )

        return "\n".join(lines)

    def _format_previous_questions(self, questions: List[str]) -> str:
        """
        Format previous questions to prevent duplicates.

        Args:
            questions: List of question texts from other sections

        Returns:
            Formatted string with previous questions
        """
        if not questions:
            return "No previous questions (this is the first section)"

        lines = ["Questions already asked in other sections:"]
        for i, question in enumerate(questions, 1):
            lines.append(f"  {i}. {question}")

        return "\n".join(lines)
