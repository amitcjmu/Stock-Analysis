"""
Generation Tools Handler
Handles question generation and related tools.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class GenerationToolsHandler:
    """Handles generation tools with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = True
        logger.info("Generation tools handler initialized successfully")
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True
    
    def generate_qualifying_questions(self, information_gaps: List[str], 
                                    application_context: Dict[str, Any],
                                    current_parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate qualifying questions based on information gaps."""
        try:
            questions = []
            
            # Technical complexity questions
            if "technical_complexity" in information_gaps or not current_parameters.get("technical_complexity"):
                questions.extend(self._generate_technical_questions(application_context))
            
            # Business value questions
            if "business_value" in information_gaps or not current_parameters.get("business_value"):
                questions.extend(self._generate_business_questions(application_context))
            
            # Compliance questions
            if "compliance" in information_gaps or not current_parameters.get("compliance_requirements"):
                questions.extend(self._generate_compliance_questions(application_context))
            
            # General migration questions
            if len(questions) < 3:
                questions.extend(self._generate_general_questions(application_context))
            
            return questions[:10]  # Limit to 10 questions
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._fallback_generate_questions()
    
    def _generate_technical_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate technical complexity questions."""
        return [
            {
                "id": "tech_complexity_1",
                "question": "How would you rate the technical complexity of this application?",
                "type": "scale",
                "scale": {"min": 1, "max": 5, "labels": {"1": "Very Simple", "5": "Very Complex"}},
                "category": "technical"
            },
            {
                "id": "tech_stack_1", 
                "question": "Does this application use legacy technologies that are difficult to modernize?",
                "type": "boolean",
                "category": "technical"
            },
            {
                "id": "integrations_1",
                "question": "How many external systems does this application integrate with?",
                "type": "multiple_choice",
                "options": ["0-2", "3-5", "6-10", "10+"],
                "category": "technical"
            }
        ]
    
    def _generate_business_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate business value questions."""
        return [
            {
                "id": "business_value_1",
                "question": "How critical is this application to your business operations?",
                "type": "scale", 
                "scale": {"min": 1, "max": 5, "labels": {"1": "Not Critical", "5": "Mission Critical"}},
                "category": "business"
            },
            {
                "id": "user_impact_1",
                "question": "How many users would be affected if this application was unavailable?",
                "type": "multiple_choice",
                "options": ["< 10", "10-100", "100-1000", "1000+"],
                "category": "business"
            }
        ]
    
    def _generate_compliance_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate compliance questions."""
        return [
            {
                "id": "compliance_1",
                "question": "Does this application handle sensitive data (PII, financial, health)?",
                "type": "boolean",
                "category": "compliance"
            },
            {
                "id": "regulations_1", 
                "question": "Which regulatory frameworks apply to this application?",
                "type": "multiple_select",
                "options": ["GDPR", "HIPAA", "PCI-DSS", "SOX", "None"],
                "category": "compliance"
            }
        ]
    
    def _generate_general_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate general migration questions."""
        return [
            {
                "id": "timeline_1",
                "question": "What is your preferred timeline for migrating this application?",
                "type": "multiple_choice", 
                "options": ["< 3 months", "3-6 months", "6-12 months", "> 12 months"],
                "category": "general"
            },
            {
                "id": "budget_1",
                "question": "How sensitive is this migration to cost considerations?",
                "type": "scale",
                "scale": {"min": 1, "max": 5, "labels": {"1": "Cost No Object", "5": "Very Cost Sensitive"}},
                "category": "general"
            }
        ]
    
    def _fallback_generate_questions(self) -> List[Dict[str, Any]]:
        """Fallback question generation."""
        return [
            {
                "id": "fallback_1",
                "question": "How would you rate the overall complexity of this application?",
                "type": "scale",
                "scale": {"min": 1, "max": 5},
                "category": "general",
                "fallback_mode": True
            }
        ] 