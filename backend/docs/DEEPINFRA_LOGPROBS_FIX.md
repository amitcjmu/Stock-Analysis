# DeepInfra Logprobs Fix Documentation

## Problem Description

DeepInfra returns `logprobs` data in responses with `top_logprobs: null` even when we explicitly set `logprobs=False` in the request. This causes Pydantic validation errors in litellm:

```
pydantic_core._pydantic_core.ValidationError: validation errors for ChoiceLogprobs
content.0.top_logprobs
  Input should be a valid list [type=list_type, input_value=None, input_type=NoneType]
```

## Solution Overview

The fix consists of three components working together:

### 1. Input Callback (`llm_config.py`)
- Removes/sets `logprobs=False` in all DeepInfra requests
- Handles various parameter locations (kwargs, extra_body, optional_params)

### 2. Response Fixer (`deepinfra_response_fixer.py`) 
- Patches litellm's `ChoiceLogprobs` class to handle null `top_logprobs`
- Converts `None` to empty list `[]` before Pydantic validation
- Most effective component of the fix

### 3. Configuration Settings
- `litellm.drop_params = True` - Allows litellm to skip unsupported parameters
- CrewAI LLM instances configured without logprobs parameters

## How It Works

1. When the backend starts, `deepinfra_response_fixer.py` patches litellm's response parsing classes
2. The patched `ChoiceLogprobs` class intercepts responses and fixes null `top_logprobs` 
3. Input callbacks ensure we're not requesting logprobs in the first place
4. The combination prevents both request and response issues

## Files Modified

- `/backend/app/services/llm_config.py` - Main configuration and callbacks
- `/backend/app/services/deepinfra_response_fixer.py` - Response parsing patch
- `/backend/app/services/deepinfra_completion_wrapper.py` - Alternative wrapper (not currently used)

## Testing

The fix has been tested with:
- Direct litellm completion calls
- CrewAI agent execution
- Both sync and async operations

All tests pass successfully with the fix in place.

## Notes

- The fix is specific to DeepInfra models (checks for "deepinfra" in model name)
- No impact on other LLM providers
- The response fixer is the most critical component
- Input callbacks provide additional safety but aren't strictly necessary with the response fix