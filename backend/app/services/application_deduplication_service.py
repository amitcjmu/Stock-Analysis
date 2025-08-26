"""
Application Deduplication Service - Legacy Compatibility Module

This module provides backward compatibility for the refactored application deduplication service.
The actual implementation has been moved to app.services.application_deduplication for better
modularity and maintainability.
"""

# Re-export the main components for backward compatibility
from app.services.application_deduplication import (
    ApplicationDeduplicationService,
    create_deduplication_service,
    DeduplicationConfig,
    DeduplicationResult,
)
