"""
Assessment Flow MFO Integration Layer - Public API

This module preserves backward compatibility after modularization.
All original functions remain importable from this package.

Modularization Structure (Pre-commit file length requirement):
- create.py: Creation operations (create_assessment_via_mfo)
- queries.py: Read operations (get_assessment_status_via_mfo)
- updates.py: Update operations (update_assessment_via_mfo)
- lifecycle.py: Lifecycle operations (pause, resume, complete, delete)

Reference: ADR-006 (Master Flow Orchestrator), ADR-012 (Flow Status Management)
"""

from .create import create_assessment_via_mfo
from .queries import get_assessment_status_via_mfo
from .updates import update_assessment_via_mfo
from .lifecycle import (
    pause_assessment_flow,
    resume_assessment_flow,
    complete_assessment_flow,
    delete_assessment_flow,
)

__all__ = [
    "create_assessment_via_mfo",
    "get_assessment_status_via_mfo",
    "update_assessment_via_mfo",
    "pause_assessment_flow",
    "resume_assessment_flow",
    "complete_assessment_flow",
    "delete_assessment_flow",
]
