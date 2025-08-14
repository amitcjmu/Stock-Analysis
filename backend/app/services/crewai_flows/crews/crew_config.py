"""
Global configuration for CrewAI crews to ensure performance optimization
"""

# Maximum delegations allowed per agent
MAX_DELEGATIONS = 0  # NO DELEGATION - direct execution only

# Maximum iterations for crew execution
MAX_ITERATIONS = 1  # Single pass - no iterations

# Default configuration for all agents
DEFAULT_AGENT_CONFIG = {
    "allow_delegation": False,  # CRITICAL: No delegation ever
    "max_delegation": 0,
    "max_iter": 1,  # Single iteration only
    "allow_code_execution": False,  # Security setting
    "verbose": False,  # Reduce logging overhead
}

# Performance optimization settings
PERFORMANCE_CONFIG = {
    "use_fast_mode": True,  # Use optimized single agents where possible
    "enable_delegation": False,  # Disable delegation for all tasks
    "max_crew_execution_time": 300,  # 300 seconds max
    "single_pass_only": True,  # No iterations
}


def get_optimized_agent_config(allow_delegation: bool = False) -> dict:
    """
    Get optimized agent configuration - NO DELEGATION ALLOWED

    Args:
        allow_delegation: IGNORED - delegation is always disabled

    Returns:
        dict: Agent configuration with performance optimizations
    """
    # Always return no-delegation config for performance
    return DEFAULT_AGENT_CONFIG.copy()


def get_optimized_crew_config() -> dict:
    """
    Get optimized crew configuration - single pass, no iterations

    Returns:
        dict: Crew configuration for fast execution
    """
    return {
        "max_iterations": MAX_ITERATIONS,
        "verbose": False,
        "memory": False,  # Disable memory for speed
        "embedder": None,  # No embedding overhead
        "max_execution_time": PERFORMANCE_CONFIG["max_crew_execution_time"],
    }
