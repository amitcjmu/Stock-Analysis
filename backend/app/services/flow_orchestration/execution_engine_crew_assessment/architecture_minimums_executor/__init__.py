"""
Execution Engine - Architecture Minimums Executor

Mixin for executing architecture minimums (compliance validation) phase.
Issue #1243: Three-level compliance validation using CrewAI agent.

Three-Level Validation:
- Level 1: OS Compliance (Asset.operating_system/os_version vs engagement standards)
- Level 2: Application Compliance (COTS apps vs vendor EOL dates)
- Level 3: Component Compliance (databases, runtimes, frameworks)

DB-first, RAG-augment strategy:
1. Query VendorProductsCatalog → ProductVersionsCatalog → LifecycleMilestones
2. On cache miss, use RAG to look up EOL data from endoflife.date
3. Cache results back to catalog for future lookups
"""

from .executor import ArchitectureMinimumsExecutorMixin
from .helpers import (
    aggregate_asset_data,
    build_empty_result,
    build_error_result,
    fallback_deterministic_validation,
    get_default_standards,
    transform_agent_result,
)
from .prompts import THREE_LEVEL_COMPLIANCE_PROMPT

__all__ = [
    "ArchitectureMinimumsExecutorMixin",
    "THREE_LEVEL_COMPLIANCE_PROMPT",
    "aggregate_asset_data",
    "build_empty_result",
    "build_error_result",
    "fallback_deterministic_validation",
    "get_default_standards",
    "transform_agent_result",
]
