"""
System prompts for contextual chat service.

Modularized for maintainability - split from prompts.py (527 lines) into:
- base_prompts.py: Foundation prompt for all interactions
- flow_prompts.py: Flow-specific context (discovery, collection, assessment, etc.)
- page_prompts.py: Page-level detailed guidance
- workflow_prompts.py: Step-by-step workflow instructions by phase

This __init__.py preserves backward compatibility by exporting all prompts.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

from .base_prompts import BASE_SYSTEM_PROMPT
from .flow_prompts import FLOW_TYPE_PROMPTS
from .page_prompts import PAGE_SPECIFIC_PROMPTS
from .workflow_prompts import GUIDED_WORKFLOW_PROMPTS

__all__ = [
    "BASE_SYSTEM_PROMPT",
    "FLOW_TYPE_PROMPTS",
    "PAGE_SPECIFIC_PROMPTS",
    "GUIDED_WORKFLOW_PROMPTS",
]
