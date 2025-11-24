"""
Section Question Generator - Modularized for <400 lines per file.

Public API preserves backward compatibility.

CC Generated for Issue #1113 - SectionQuestionGenerator Modularization
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

from .generator import SectionQuestionGenerator

__all__ = ["SectionQuestionGenerator"]
