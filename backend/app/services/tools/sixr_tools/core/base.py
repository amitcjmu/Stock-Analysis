"""
Base classes and common imports for 6R Analysis Tools.
Contains shared functionality and fallback implementations.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Common logger for all sixr tools
logger = logging.getLogger(__name__)

try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    SIXR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Tool imports failed: {e}")

    # Fallback classes for testing
    class BaseTool:
        def __init__(self, **kwargs):
            pass

    class BaseModel:
        def __init__(self, **kwargs):
            pass

    def Field(*args, **kwargs):
        return None

    SIXR_AVAILABLE = False


# Import schemas and services only when needed (lazy imports)
def get_sixr_imports():
    """Lazy import of SixR-specific classes to avoid circular imports."""
    try:
        from app.schemas.sixr_analysis import SixRParameterBase, SixRStrategy
        from app.services.field_mapper_modular import FieldMapperService
        from app.services.sixr_engine_modular import SixRDecisionEngine

        return SixRParameterBase, SixRStrategy, FieldMapperService, SixRDecisionEngine
    except ImportError:
        return None, None, None, None


# Export common classes and utilities
__all__ = [
    "BaseTool",
    "BaseModel",
    "Field",
    "logger",
    "SIXR_AVAILABLE",
    "json",
    "get_sixr_imports",
]
