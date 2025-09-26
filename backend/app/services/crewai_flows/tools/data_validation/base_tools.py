"""
Base Tool Classes for Data Validation

CrewAI tool wrapper classes that provide the interface for persistent agents.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

from .implementations import (
    DataQualityImpl,
    DataStructureAnalyzerImpl,
    DataValidationToolImpl,
    FieldSuggestionImpl,
)

logger = logging.getLogger(__name__)

# Import CrewAI tools with fallback
try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


class BaseDataValidationTool(BaseTool):
    """Base tool for agents to validate imported data"""

    name: str = "data_validator"
    description: str = """
    Validate imported data for structure, completeness, and quality.
    Use this tool to check if imported data is ready for processing.

    Input: List of raw data records
    Output: Validation results with errors, warnings, and statistics
    """

    def __init__(self, context_info: Dict[str, Any]):
        super().__init__()
        self._context_info = context_info

    async def _arun(self, raw_data: List[Dict[str, Any]]) -> str:
        """Async implementation to validate data"""
        result = await DataValidationToolImpl.validate_data(
            raw_data, self._context_info
        )
        return json.dumps(result)

    def _run(self, raw_data: List[Dict[str, Any]]) -> str:
        """Sync wrapper for async implementation"""
        try:
            loop = asyncio.get_running_loop()
            # Already in an event loop, create task
            future = asyncio.ensure_future(self._arun(raw_data))
            # This will block but won't create a new loop
            return loop.run_until_complete(future)
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self._arun(raw_data))


class BaseDataStructureAnalyzerTool(BaseTool):
    """Base tool for analyzing data structure and patterns"""

    name: str = "data_structure_analyzer"
    description: str = """
    Analyze the structure and patterns in imported data.
    Use this to understand data types, detect asset types,
    and assess quality.

    Input: List of raw data records
    Output: Structure analysis with field types, patterns,
            and asset indicators
    """

    def __init__(self, context_info: Dict[str, Any]):
        super().__init__()
        self._context_info = context_info

    async def _arun(self, raw_data: List[Dict[str, Any]]) -> str:
        """Async implementation to analyze structure"""
        result = await DataStructureAnalyzerImpl.analyze_structure(
            raw_data, self._context_info
        )
        return json.dumps(result)

    def _run(self, raw_data: List[Dict[str, Any]]) -> str:
        """Sync wrapper for async implementation"""
        try:
            loop = asyncio.get_running_loop()
            # Already in an event loop, create task
            future = asyncio.ensure_future(self._arun(raw_data))
            # This will block but won't create a new loop
            return loop.run_until_complete(future)
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self._arun(raw_data))


class BaseFieldSuggestionTool(BaseTool):
    """Base tool for suggesting field mappings"""

    name: str = "field_suggestion_generator"
    description: str = """
    Generate intelligent field mapping suggestions based on data patterns.
    Use this to suggest how source fields should map to target schema.

    Input: Dictionary with source_fields and optional target_schema
    Output: Mapping suggestions with confidence scores
    """

    def __init__(self, context_info: Dict[str, Any]):
        super().__init__()
        self._context_info = context_info

    def _run(self, **kwargs) -> str:
        """Generate field mapping suggestions"""
        # Handle multiple parameter formats for maximum compatibility
        # The agent might pass data in various formats, so we accept **kwargs
        # and figure out the actual data structure

        # Check if 'mapping_request' key exists (expected format)
        if "mapping_request" in kwargs:
            # Could be nested or direct
            mapping_data = kwargs["mapping_request"]
            if isinstance(mapping_data, dict) and "mapping_request" in mapping_data:
                # Double wrapped - extract inner
                actual_request = mapping_data["mapping_request"]
            else:
                # Single wrapped - use directly
                actual_request = mapping_data
        # Check if data is passed directly with source_fields
        elif "source_fields" in kwargs:
            # Direct format - agent passed data directly
            actual_request = kwargs
        # Try first positional argument if exists
        elif len(kwargs) == 1:
            # Single dict passed, use it
            actual_request = next(iter(kwargs.values()))
        else:
            # Fallback - use all kwargs as the request
            actual_request = kwargs

        result = FieldSuggestionImpl.generate_suggestions(actual_request)
        return json.dumps(result)


class BaseDataQualityAssessmentTool(BaseTool):
    """Base tool for assessing data quality"""

    name: str = "data_quality_assessor"
    description: str = """
    Assess the overall quality of imported data.
    Use this to determine if data is ready for processing or
    needs cleansing.

    Input: List of raw data records
    Output: Quality assessment with scores and recommendations
    """

    def __init__(self, context_info: Dict[str, Any]):
        super().__init__()
        self._context_info = context_info

    def _run(self, raw_data: List[Dict[str, Any]]) -> str:
        """Assess data quality"""
        result = DataQualityImpl.assess_quality(raw_data)
        return json.dumps(result)


# Dummy classes for when CrewAI is not available
class DummyDataValidationTool:
    def __init__(self, context_info: Dict[str, Any]):
        pass


class DummyDataStructureAnalyzerTool:
    def __init__(self, context_info: Dict[str, Any]):
        pass


class DummyFieldSuggestionTool:
    def __init__(self, context_info: Dict[str, Any]):
        pass


class DummyDataQualityAssessmentTool:
    def __init__(self, context_info: Dict[str, Any]):
        pass
