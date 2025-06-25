"""
Discovery endpoints package
"""

# Make this directory a proper Python package 
# Export the main discovery router to resolve naming conflicts
from ..discovery_main import router

__all__ = ["router"] 