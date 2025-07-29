"""
DeepInfra Response Fixer
Patches litellm's response parsing to handle DeepInfra's null top_logprobs
"""

import logging

logger = logging.getLogger(__name__)


def patch_litellm_response_parsing():
    """
    Patch litellm's response parsing to handle DeepInfra's null top_logprobs.
    This is a more targeted approach that fixes the parsing issue.
    """
    try:
        # Import the specific module that does response parsing
        from litellm.types.utils import ChoiceLogprobs

        # Store the original ChoiceLogprobs class
        _OriginalChoiceLogprobs = ChoiceLogprobs

        # Create a patched version
        class PatchedChoiceLogprobs(_OriginalChoiceLogprobs):
            def __init__(self, **data):
                # Fix content if it has null top_logprobs
                if "content" in data and isinstance(data["content"], list):
                    fixed_content = []
                    for i, item in enumerate(data["content"]):
                        if isinstance(item, dict):
                            # Create a copy to avoid modifying original
                            item_copy = item.copy()
                            # Fix None top_logprobs
                            if (
                                "top_logprobs" in item_copy
                                and item_copy["top_logprobs"] is None
                            ):
                                item_copy["top_logprobs"] = []
                            fixed_content.append(item_copy)
                        else:
                            fixed_content.append(item)
                    data["content"] = fixed_content

                # Call parent constructor with fixed data
                try:
                    super().__init__(**data)
                except Exception as e:
                    logger.warning(
                        f"ChoiceLogprobs init error (attempting recovery): {e}"
                    )
                    # If it still fails, try creating a minimal valid object
                    try:
                        # Create minimal valid data
                        minimal_data = {}
                        if "content" in data:
                            # Try to extract just the text content
                            content_items = []
                            for item in data.get("content") or []:
                                if isinstance(item, dict):
                                    # Keep only essential fields
                                    clean_item = {
                                        "token": item.get("token", ""),
                                        "logprob": item.get("logprob", 0.0),
                                        "top_logprobs": [],  # Always use empty list
                                    }
                                    if "bytes" in item:
                                        clean_item["bytes"] = item["bytes"]
                                    content_items.append(clean_item)
                            minimal_data["content"] = content_items
                        super().__init__(**minimal_data)
                    except Exception as e2:
                        logger.error(
                            f"Failed to create even minimal ChoiceLogprobs: {e2}"
                        )
                        # Last resort - create without content
                        super().__init__()

        # Replace in the types module
        import litellm.types.utils as types_module

        types_module.ChoiceLogprobs = PatchedChoiceLogprobs

        # Also replace in the main litellm module if it's imported there
        import litellm

        if hasattr(litellm, "ChoiceLogprobs"):
            litellm.ChoiceLogprobs = PatchedChoiceLogprobs

        logger.info(
            "Successfully patched litellm response parsing for DeepInfra null top_logprobs"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to patch litellm response parsing: {e}")
        return False


def apply_alternative_fix():
    """
    Alternative fix: Patch the specific validation that's failing
    """
    try:
        # Import all the types that might have top_logprobs
        from litellm.types.utils import ChatCompletionTokenLogprob

        # Try different patching approaches

        # Approach 1: Monkey-patch the __init__ method
        original_init = ChatCompletionTokenLogprob.__init__

        def patched_init(self, **data):
            # Fix top_logprobs before calling original init
            if "top_logprobs" in data and data["top_logprobs"] is None:
                data["top_logprobs"] = []
            original_init(self, **data)

        ChatCompletionTokenLogprob.__init__ = patched_init

        # Approach 2: Also patch field validation if possible
        try:
            # Try to modify the field directly
            if hasattr(ChatCompletionTokenLogprob, "__fields__"):
                for field_name, field in ChatCompletionTokenLogprob.__fields__.items():
                    if field_name == "top_logprobs":
                        # Make the field optional and default to empty list
                        field.required = False
                        field.default = []
        except Exception:
            pass

        logger.info("Applied alternative ChatCompletionTokenLogprob fix")
        return True

    except Exception as e:
        logger.error(f"Failed to apply alternative fix: {e}")
        return False


# Apply fixes when module is imported
success = patch_litellm_response_parsing()
if not success:
    logger.warning("Primary fix failed, trying alternative approach")
    apply_alternative_fix()
