"""
Response Handler
Handles result parsing, question processing, and parameter updates.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseHandlerHandler:
    """Handles response processing and result parsing with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = True
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.schemas.sixr_analysis import QualifyingQuestion, QuestionType, QuestionOption
            self.QualifyingQuestion = QualifyingQuestion
            self.QuestionType = QuestionType
            self.QuestionOption = QuestionOption
            logger.info("Response handler initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Schema imports not available: {e}")
            self._initialize_fallback_schemas()
            self.service_available = False
    
    def _initialize_fallback_schemas(self):
        """Initialize fallback schema classes."""
        class FallbackQualifyingQuestion:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        class FallbackQuestionType:
            TEXT = "text"
            SELECT = "select"
            MULTISELECT = "multiselect"
            BOOLEAN = "boolean"
            SCALE = "scale"
        
        class FallbackQuestionOption:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        self.QualifyingQuestion = FallbackQualifyingQuestion
        self.QuestionType = FallbackQuestionType
        self.QuestionOption = FallbackQuestionOption
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    def parse_generated_questions(self, raw_result: str) -> List[Dict[str, Any]]:
        """Parse and structure questions from agent output."""
        try:
            # Try to parse JSON if possible
            if isinstance(raw_result, str):
                # Look for JSON-like content
                json_pattern = r'\{.*\}'
                json_matches = re.findall(json_pattern, raw_result, re.DOTALL)
                
                if json_matches:
                    try:
                        parsed_json = json.loads(json_matches[0])
                        if isinstance(parsed_json, list):
                            return self._structure_questions(parsed_json)
                        elif isinstance(parsed_json, dict) and 'questions' in parsed_json:
                            return self._structure_questions(parsed_json['questions'])
                    except json.JSONDecodeError:
                        pass
            
            # Fallback to text parsing
            return self._parse_questions_from_text(raw_result)
            
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            return self._generate_default_questions()
    
    def _structure_questions(self, questions_data: List[Any]) -> List[Dict[str, Any]]:
        """Structure questions into proper format."""
        structured_questions = []
        
        for i, question_data in enumerate(questions_data):
            if isinstance(question_data, dict):
                structured_question = {
                    "id": question_data.get("id", f"question_{i+1}"),
                    "question": question_data.get("question", "Unknown question"),
                    "question_type": question_data.get("type", self.QuestionType.TEXT),
                    "category": question_data.get("category", "General"),
                    "priority": question_data.get("priority", 2),
                    "required": question_data.get("required", False),
                    "help_text": question_data.get("help_text", "")
                }
                
                # Add options if present
                if "options" in question_data:
                    structured_question["options"] = [
                        self.QuestionOption(
                            value=opt.get("value", ""),
                            label=opt.get("label", "")
                        ) if isinstance(opt, dict) else self.QuestionOption(value=str(opt), label=str(opt))
                        for opt in question_data["options"]
                    ]
                
                structured_questions.append(structured_question)
        
        return structured_questions
    
    def _parse_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse questions from unstructured text."""
        questions = []
        
        # Look for question patterns
        question_patterns = [
            r'\d+\.\s*(.*\?)',  # "1. What is...?"
            r'Question:\s*(.*\?)',  # "Question: What is...?"
            r'Q\d*:\s*(.*\?)',  # "Q1: What is...?"
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for i, match in enumerate(matches):
                questions.append({
                    "id": f"parsed_question_{len(questions)+1}",
                    "question": match.strip(),
                    "question_type": self.QuestionType.TEXT,
                    "category": "General",
                    "priority": 2,
                    "required": False,
                    "help_text": "Generated from agent analysis"
                })
        
        return questions if questions else self._generate_default_questions()
    
    def _generate_default_questions(self) -> List[Dict[str, Any]]:
        """Generate default questions when parsing fails."""
        return [
            {
                "id": "technical_complexity",
                "question": "How would you rate the technical complexity of this application?",
                "question_type": self.QuestionType.SCALE,
                "category": "Technical",
                "priority": 1,
                "required": True,
                "scale": {"min": 1, "max": 5, "labels": {"1": "Very Simple", "5": "Very Complex"}},
                "help_text": "Consider architecture, dependencies, and technology stack"
            },
            {
                "id": "business_criticality",
                "question": "What is the business criticality of this application?",
                "question_type": self.QuestionType.SELECT,
                "category": "Business",
                "priority": 1,
                "required": True,
                "options": [
                    self.QuestionOption(value="low", label="Low - Can be offline for days"),
                    self.QuestionOption(value="medium", label="Medium - Can be offline for hours"),
                    self.QuestionOption(value="high", label="High - Can be offline for minutes"),
                    self.QuestionOption(value="critical", label="Critical - Must be always available")
                ],
                "help_text": "Consider impact on business operations and revenue"
            },
            {
                "id": "dependencies",
                "question": "How many external dependencies does this application have?",
                "question_type": self.QuestionType.SELECT,
                "category": "Technical",
                "priority": 2,
                "required": False,
                "options": [
                    self.QuestionOption(value="none", label="No dependencies"),
                    self.QuestionOption(value="few", label="1-3 dependencies"),
                    self.QuestionOption(value="moderate", label="4-10 dependencies"),
                    self.QuestionOption(value="many", label="More than 10 dependencies")
                ],
                "help_text": "Consider databases, external APIs, shared services, and other applications"
            }
        ]
    
    def parse_parameter_updates(self, raw_result: str) -> Dict[str, Any]:
        """Parse parameter updates from agent output."""
        try:
            # Try to parse structured output
            if isinstance(raw_result, str):
                # Look for parameter updates in the text
                parameter_patterns = {
                    'business_value': r'business[_\s]*value[:\s]*(\d+(?:\.\d+)?)',
                    'technical_complexity': r'technical[_\s]*complexity[:\s]*(\d+(?:\.\d+)?)',
                    'migration_urgency': r'migration[_\s]*urgency[:\s]*(\d+(?:\.\d+)?)',
                    'compliance_requirements': r'compliance[_\s]*requirements?[:\s]*(\d+(?:\.\d+)?)',
                    'cost_sensitivity': r'cost[_\s]*sensitivity[:\s]*(\d+(?:\.\d+)?)',
                    'risk_tolerance': r'risk[_\s]*tolerance[:\s]*(\d+(?:\.\d+)?)',
                    'innovation_priority': r'innovation[_\s]*priority[:\s]*(\d+(?:\.\d+)?)'
                }
                
                updates = {}
                for param, pattern in parameter_patterns.items():
                    matches = re.findall(pattern, raw_result, re.IGNORECASE)
                    if matches:
                        try:
                            value = float(matches[0])
                            if 1 <= value <= 5:  # Validate range
                                updates[param] = value
                        except ValueError:
                            continue
                
                # Extract confidence and reasoning
                confidence_match = re.search(r'confidence[:\s]*(\d+(?:\.\d+)?)', raw_result, re.IGNORECASE)
                confidence = float(confidence_match.group(1)) if confidence_match else 0.8
                
                return {
                    "updates": updates,
                    "confidence": min(confidence, 1.0),
                    "reasoning": self._extract_reasoning(raw_result),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error parsing parameter updates: {e}")
        
        # Fallback response
        return {
            "updates": {},
            "confidence": 0.6,
            "reasoning": "Unable to parse parameter updates - using fallback",
            "timestamp": datetime.utcnow().isoformat(),
            "fallback_mode": True
        }
    
    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning from agent output."""
        # Look for reasoning patterns
        reasoning_patterns = [
            r'reasoning[:\s]*(.*?)(?:\n\n|\.|$)',
            r'because[:\s]*(.*?)(?:\n\n|\.|$)',
            r'rationale[:\s]*(.*?)(?:\n\n|\.|$)',
            r'justification[:\s]*(.*?)(?:\n\n|\.|$)'
        ]
        
        for pattern in reasoning_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                return matches[0].strip()
        
        return "Parameter updates based on agent analysis"
    
    def process_stakeholder_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process stakeholder responses into parameter updates."""
        try:
            parameter_mapping = {
                'technical_complexity': 'technical_complexity',
                'business_criticality': 'business_value',
                'migration_timeline': 'migration_urgency',
                'compliance_requirements': 'compliance_requirements',
                'cost_constraints': 'cost_sensitivity',
                'risk_appetite': 'risk_tolerance',
                'innovation_goals': 'innovation_priority'
            }
            
            updates = {}
            confidence_scores = []
            
            for response in responses:
                question_id = response.get('question_id', '')
                answer = response.get('answer', '')
                
                # Map question responses to parameters
                if question_id in parameter_mapping:
                    param_name = parameter_mapping[question_id]
                    param_value = self._convert_answer_to_value(answer, question_id)
                    
                    if param_value is not None:
                        updates[param_name] = param_value
                        confidence_scores.append(0.9)  # High confidence for direct mappings
                
                # Handle scale responses
                elif 'complexity' in question_id.lower():
                    if isinstance(answer, (int, float)) and 1 <= answer <= 5:
                        updates['technical_complexity'] = float(answer)
                        confidence_scores.append(0.95)
                
                elif 'criticality' in question_id.lower() or 'business' in question_id.lower():
                    if isinstance(answer, (int, float)) and 1 <= answer <= 5:
                        updates['business_value'] = float(answer)
                        confidence_scores.append(0.95)
            
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7
            
            return {
                "updates": updates,
                "confidence": overall_confidence,
                "reasoning": f"Processed {len(responses)} stakeholder responses",
                "responses_processed": len(responses),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing stakeholder responses: {e}")
            return {
                "updates": {},
                "confidence": 0.5,
                "reasoning": f"Error processing responses: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "fallback_mode": True
            }
    
    def _convert_answer_to_value(self, answer: Any, question_id: str) -> Optional[float]:
        """Convert answer to parameter value (1-5 scale)."""
        try:
            # Handle numeric answers
            if isinstance(answer, (int, float)):
                return max(1, min(5, float(answer)))
            
            # Handle string answers
            if isinstance(answer, str):
                answer_lower = answer.lower()
                
                # Handle scale responses
                if 'very low' in answer_lower or 'minimal' in answer_lower:
                    return 1.0
                elif 'low' in answer_lower:
                    return 2.0
                elif 'medium' in answer_lower or 'moderate' in answer_lower:
                    return 3.0
                elif 'high' in answer_lower:
                    return 4.0
                elif 'very high' in answer_lower or 'critical' in answer_lower:
                    return 5.0
                
                # Handle yes/no responses
                elif 'yes' in answer_lower or 'true' in answer_lower:
                    return 4.0
                elif 'no' in answer_lower or 'false' in answer_lower:
                    return 2.0
                
                # Try to extract number from string
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    return max(1, min(5, float(numbers[0])))
            
            return None
            
        except Exception as e:
            logger.error(f"Error converting answer to value: {e}")
            return None
    
    def validate_response_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize response format."""
        try:
            validated = {
                "question_id": response.get("question_id", "unknown"),
                "answer": response.get("answer", ""),
                "confidence": response.get("confidence", 0.8),
                "timestamp": response.get("timestamp", datetime.utcnow().isoformat())
            }
            
            # Validate answer based on question type
            question_type = response.get("question_type", "text")
            if question_type == "scale":
                answer = validated["answer"]
                if isinstance(answer, (int, float)) and 1 <= answer <= 5:
                    validated["answer"] = float(answer)
                else:
                    validated["answer"] = 3.0  # Default to middle value
                    validated["confidence"] = 0.5
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return {
                "question_id": "error",
                "answer": "",
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def generate_response_summary(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of processed responses."""
        try:
            total_responses = len(responses)
            valid_responses = sum(1 for r in responses if r.get("answer"))
            
            categories = {}
            for response in responses:
                category = response.get("category", "Unknown")
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            return {
                "total_responses": total_responses,
                "valid_responses": valid_responses,
                "completion_rate": valid_responses / total_responses if total_responses > 0 else 0,
                "categories": categories,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating response summary: {e}")
            return {
                "total_responses": 0,
                "valid_responses": 0,
                "completion_rate": 0,
                "categories": {},
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            } 