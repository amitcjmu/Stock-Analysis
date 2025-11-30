"""
Resource Service Package.

Provides resource planning operations with 6R-based estimation.
This module maintains backward compatibility with the original resource_service.py.
"""

from app.services.planning.resource_service.service import ResourceService

__all__ = ["ResourceService"]
