"""
DeepInfra Completion Wrapper
Provides a wrapper around litellm completion calls to handle DeepInfra's logprobs issues
"""

import logging

import litellm

logger = logging.getLogger(__name__)


def safe_deepinfra_completion(**kwargs):
    """
    Safe wrapper for litellm completion that handles DeepInfra's null logprobs response.
    """
    model = kwargs.get("model", "")
    
    # Force logprobs to False for DeepInfra models
    if "deepinfra" in model.lower():
        kwargs["logprobs"] = False
        kwargs.pop("top_logprobs", None)
        
    try:
        # Make the actual call
        response = litellm.completion(**kwargs)
        
        # If it's a DeepInfra model and response has logprobs, remove them
        if "deepinfra" in model.lower() and hasattr(response, 'choices'):
            for choice in response.choices:
                if hasattr(choice, 'logprobs'):
                    # Remove logprobs attribute entirely to avoid issues
                    delattr(choice, 'logprobs')
                    
        return response
        
    except Exception as e:
        # If the error is related to logprobs, try to fix the response
        if "logprobs" in str(e).lower() and "deepinfra" in model.lower():
            logger.warning(f"DeepInfra logprobs error detected, attempting workaround: {e}")
            
            # Try calling without any logprobs-related parameters
            clean_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['logprobs', 'top_logprobs']}
            clean_kwargs['logprobs'] = False
            
            try:
                response = litellm.completion(**clean_kwargs)
                
                # Clean response
                if hasattr(response, 'choices'):
                    for choice in response.choices:
                        if hasattr(choice, 'logprobs'):
                            delattr(choice, 'logprobs')
                            
                return response
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                raise retry_error
        else:
            raise e


async def safe_deepinfra_acompletion(**kwargs):
    """
    Safe async wrapper for litellm acompletion that handles DeepInfra's null logprobs response.
    """
    model = kwargs.get("model", "")
    
    # Force logprobs to False for DeepInfra models
    if "deepinfra" in model.lower():
        kwargs["logprobs"] = False
        kwargs.pop("top_logprobs", None)
        
    try:
        # Make the actual call
        response = await litellm.acompletion(**kwargs)
        
        # If it's a DeepInfra model and response has logprobs, remove them
        if "deepinfra" in model.lower() and hasattr(response, 'choices'):
            for choice in response.choices:
                if hasattr(choice, 'logprobs'):
                    # Remove logprobs attribute entirely to avoid issues
                    delattr(choice, 'logprobs')
                    
        return response
        
    except Exception as e:
        # If the error is related to logprobs, try to fix the response
        if "logprobs" in str(e).lower() and "deepinfra" in model.lower():
            logger.warning(f"DeepInfra logprobs error detected, attempting workaround: {e}")
            
            # Try calling without any logprobs-related parameters
            clean_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['logprobs', 'top_logprobs']}
            clean_kwargs['logprobs'] = False
            
            try:
                response = await litellm.acompletion(**clean_kwargs)
                
                # Clean response
                if hasattr(response, 'choices'):
                    for choice in response.choices:
                        if hasattr(choice, 'logprobs'):
                            delattr(choice, 'logprobs')
                            
                return response
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                raise retry_error
        else:
            raise e


# Store originals before any patching
_original_completion = litellm.completion
_original_acompletion = litellm.acompletion


def safe_deepinfra_completion_internal(**kwargs):
    """Internal version that calls the original litellm function"""
    model = kwargs.get("model", "")
    
    # Force logprobs to False for DeepInfra models
    if "deepinfra" in model.lower():
        kwargs["logprobs"] = False
        kwargs.pop("top_logprobs", None)
        
    try:
        # Make the actual call using the original function
        response = _original_completion(**kwargs)
        
        # If it's a DeepInfra model and response has logprobs, remove them
        if "deepinfra" in model.lower() and hasattr(response, 'choices'):
            for choice in response.choices:
                if hasattr(choice, 'logprobs'):
                    # Remove logprobs attribute entirely to avoid issues
                    delattr(choice, 'logprobs')
                    
        return response
        
    except Exception as e:
        logger.error(f"DeepInfra completion error: {e}")
        raise e


async def safe_deepinfra_acompletion_internal(**kwargs):
    """Internal async version that calls the original litellm function"""
    model = kwargs.get("model", "")
    
    # Force logprobs to False for DeepInfra models
    if "deepinfra" in model.lower():
        kwargs["logprobs"] = False
        kwargs.pop("top_logprobs", None)
        
    try:
        # Make the actual call using the original function
        response = await _original_acompletion(**kwargs)
        
        # If it's a DeepInfra model and response has logprobs, remove them
        if "deepinfra" in model.lower() and hasattr(response, 'choices'):
            for choice in response.choices:
                if hasattr(choice, 'logprobs'):
                    # Remove logprobs attribute entirely to avoid issues
                    delattr(choice, 'logprobs')
                    
        return response
        
    except Exception as e:
        logger.error(f"DeepInfra acompletion error: {e}")
        raise e


def patch_litellm_for_deepinfra():
    """
    Monkey patch litellm to use our safe wrappers for DeepInfra.
    This ensures all DeepInfra calls go through our error handling.
    """
    
    def patched_completion(**kwargs):
        model = kwargs.get("model", "")
        if "deepinfra" in model.lower():
            return safe_deepinfra_completion_internal(**kwargs)
        return _original_completion(**kwargs)
    
    async def patched_acompletion(**kwargs):
        model = kwargs.get("model", "")
        if "deepinfra" in model.lower():
            return await safe_deepinfra_acompletion_internal(**kwargs)
        return await _original_acompletion(**kwargs)
    
    # Apply patches
    litellm.completion = patched_completion
    litellm.acompletion = patched_acompletion
    
    logger.info("Applied DeepInfra completion patches to litellm")


# Auto-patch when imported
patch_litellm_for_deepinfra()