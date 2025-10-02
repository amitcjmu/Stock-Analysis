# LLM Usage Tracking Enforcement

## Overview

This directory contains `check_llm_calls.py`, a pre-commit hook that checks for proper LLM usage tracking across the codebase.

## Purpose

**ALL LLM API calls SHOULD be tracked** for cost monitoring, usage analysis, and compliance. The `multi_model_service` provides automatic tracking when used correctly.

**IMPORTANT**: This is a **WARNING-ONLY** check - it will NOT block commits. LLM tracking is an operational concern, not a code quality blocker.

## Usage

### Manual Check
```bash
# Check specific files
python scripts/check_llm_calls.py app/services/my_service.py

# Check entire codebase
python scripts/check_llm_calls.py

# Check before committing
python scripts/check_llm_calls.py $(git diff --cached --name-only --diff-filter=ACMR | grep '\.py$')
```

### Add to Pre-Commit (Optional)

If you want automatic enforcement on every commit, add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: check-llm-usage
        name: Check LLM Usage Tracking
        entry: python scripts/check_llm_calls.py
        language: python
        types: [python]
        pass_filenames: true
```

Then install:
```bash
pip install pre-commit
pre-commit install
```

## What It Checks

The script flags these **VIOLATIONS**:

❌ `litellm.completion()` - Direct call bypasses tracking
❌ `openai.chat.completions.create()` - Direct call bypasses tracking
❌ `client.chat.completions.create()` - Direct call bypasses tracking
❌ `completion(model=...)` - Direct call bypasses tracking

## Correct Usage

✅ **Use `multi_model_service.generate_response()`:**

```python
from app.services.multi_model_service import multi_model_service, TaskComplexity

# Chat/simple tasks
response = await multi_model_service.generate_response(
    prompt="What is machine learning?",
    task_type="chat",
    complexity=TaskComplexity.SIMPLE
)

# Agentic/complex tasks
response = await multi_model_service.generate_response(
    prompt="Analyze migration dependencies",
    task_type="field_mapping",
    complexity=TaskComplexity.AGENTIC
)
```

✅ **Legacy code exception (wrap with tracker):**

```python
from app.services.llm_usage_tracker import llm_tracker

async with llm_tracker.track_llm_call(
    provider="deepinfra",
    model=model_name,
    feature_context="crew_execution"
) as usage_log:
    response = litellm.completion(model=model, messages=messages)
    usage_log.input_tokens = response.usage.prompt_tokens
    usage_log.output_tokens = response.usage.completion_tokens
```

## Benefits of Tracking

- 📊 **Cost Monitoring**: View real-time LLM costs at `/finops/llm-costs`
- 📈 **Usage Analytics**: Track token consumption by model/feature
- 🎯 **Optimization**: Identify expensive calls for caching opportunities
- 🔍 **Debugging**: Trace failed LLM calls with request/response data
- 🏢 **Multi-Tenant**: Costs attributed to correct client/engagement

## Skipped Files

These files are allowed to have direct LLM calls:

- `app/services/llm_usage_tracker.py` - The tracker itself
- `app/services/multi_model_service.py` - The wrapper service
- `tests/` - Test files
- `alembic/` - Database migrations
- `scripts/check_llm_calls.py` - This checker script

## Automatic Tracking

### LiteLLM Callback (CrewAI + All LLM Calls)

The application automatically tracks **ALL** LLM calls via LiteLLM callback:

- **Installed at**: App startup (`app/app_setup/lifecycle.py:116`)
- **Tracks**: CrewAI agents (Llama 4), direct LiteLLM calls, all LLM providers
- **Logs to**: `migration.llm_usage_logs` table
- **Status**: Check logs for "✅ LiteLLM tracking callback installed"

### Multi-Model Service (Recommended)

For new code, use `multi_model_service` for cleaner API:

```python
from app.services.multi_model_service import multi_model_service, TaskComplexity

response = await multi_model_service.generate_response(
    prompt="Your prompt",
    task_type="chat",  # or "field_mapping" for agentic
    complexity=TaskComplexity.SIMPLE  # or AGENTIC
)
```

## Exit Codes

- `0` - Always (warnings only, never blocks commits)

## See Also

- **CLAUDE.md** - Full LLM usage policy and architecture
- **app/services/multi_model_service.py** - Implementation details
- **app/services/llm_usage_tracker.py** - Tracking logic
- **migration.llm_usage_logs** - Database table schema
