"""
Decommission Flow MFO Integration Layer - Public API

This module preserves backward compatibility after modularization.
All original functions remain importable from this package.

Modularization Structure (Pre-commit file length requirement):
- create.py: Creation operations (create_decommission_via_mfo)
- queries.py: Read operations (get_decommission_status_via_mfo)
- updates.py: Update operations (update_decommission_phase_via_mfo)
- lifecycle.py: Lifecycle operations (resume, pause)

Reference: ADR-006 (Master Flow Orchestrator), ADR-012 (Flow Status Management)
"""

from .create import create_decommission_via_mfo
from .queries import get_decommission_status_via_mfo
from .updates import update_decommission_phase_via_mfo
from .lifecycle import (
    resume_decommission_flow,
    pause_decommission_flow,
    cancel_decommission_flow,
)

__all__ = [
    "create_decommission_via_mfo",
    "get_decommission_status_via_mfo",
    "update_decommission_phase_via_mfo",
    "resume_decommission_flow",
    "pause_decommission_flow",
    "cancel_decommission_flow",
]
