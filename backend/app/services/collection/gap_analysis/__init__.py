"""
Lean Gap Analysis Service - Single Persistent Agent

Uses TenantScopedAgentPool (ADR-015) for gap detection and questionnaire generation.
Replaces bloated 3-agent crew with direct asset comparison and single-task processing.
"""

from app.services.collection.gap_analysis.service import GapAnalysisService

__all__ = ["GapAnalysisService"]
