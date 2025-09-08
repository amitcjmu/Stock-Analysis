"""
Adaptive Form Creation Module

Handles creation of adaptive forms from questionnaire data and gap context.
This module is separated from the main service to maintain file size limits.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class FormCreationMixin:
    """
    Mixin class for adaptive form creation from questionnaire data.

    This class provides methods to create form configurations from AI-generated
    questionnaire data while preserving gap field names for proper resolution.
    """

    async def create_adaptive_form(
        self,
        questionnaire_data: Dict[str, Any],
        gap_context: List[Dict[str, Any]],
        template_preferences: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create adaptive form configuration from questionnaire data and gap context.

        This method converts AI-generated questionnaire data into form configuration
        that preserves the exact gap field names for proper gap resolution.

        Args:
            questionnaire_data: Generated questionnaire from AI agents
            gap_context: List of gaps that need to be resolved
            template_preferences: Optional form styling and behavior preferences

        Returns:
            Form configuration dict or None if creation fails
        """
        try:
            self.logger.info("Creating adaptive form from questionnaire data")

            # Build gap lookup by field_name for quick access
            gap_lookup = {
                gap.get("field_name"): gap
                for gap in gap_context
                if gap.get("field_name")
            }

            # Extract sections from questionnaire data
            sections = []
            if isinstance(questionnaire_data, dict):
                # Check for nested structure
                if "questionnaire" in questionnaire_data and isinstance(
                    questionnaire_data["questionnaire"], dict
                ):
                    sections = questionnaire_data["questionnaire"].get("sections", [])
                # Check for direct sections
                elif "sections" in questionnaire_data:
                    sections = questionnaire_data.get("sections", [])
                # Check for flat structure with questions
                elif "questions" in questionnaire_data:
                    sections = [
                        {
                            "section_id": "default",
                            "section_title": questionnaire_data.get(
                                "title", "Data Collection"
                            ),
                            "questions": questionnaire_data.get("questions", []),
                        }
                    ]

            if not sections:
                self.logger.warning("No sections found in questionnaire data")
                return None

            # Build form configuration
            form_config = {
                "form_id": questionnaire_data.get("id", f"form_{uuid.uuid4()}"),
                "title": questionnaire_data.get("title", "Data Collection Form"),
                "description": questionnaire_data.get(
                    "description", "Adaptive questionnaire for data collection"
                ),
                "sections": [],
                "field_mapping": {},  # Maps form field IDs to gap field_names
                "validation_rules": {},
                "conditional_logic": {},
            }

            # Process each section
            for section in sections:
                section_config = {
                    "section_id": section.get("section_id", "default"),
                    "title": section.get("section_title", "Questions"),
                    "description": section.get("section_description", ""),
                    "fields": [],
                }

                # Process questions in section
                questions = section.get("questions", [])
                for question in questions:
                    field_config = self._create_field_from_question(
                        question, gap_lookup
                    )
                    if field_config:
                        section_config["fields"].append(field_config)

                        # Map the field ID to gap field_name for resolution
                        field_id = field_config.get("id")
                        gap_field_name = field_config.get("gap_field_name")
                        if field_id and gap_field_name:
                            form_config["field_mapping"][field_id] = gap_field_name

                if section_config["fields"]:  # Only add sections with fields
                    form_config["sections"].append(section_config)

            self.logger.info(
                f"Created adaptive form with {len(form_config['sections'])} sections"
            )
            return form_config

        except Exception as e:
            self.logger.error(f"Failed to create adaptive form from questionnaire: {e}")
            return None

    def _create_field_from_question(
        self, question: Dict[str, Any], gap_lookup: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create form field configuration from questionnaire question.

        CRITICAL: This method ensures that the field ID matches the exact gap field_name
        to enable proper gap resolution when responses are submitted.
        """
        try:
            # Extract question ID - this should be the gap field_name
            question_id = question.get("question_id")
            if not question_id:
                self.logger.warning("Question missing question_id, skipping")
                return None

            # Look up the corresponding gap
            gap = gap_lookup.get(question_id)
            if not gap:
                self.logger.warning(f"No gap found for question_id: {question_id}")
                # Still create the field but note the issue

            # Map question types to form field types
            question_type = question.get("question_type", "text_input")
            field_type_mapping = {
                "single_select": "select",
                "multi_select": "multiselect",
                "text_input": "text",
                "textarea": "textarea",
                "numeric_input": "number",
                "boolean": "checkbox",
                "date_input": "date",
                "file_upload": "file",
                "rating_scale": "number",
                "radio": "radio",
            }

            field_type = field_type_mapping.get(question_type, "text")

            # Build field configuration preserving the exact question_id as field ID
            field_config = {
                "id": question_id,  # CRITICAL: Use exact question_id (which should be gap field_name)
                "name": question_id,  # Also set name for HTML form compatibility
                "label": question.get("question_text", ""),
                "type": field_type,
                "required": question.get("required", False),
                "help_text": question.get("help_text", ""),
                "gap_field_name": question_id,  # Explicitly track the gap field name
                "placeholder": "",
                "validation": {},
            }

            # Add options for select fields
            options = question.get("options", [])
            if options and field_type in ["select", "multiselect", "radio"]:
                field_config["options"] = [
                    {
                        "value": opt.get("value", ""),
                        "label": opt.get("label", opt.get("value", "")),
                    }
                    for opt in options
                ]

            # Add validation rules
            validation_rules = question.get("validation_rules", {})
            if validation_rules:
                field_config["validation"].update(validation_rules)

            # Add conditional logic if present
            conditional_logic = question.get("conditional_logic", {})
            if conditional_logic:
                field_config["conditional_logic"] = conditional_logic

            return field_config

        except Exception as e:
            self.logger.error(f"Failed to create field from question: {e}")
            return None
