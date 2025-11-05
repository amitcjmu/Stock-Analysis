"""
Decommission Flow API Endpoints

This package contains all decommission flow API endpoints following ADR-006 MFO pattern.
"""

from .flow_management import router

__all__ = ["router"]
