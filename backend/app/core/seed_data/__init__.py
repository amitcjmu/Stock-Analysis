"""
Seed Data Modules for Platform Initialization
Provides industry-standard templates and default configurations.
"""

from .assessment_standards import (get_default_standards,
                                   initialize_assessment_standards)

__all__ = ["initialize_assessment_standards", "get_default_standards"]
