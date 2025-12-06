"""
EOL Lifecycle Service

ADR-039: Architecture Standards Compliance and EOL Lifecycle Integration

This module provides EOL (End of Life) status checking for operating systems,
runtimes, databases, and vendor products. It uses a three-tier lookup:

1. Redis cache (24h TTL)
2. endoflife.date API (authoritative source)
3. Fallback heuristics (hardcoded patterns)

Usage:
    from app.services.eol_lifecycle import get_eol_service, EOLStatus

    service = await get_eol_service(redis_client)
    status = await service.get_eol_status("Windows Server", "2012", "os")

    if status.status == "eol_expired":
        # Handle expired product
        pass
"""

from .eol_lifecycle_service import EOLLifecycleService, get_eol_service
from .fallback_heuristics import fallback_eol_check
from .models import (
    EOLBatchResult,
    EOLDataSource,
    EOLStatus,
    EOLStatusEnum,
    SupportTypeEnum,
)
from .vendor_catalog import get_vendor_eol_status, VENDOR_LIFECYCLE_CATALOG

__all__ = [
    # Service
    "EOLLifecycleService",
    "get_eol_service",
    # Models
    "EOLStatus",
    "EOLStatusEnum",
    "SupportTypeEnum",
    "EOLDataSource",
    "EOLBatchResult",
    # Fallback
    "fallback_eol_check",
    # Vendor catalog
    "get_vendor_eol_status",
    "VENDOR_LIFECYCLE_CATALOG",
]
