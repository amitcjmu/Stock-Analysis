"""
Agent Reasoning Patterns - Core Intelligence Architecture

This module defines the reasoning patterns that CrewAI agents use to analyze assets
and discover business value, risk factors, and modernization opportunities.

This file maintains backward compatibility by importing from the modularized
agent_reasoning_patterns package while providing the same interface.

Instead of hard-coded rules, agents learn and apply insights through:
1. Pattern discovery and storage in Tier 3 memory
2. Evidence-based reasoning using discovered patterns
3. Continuous learning from user feedback and validation
4. Multi-dimensional analysis covering business, technical, and strategic factors
"""

# Legacy imports for backward compatibility
import logging

# Import all classes and functions from the modularized packages
# These star imports are necessary for backward compatibility
from .causal_patterns import *  # noqa: F403,F401
from .decision_trees import *  # noqa: F403,F401
from .learning_patterns import *  # noqa: F403,F401
from .logical_patterns import *  # noqa: F403,F401
from .probabilistic import *  # noqa: F403,F401
from .temporal_patterns import *  # noqa: F403,F401

# Set up module-level logger for any legacy code
logger = logging.getLogger(__name__)
