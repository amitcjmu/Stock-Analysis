"""
Question Generator Handler
Generates intelligent clarification questions from data analysis.
"""

import logging
from typing import Dict, List, Any

from app.services.models.agent_communication import QuestionType, ConfidenceLevel

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """Generates intelligent clarification questions based on data analysis."""
    
    def __init__(self):
        self.generator_id = "question_generator"
    
    async def generate_clarification_questions(self, data: List[Dict[str, Any]], 
                                             metadata: Dict[str, Any], 
                                             page_context: str) -> List[Dict[str, Any]]:
        """Generate clarification questions based on data analysis."""
        
        questions = []
        
        if not data:
            return [{
                "id": "no_data_question",
                "type": QuestionType.DATA_CLASSIFICATION.value,
                "title": "No Data Provided",
                "question": "No data was uploaded for analysis. Would you like to upload a different file?",
                "context": {"issue": "no_data"},
                "confidence": ConfidenceLevel.HIGH.value,
                "priority": "high"
            }]
        
        # Generate different types of questions
        questions.extend(await self._generate_field_mapping_questions(data, metadata))
        questions.extend(await self._generate_data_classification_questions(data))
        questions.extend(await self._generate_business_context_questions(data))
        questions.extend(await self._generate_quality_validation_questions(data))
        
        # Limit to most important questions
        prioritized_questions = self._prioritize_questions(questions)
        return prioritized_questions[:5]  # Return top 5 questions
    
    async def _generate_field_mapping_questions(self, data: List[Dict[str, Any]], 
                                               metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate questions about field mapping and interpretation."""
        
        questions = []
        
        # Sample data for analysis
        sample_data = data[:5]
        all_columns = set()
        for row in sample_data:
            all_columns.update(row.keys())
        
        # Check for unclear column names
        unclear_columns = []
        for column in all_columns:
            if self._is_column_name_unclear(column):
                unclear_columns.append(column)
        
        if unclear_columns:
            questions.append({
                "id": f"field_mapping_{hash('_'.join(unclear_columns))}",
                "type": QuestionType.FIELD_MAPPING.value,
                "title": "Field Mapping Clarification",
                "question": f"Could you clarify what these columns represent: {', '.join(unclear_columns[:3])}?",
                "context": {
                    "unclear_columns": unclear_columns,
                    "sample_data": sample_data[0] if sample_data else {},
                    "total_unclear": len(unclear_columns)
                },
                "options": ["Asset identifier", "Environment info", "Technical spec", "Business info", "Other"],
                "confidence": ConfidenceLevel.MEDIUM.value,
                "priority": "high" if len(unclear_columns) > 3 else "medium"
            })
        
        # Check for missing critical fields
        critical_fields = ["hostname", "asset_name", "server_name", "ip_address"]
        missing_critical = []
        
        for critical_field in critical_fields:
            if not any(critical_field.lower() in col.lower() for col in all_columns):
                missing_critical.append(critical_field)
        
        if missing_critical and len(missing_critical) < 4:  # If some are missing but not all
            questions.append({
                "id": f"missing_fields_{hash('_'.join(missing_critical))}",
                "type": QuestionType.FIELD_MAPPING.value,
                "title": "Missing Critical Fields",
                "question": f"This data appears to be missing {', '.join(missing_critical)}. Are these available in other columns?",
                "context": {
                    "missing_fields": missing_critical,
                    "available_columns": list(all_columns)[:10],
                    "suggestion": "field_mapping_needed"
                },
                "confidence": ConfidenceLevel.HIGH.value,
                "priority": "high"
            })
        
        return questions
    
    async def _generate_data_classification_questions(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate questions about data classification and quality."""
        
        questions = []
        
        # Check for data completeness issues
        empty_columns = []
        sample_size = min(10, len(data))
        sample_data = data[:sample_size]
        
        all_columns = set()
        for row in sample_data:
            all_columns.update(row.keys())
        
        for column in all_columns:
            empty_count = 0
            for row in sample_data:
                if not row.get(column) or str(row.get(column, "")).strip() == "":
                    empty_count += 1
            
            if empty_count > sample_size * 0.7:  # More than 70% empty
                empty_columns.append(column)
        
        if empty_columns:
            questions.append({
                "id": f"data_quality_{hash('_'.join(empty_columns))}",
                "type": QuestionType.DATA_CLASSIFICATION.value,
                "title": "Data Completeness Issue",
                "question": f"Columns {', '.join(empty_columns[:3])} appear to be mostly empty. Should these be excluded from analysis?",
                "context": {
                    "empty_columns": empty_columns,
                    "sample_size": sample_size,
                    "analysis_suggestion": "exclude_or_clarify"
                },
                "options": ["Exclude from analysis", "Include (data may be elsewhere)", "Request additional data"],
                "confidence": ConfidenceLevel.HIGH.value,
                "priority": "medium"
            })
        
        # Check for inconsistent data formats
        format_issues = await self._identify_format_inconsistencies(sample_data)
        if format_issues:
            questions.append({
                "id": f"format_consistency_{hash(str(format_issues))}",
                "type": QuestionType.QUALITY_VALIDATION.value,
                "title": "Data Format Inconsistencies",
                "question": f"Found format inconsistencies in: {', '.join(format_issues.keys())}. Should we standardize these?",
                "context": {
                    "format_issues": format_issues,
                    "standardization_needed": True
                },
                "options": ["Yes, standardize automatically", "No, keep as-is", "Manual review needed"],
                "confidence": ConfidenceLevel.MEDIUM.value,
                "priority": "medium"
            })
        
        return questions
    
    async def _generate_business_context_questions(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate questions about business context and ownership."""
        
        questions = []
        
        # Check for department/ownership information
        sample_data = data[:10]
        has_owner_info = False
        has_dept_info = False
        
        for row in sample_data:
            for column in row.keys():
                if any(keyword in column.lower() for keyword in ['owner', 'contact', 'responsible']):
                    has_owner_info = True
                if any(keyword in column.lower() for keyword in ['department', 'dept', 'organization', 'org']):
                    has_dept_info = True
        
        if not has_owner_info:
            questions.append({
                "id": "business_owner_info",
                "type": QuestionType.BUSINESS_CONTEXT.value,
                "title": "Asset Ownership Information",
                "question": "No asset ownership information found. Is this available elsewhere or should migration proceed without owner details?",
                "context": {
                    "missing_info": "ownership",
                    "migration_impact": "medium",
                    "suggestion": "may_need_additional_data"
                },
                "options": ["Available in separate file", "Not available", "Will provide later"],
                "confidence": ConfidenceLevel.MEDIUM.value,
                "priority": "low"
            })
        
        if not has_dept_info:
            questions.append({
                "id": "department_info",
                "type": QuestionType.BUSINESS_CONTEXT.value,
                "title": "Department/Organization Information",
                "question": "No department information found. Is organizational structure important for migration planning?",
                "context": {
                    "missing_info": "department",
                    "planning_impact": "organizational_structure",
                    "suggestion": "helpful_but_not_critical"
                },
                "options": ["Yes, very important", "Somewhat important", "Not needed"],
                "confidence": ConfidenceLevel.LOW.value,
                "priority": "low"
            })
        
        return questions
    
    async def _generate_quality_validation_questions(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate questions about data quality validation."""
        
        questions = []
        
        # Check for duplicate detection
        sample_data = data[:20]
        potential_duplicates = await self._detect_potential_duplicates(sample_data)
        
        if potential_duplicates > 0:
            questions.append({
                "id": "duplicate_validation",
                "type": QuestionType.QUALITY_VALIDATION.value,
                "title": "Potential Duplicate Records",
                "question": f"Found {potential_duplicates} potential duplicate records. How should these be handled?",
                "context": {
                    "duplicate_count": potential_duplicates,
                    "total_sample": len(sample_data),
                    "deduplication_needed": True
                },
                "options": ["Remove duplicates automatically", "Keep all records", "Manual review required"],
                "confidence": ConfidenceLevel.MEDIUM.value,
                "priority": "medium"
            })
        
        # Check for data validation requirements
        has_ip_addresses = False
        has_hostnames = False
        
        for row in sample_data:
            for column, value in row.items():
                if "ip" in column.lower() and value:
                    has_ip_addresses = True
                if "hostname" in column.lower() and value:
                    has_hostnames = True
        
        if has_ip_addresses or has_hostnames:
            questions.append({
                "id": "network_validation",
                "type": QuestionType.QUALITY_VALIDATION.value,
                "title": "Network Information Validation",
                "question": "Network information (IPs/hostnames) detected. Should we validate these are current and accessible?",
                "context": {
                    "has_ip_addresses": has_ip_addresses,
                    "has_hostnames": has_hostnames,
                    "validation_type": "network_connectivity"
                },
                "options": ["Yes, validate network info", "Skip validation", "Validate critical assets only"],
                "confidence": ConfidenceLevel.MEDIUM.value,
                "priority": "low"
            })
        
        return questions
    
    def _is_column_name_unclear(self, column_name: str) -> bool:
        """Check if a column name is unclear or needs clarification."""
        
        # Very generic names that need clarification
        generic_patterns = [
            'col', 'column', 'field', 'data', 'value', 'item', 'record',
            'attribute', 'property', 'info', 'details'
        ]
        
        # Single letter or very short names
        if len(column_name) <= 2:
            return True
        
        # Check for generic patterns
        column_lower = column_name.lower()
        for pattern in generic_patterns:
            if pattern in column_lower and len(column_lower) <= len(pattern) + 2:
                return True
        
        # Cryptic abbreviations (all uppercase, no vowels, >3 chars)
        if (column_name.isupper() and 
            len(column_name) > 3 and 
            not any(vowel in column_name.lower() for vowel in 'aeiou')):
            return True
        
        return False
    
    async def _identify_format_inconsistencies(self, data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify format inconsistencies in the data."""
        
        format_issues = {}
        
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        for column in all_columns:
            values = [str(row.get(column, "")) for row in data if row.get(column)]
            
            if len(values) < 2:
                continue
            
            # Check for mixed formats in the same column
            formats = set()
            for value in values[:10]:  # Check first 10 values
                if value.strip():
                    if any(char.isdigit() for char in value):
                        if '.' in value and all(part.isdigit() for part in value.split('.') if part):
                            formats.add("ip_address")
                        elif value.isdigit():
                            formats.add("numeric")
                        else:
                            formats.add("mixed_alphanumeric")
                    else:
                        formats.add("text")
            
            if len(formats) > 1:
                format_issues[column] = list(formats)
        
        return format_issues
    
    async def _detect_potential_duplicates(self, data: List[Dict[str, Any]]) -> int:
        """Detect potential duplicate records."""
        
        if len(data) < 2:
            return 0
        
        # Create simple signatures for duplicate detection
        signatures = []
        for row in data:
            # Use first 3 non-empty values as signature
            values = [str(v) for v in row.values() if v and str(v).strip()][:3]
            if len(values) >= 2:
                signatures.append("|".join(values))
        
        unique_signatures = set(signatures)
        return len(signatures) - len(unique_signatures)
    
    def _prioritize_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize questions by importance and relevance."""
        
        priority_scores = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        confidence_scores = {
            ConfidenceLevel.HIGH.value: 3,
            ConfidenceLevel.MEDIUM.value: 2,
            ConfidenceLevel.LOW.value: 1,
            ConfidenceLevel.UNCERTAIN.value: 0
        }
        
        # Calculate combined score for each question
        for question in questions:
            priority_score = priority_scores.get(question.get("priority", "medium"), 2)
            confidence_score = confidence_scores.get(question.get("confidence", ConfidenceLevel.MEDIUM.value), 2)
            question["_score"] = priority_score + confidence_score
        
        # Sort by score (highest first)
        return sorted(questions, key=lambda q: q.get("_score", 0), reverse=True) 