"""
CrewAI LLM Wrapper with Rate Limiting
Wraps CrewAI LLM calls with rate limiting to prevent 429 errors.
"""

import asyncio
import logging
from functools import wraps

from app.services.llm_config import LLM
from app.services.llm_rate_limiter import llm_rate_limiter

logger = logging.getLogger(__name__)


class RateLimitedLLM:
    """
    A wrapper around CrewAI LLM that adds rate limiting.
    This prevents 429 errors from DeepInfra.
    """
    
    def __init__(self, base_llm: LLM):
        self.base_llm = base_llm
        self.model = getattr(base_llm, 'model', 'default')
        
        # Copy all attributes from base LLM
        for attr in dir(base_llm):
            if not attr.startswith('_') and not hasattr(self, attr):
                setattr(self, attr, getattr(base_llm, attr))
    
    def __getattr__(self, name):
        """Delegate attribute access to base LLM"""
        return getattr(self.base_llm, name)
    
    async def _make_rate_limited_call(self, method_name: str, *args, **kwargs):
        """Make a rate-limited call to the base LLM"""
        method = getattr(self.base_llm, method_name)
        
        # If it's not an async method, wrap it
        if not asyncio.iscoroutinefunction(method):
            async def async_wrapper(*a, **kw):
                return method(*a, **kw)
            method = async_wrapper
        
        return await llm_rate_limiter.execute_with_rate_limit(
            self.model,
            method,
            *args,
            **kwargs
        )
    
    def __call__(self, *args, **kwargs):
        """
        Make the LLM callable with rate limiting.
        This handles synchronous calls by running them in an event loop.
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                asyncio.create_task(self._make_rate_limited_call('__call__', *args, **kwargs))
                # For sync compatibility, we need to block until complete
                # This is not ideal but necessary for CrewAI compatibility
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    return executor.submit(asyncio.run, self._make_rate_limited_call('__call__', *args, **kwargs)).result()
            else:
                # If no loop is running, create one
                return asyncio.run(self._make_rate_limited_call('__call__', *args, **kwargs))
        except RuntimeError:
            # Fallback to creating a new event loop
            return asyncio.run(self._make_rate_limited_call('__call__', *args, **kwargs))
    
    # Wrap common LLM methods
    async def generate(self, *args, **kwargs):
        """Generate text with rate limiting"""
        return await self._make_rate_limited_call('generate', *args, **kwargs)
    
    async def chat(self, *args, **kwargs):
        """Chat completion with rate limiting"""
        return await self._make_rate_limited_call('chat', *args, **kwargs)
    
    async def complete(self, *args, **kwargs):
        """Text completion with rate limiting"""
        return await self._make_rate_limited_call('complete', *args, **kwargs)


def get_rate_limited_crewai_llm(base_llm=None):
    """
    Get a rate-limited CrewAI LLM instance.
    This should be used instead of get_crewai_llm() to prevent rate limit errors.
    
    Args:
        base_llm: Optional base LLM instance. If not provided, will create one.
    """
    from app.services.simple_rate_limiter import add_simple_rate_limiting
    
    # If no base LLM provided, create one directly from llm_config to avoid circular import
    if base_llm is None:
        from app.services.llm_config import llm_config
        base_llm = llm_config.get_crewai_llm()
    
    return add_simple_rate_limiting(base_llm)


def apply_rate_limiting_to_crew(crew):
    """
    Apply rate limiting to all agents in a crew.
    This modifies the crew's agents to use rate-limited LLMs.
    """
    if hasattr(crew, 'agents') and crew.agents:
        rate_limited_llm = get_rate_limited_crewai_llm()
        
        for agent in crew.agents:
            if hasattr(agent, 'llm'):
                # Replace the agent's LLM with a rate-limited version
                agent.llm = rate_limited_llm
                logger.info(f"Applied rate limiting to agent: {getattr(agent, 'role', 'Unknown')}")
    
    return crew


# Monkey patch for CrewAI service to use rate-limited LLMs
def patch_crewai_service_for_rate_limiting():
    """
    Patch the CrewAI service to automatically use rate-limited LLMs.
    This should be called during application startup.
    """
    try:
        from app.services.crewai_service import CrewAIService
        
        # Store original create_agent method
        original_create_agent = CrewAIService.create_agent
        
        def rate_limited_create_agent(self, *args, **kwargs):
            # Call original method
            agent = original_create_agent(self, *args, **kwargs)
            
            # Replace LLM with rate-limited version if not already done
            if hasattr(agent, 'llm') and not isinstance(agent.llm, RateLimitedLLM):
                agent.llm = get_rate_limited_crewai_llm()
                logger.debug(f"Applied rate limiting to agent: {getattr(agent, 'role', 'Unknown')}")
            
            return agent
        
        # Replace the method
        CrewAIService.create_agent = rate_limited_create_agent
        
        logger.info("✅ Successfully patched CrewAI service for rate limiting")
        
    except Exception as e:
        logger.error(f"Failed to patch CrewAI service for rate limiting: {e}")


# Decorator for rate-limiting any LLM function
def rate_limit_llm(model: str = "default"):
    """
    Decorator to add rate limiting to any LLM function.
    
    Usage:
        @rate_limit_llm("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8")
        async def my_llm_function():
            # LLM call here
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await llm_rate_limiter.execute_with_rate_limit(
                model,
                func,
                *args,
                **kwargs
            )
        return wrapper
    return decorator