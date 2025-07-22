"""
Global Rich console configuration to prevent conflicts.
Ensures only one Rich console/live display is active across the application.
"""

import logging
import os

logger = logging.getLogger(__name__)

def configure_rich_for_backend():
    """
    Configure Rich console for backend usage to prevent conflicts.
    This is especially important when running with CrewAI which may use Rich internally.
    """
    try:
        # Disable Rich output in production/backend environments
        # This prevents "Only one live display may be active at once" errors
        if os.environ.get('DISABLE_RICH_OUTPUT', 'false').lower() == 'true':
            os.environ['TERM'] = 'dumb'
            logger.info("Rich output disabled via DISABLE_RICH_OUTPUT env var")
            return
        
        # Check if we're running in a non-interactive environment
        if not os.isatty(0):  # stdin is not a terminal
            os.environ['TERM'] = 'dumb'
            logger.info("Rich output disabled - non-interactive environment detected")
            return
        
        # For Docker/container environments
        if os.environ.get('DOCKER_CONTAINER') or os.path.exists('/.dockerenv'):
            os.environ['TERM'] = 'dumb'
            logger.info("Rich output disabled - Docker environment detected")
            return
            
        # For CI/CD environments
        ci_env_vars = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS']
        if any(os.environ.get(var) for var in ci_env_vars):
            os.environ['TERM'] = 'dumb'
            logger.info("Rich output disabled - CI environment detected")
            return
        
        # Configure Rich to be less aggressive with live displays
        os.environ['FORCE_COLOR'] = '0'  # Disable forced colors
        os.environ['NO_COLOR'] = '1'      # Respect NO_COLOR standard
        
        logger.info("Rich console configured for backend usage")
        
    except Exception as e:
        logger.warning(f"Could not configure Rich console: {e}")

# Auto-configure on import
configure_rich_for_backend()