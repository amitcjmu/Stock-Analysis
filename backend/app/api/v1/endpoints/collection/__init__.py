"""
Collection Bulk Operations Module

Provides endpoints for Collection Flow Adaptive Questionnaire Enhancements:
- Bulk answer operations
- Dynamic question filtering
- Bulk CSV/JSON import
- Gap analysis with weight-based progress tracking
"""

from fastapi import APIRouter

from . import bulk_answer, bulk_import, dynamic_questions, gap_analysis

# Create main collection router
# Prefix and tags will be set during registration in router_registry.py
router = APIRouter()

# Include sub-routers
router.include_router(bulk_answer.router)
router.include_router(bulk_import.router)
router.include_router(dynamic_questions.router)
router.include_router(gap_analysis.router)

__all__ = ["router"]
