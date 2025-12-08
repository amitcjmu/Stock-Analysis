"""
Planning flow export endpoint (backwards compatibility shim).

Actual implementation is in export_module/ subdirectory.
Issue #714: Full PDF and Excel export implementation.

Related ADRs:
- ADR-012: Two-Table Pattern (child flow operational state)
"""

from .export_module import router

__all__ = ["router"]
