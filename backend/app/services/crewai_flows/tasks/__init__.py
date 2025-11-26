"""
CrewAI Task Definitions

This module contains task creation functions for CrewAI agents.
Tasks define what work agents should perform and what outputs are expected.
"""

from .planning_tasks import create_wave_planning_task

__all__ = ["create_wave_planning_task"]
