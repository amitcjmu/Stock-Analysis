"""
Questionnaire Generator Enums
"""

from enum import Enum


class QuestionType(str, Enum):
    """Question types supported by the adaptive questionnaire system"""

    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    TEXT_INPUT = "text_input"
    NUMERIC_INPUT = "numeric_input"
    BOOLEAN = "boolean"
    DATE_INPUT = "date_input"
    FILE_UPLOAD = "file_upload"
    RATING_SCALE = "rating_scale"
    DEPENDENCY_MAPPING = "dependency_mapping"
    TECHNOLOGY_SELECTION = "technology_selection"


class QuestionPriority(str, Enum):
    """Question priority levels for questionnaire sequencing"""

    CRITICAL = "critical"  # Must be answered to proceed
    HIGH = "high"  # Important for strategy confidence
    MEDIUM = "medium"  # Helpful for planning
    LOW = "low"  # Nice to have
