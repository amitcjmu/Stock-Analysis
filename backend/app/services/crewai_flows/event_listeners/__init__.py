"""
CrewAI Event Listeners Package

Following the CrewAI Event Listener documentation pattern:
https://docs.crewai.com/concepts/event-listener#properly-registering-your-listener

This ensures the discovery_flow_listener is loaded when the package is imported,
exactly like CrewAI's built-in agentops_listener is registered.
"""

from .discovery_flow_listener import discovery_flow_listener

# Export the listener instance to ensure it's loaded and active
__all__ = ["discovery_flow_listener"]
