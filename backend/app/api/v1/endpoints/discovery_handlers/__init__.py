"""
Discovery Handlers Package
Modular handlers for different discovery operations.
"""

from .feedback import FeedbackHandler
from .templates import TemplateHandler

__all__ = [
    "TemplateHandler",
    "FeedbackHandler",
]
