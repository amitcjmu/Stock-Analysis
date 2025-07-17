"""
Console Manager for CrewAI Event Listeners
Ensures only one Rich console/live display is active at a time to prevent conflicts.
"""

import threading
from contextlib import contextmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ConsoleManager:
    """Singleton manager to ensure only one Rich console is active at a time."""
    
    _instance = None
    _lock = threading.Lock()
    _console = None
    _live_display = None
    _active_count = 0
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Initialize only once
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._console_lock = threading.Lock()
            logger.info("ConsoleManager initialized")
    
    @contextmanager
    def get_console(self):
        """Get console in a thread-safe manner."""
        with self._console_lock:
            try:
                # Disable Rich console output during event processing
                # This prevents "Only one live display may be active at once" errors
                import os
                original_term = os.environ.get('TERM')
                os.environ['TERM'] = 'dumb'  # Disable Rich formatting
                
                yield None  # Don't actually provide a console
                
            finally:
                # Restore original TERM setting
                if original_term:
                    os.environ['TERM'] = original_term
                else:
                    os.environ.pop('TERM', None)
    
    def disable_rich_output(self):
        """Disable Rich console output globally."""
        try:
            import os
            os.environ['TERM'] = 'dumb'
            logger.info("Rich output disabled for event processing")
        except Exception as e:
            logger.warning(f"Could not disable Rich output: {e}")
    
    def enable_rich_output(self):
        """Re-enable Rich console output."""
        try:
            import os
            if 'TERM' in os.environ and os.environ['TERM'] == 'dumb':
                os.environ.pop('TERM', None)
            logger.info("Rich output re-enabled")
        except Exception as e:
            logger.warning(f"Could not re-enable Rich output: {e}")

# Global instance
console_manager = ConsoleManager()