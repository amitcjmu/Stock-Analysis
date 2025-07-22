"""
DeepInfra Response Fixer
Patches litellm's response parsing to handle DeepInfra's null top_logprobs
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def patch_litellm_response_parsing():
    """
    Patch litellm's response parsing to handle DeepInfra's null top_logprobs.
    This is a more targeted approach that fixes the parsing issue.
    """
    try:
        # Import the specific module that does response parsing
        import litellm.litellm_core_utils.llm_response_utils.convert_dict_to_response as response_converter
        from litellm.types.utils import ChoiceLogprobs
        
        # Store the original ChoiceLogprobs class
        _OriginalChoiceLogprobs = ChoiceLogprobs
        
        # Create a patched version
        class PatchedChoiceLogprobs(_OriginalChoiceLogprobs):
            def __init__(self, **data):
                # Fix content if it has null top_logprobs
                if 'content' in data and isinstance(data['content'], list):
                    fixed_content = []
                    for item in data['content']:
                        if isinstance(item, dict):
                            # Create a copy to avoid modifying original
                            item_copy = item.copy()
                            if item_copy.get('top_logprobs') is None:
                                item_copy['top_logprobs'] = []
                            fixed_content.append(item_copy)
                        else:
                            fixed_content.append(item)
                    data['content'] = fixed_content
                
                # Call parent constructor with fixed data
                try:
                    super().__init__(**data)
                except Exception as e:
                    logger.warning(f"ChoiceLogprobs init error (attempting recovery): {e}")
                    # If it still fails, try without content
                    data_without_content = {k: v for k, v in data.items() if k != 'content'}
                    super().__init__(**data_without_content)
        
        # Replace in the types module
        import litellm.types.utils as types_module
        types_module.ChoiceLogprobs = PatchedChoiceLogprobs
        
        # Also replace in the main litellm module if it's imported there
        import litellm
        if hasattr(litellm, 'ChoiceLogprobs'):
            litellm.ChoiceLogprobs = PatchedChoiceLogprobs
            
        logger.info("Successfully patched litellm response parsing for DeepInfra null top_logprobs")
        return True
        
    except Exception as e:
        logger.error(f"Failed to patch litellm response parsing: {e}")
        return False


def apply_alternative_fix():
    """
    Alternative fix: Patch the specific validation that's failing
    """
    try:
        # Try to patch pydantic's validation for this specific case
        from litellm.types.utils import ChatCompletionTokenLogprob
        from pydantic import validator
        
        # Create a custom validator that handles None
        def fix_top_logprobs(cls, v):
            if v is None:
                return []
            return v
        
        # Add the validator to the class
        ChatCompletionTokenLogprob.__validator_top_logprobs = validator('top_logprobs', pre=True, allow_reuse=True)(fix_top_logprobs)
        
        logger.info("Applied alternative pydantic validator fix")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply alternative fix: {e}")
        return False


# Apply fixes when module is imported
success = patch_litellm_response_parsing()
if not success:
    logger.warning("Primary fix failed, trying alternative approach")
    apply_alternative_fix()