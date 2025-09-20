"""
Unit tests for AssessmentFlowRepository with database operations

This module imports from modularized test classes while maintaining compatibility.
All test classes are now organized in test_modules/ for better maintainability.

Generated with CC for MFO compliance.
"""

# Import all test classes from modularized structure
from .test_modules.repository_tests.test_flow_operations import TestAssessmentFlowRepository
from .test_modules.repository_tests.test_queries import TestRepositoryQueries

# Re-export for pytest discovery
__all__ = [
    "TestAssessmentFlowRepository",
    "TestRepositoryQueries",
]

# This allows running the file directly for testing
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
