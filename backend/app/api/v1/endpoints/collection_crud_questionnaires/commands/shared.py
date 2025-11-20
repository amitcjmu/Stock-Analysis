"""Shared state for collection questionnaire commands."""

# Track background tasks to prevent memory leaks
_background_tasks: set = set()
