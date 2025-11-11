"""
Gap-to-Questionnaire Adapter Package

Bridges GapAnalyzer ComprehensiveGapReport to IntelligentQuestionnaireGenerator.
Transforms multi-layer gap analysis into targeted questionnaire generation.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 14
Author: CC (Claude Code)
GPT-5 Recommendations: #1 (tenant scoping), #3 (async), #8 (JSON safety)
"""

from .adapter import GapToQuestionnaireAdapter

__all__ = ["GapToQuestionnaireAdapter"]
