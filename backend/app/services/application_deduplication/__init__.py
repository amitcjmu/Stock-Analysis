"""
Application Deduplication Service Module
"""

from .service import ApplicationDeduplicationService, create_deduplication_service
from .config import DeduplicationConfig
from .types import DeduplicationResult

__all__ = [
    "ApplicationDeduplicationService",
    "create_deduplication_service",
    "DeduplicationConfig",
    "DeduplicationResult",
]
