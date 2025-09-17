"""
Question Generation Tool for 6R Migration Strategy Analysis.
Generates targeted qualifying questions to address information gaps.
"""

from typing import Any, Dict, List

from ..core.base import BaseTool, BaseModel, Field, logger, json


class QuestionGenerationInput(BaseModel):
    """Input schema for question generation tool."""

    information_gaps: List[str] = Field(
        ..., description="List of information gaps to address"
    )
    application_context: Dict[str, Any] = Field(..., description="Application context")
    priority_focus: str = Field(default="all", description="Priority focus area")


class QuestionGenerationTool(BaseTool):
    """Tool for generating qualifying questions based on information gaps."""

    name: str = "question_generation_tool"
    description: str = (
        "Generate targeted qualifying questions to address information gaps"
    )
    args_schema: type[BaseModel] = QuestionGenerationInput

    def _run(
        self,
        information_gaps: List[str],
        application_context: Dict[str, Any],
        priority_focus: str = "all",
    ) -> str:
        """Generate questions based on information gaps."""
        try:
            questions = []

            # Question templates based on common gaps
            question_templates = {
                "application_type": {
                    "question": "What type of application is this?",
                    "type": "select",
                    "options": [
                        {
                            "value": "custom",
                            "label": "Custom-built application (developed in-house)",
                        },
                        {
                            "value": "cots",
                            "label": "Commercial Off-The-Shelf (COTS) application",
                        },
                        {
                            "value": "hybrid",
                            "label": "Hybrid (mix of custom and COTS components)",
                        },
                    ],
                    "category": "Application Classification",
                    "priority": 1,
                    "help_text": "COTS applications cannot be rewritten, only replaced with alternatives",
                },
                "dependencies": {
                    "question": "How many external dependencies does this application have?",
                    "type": "select",
                    "options": [
                        {"value": "none", "label": "No external dependencies"},
                        {"value": "few", "label": "1-3 dependencies"},
                        {"value": "moderate", "label": "4-10 dependencies"},
                        {"value": "many", "label": "More than 10 dependencies"},
                    ],
                    "category": "Technical Architecture",
                    "priority": 1,
                },
                "compliance": {
                    "question": "What compliance frameworks apply to this application?",
                    "type": "multiselect",
                    "options": [
                        {"value": "sox", "label": "SOX (Sarbanes-Oxley)"},
                        {"value": "pci", "label": "PCI DSS"},
                        {"value": "hipaa", "label": "HIPAA"},
                        {"value": "gdpr", "label": "GDPR"},
                        {
                            "value": "none",
                            "label": "No specific compliance requirements",
                        },
                    ],
                    "category": "Compliance",
                    "priority": 2,
                },
                "business_impact": {
                    "question": "What is the business impact if this application is unavailable?",
                    "type": "select",
                    "options": [
                        {
                            "value": "low",
                            "label": "Minimal impact - can be down for days",
                        },
                        {
                            "value": "medium",
                            "label": "Moderate impact - can be down for hours",
                        },
                        {
                            "value": "high",
                            "label": "High impact - can be down for minutes",
                        },
                        {
                            "value": "critical",
                            "label": "Critical - must be always available",
                        },
                    ],
                    "category": "Business Impact",
                    "priority": 1,
                },
                "technical_debt": {
                    "question": "How would you rate the technical debt of this application?",
                    "type": "select",
                    "options": [
                        {"value": "low", "label": "Low - well maintained, modern code"},
                        {"value": "medium", "label": "Medium - some legacy components"},
                        {"value": "high", "label": "High - significant legacy code"},
                        {
                            "value": "very_high",
                            "label": "Very High - mostly legacy, hard to maintain",
                        },
                    ],
                    "category": "Technical Quality",
                    "priority": 2,
                },
                "data_volume": {
                    "question": "What is the approximate data volume for this application?",
                    "type": "select",
                    "options": [
                        {"value": "small", "label": "Small (< 1 GB)"},
                        {"value": "medium", "label": "Medium (1-100 GB)"},
                        {"value": "large", "label": "Large (100 GB - 1 TB)"},
                        {"value": "very_large", "label": "Very Large (> 1 TB)"},
                    ],
                    "category": "Data Management",
                    "priority": 3,
                },
            }

            # Generate questions based on gaps
            for gap in information_gaps:
                gap_lower = gap.lower()

                # Match gaps to question templates
                added_templates_for_gap = set()
                for template_key, template in question_templates.items():
                    if template_key not in added_templates_for_gap and (
                        template_key in gap_lower
                        or any(
                            keyword in gap_lower for keyword in template_key.split("_")
                        )
                    ):
                        question = {
                            "id": f"{template_key}_{len(questions)}",
                            "question": template["question"],
                            "question_type": template["type"],
                            "category": template["category"],
                            "priority": template["priority"],
                            "required": template["priority"] <= 2,
                            "options": template.get("options", []),
                            "help_text": f"This information helps address: {gap}",
                        }
                        questions.append(question)
                        added_templates_for_gap.add(template_key)

            # Add default questions if no specific gaps matched
            if not questions:
                for template_key, template in list(question_templates.items())[:3]:
                    question = {
                        "id": f"default_{template_key}",
                        "question": template["question"],
                        "question_type": template["type"],
                        "category": template["category"],
                        "priority": template["priority"],
                        "required": template["priority"] <= 2,
                        "options": template.get("options", []),
                        "help_text": "General information to improve analysis accuracy",
                    }
                    questions.append(question)

            # Sort by priority
            questions.sort(key=lambda x: x["priority"])

            return json.dumps(
                {"questions": questions, "total_count": len(questions)}, indent=2
            )

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})
