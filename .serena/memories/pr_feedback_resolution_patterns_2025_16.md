# PR Feedback Resolution Patterns

## Insight 1: Qodo Bot Critical Issue Response
**Problem**: Bot identifies production-breaking issues in PR
**Solution**: Use specialized agent to address all issues systematically
**Code**:
```python
Task(
    description="Fix PR feedback issues",
    subagent_type="python-crewai-fastapi-expert",
    prompt="""
    PRIORITY ISSUES TO FIX:
    1. CRITICAL - [Issue description] (Importance: 10/10)
    2. HIGH - [Issue description] (Importance: 8/10)
    3. MEDIUM - [Issue description] (Importance: 7/10)
    """
)
```
**Usage**: Always prioritize by importance score, fix highest first

## Insight 2: Shared Storage Implementation
**Problem**: State lost across multiple process instances
**Solution**: Implement with Redis primary, in-memory fallback
**Pattern**:
```python
# In class __init__:
def __init__(self, redis_client=None):
    if redis_client and redis_client.ping():
        self.state_manager = SharedStateManager(redis_client)
    else:
        logger.warning("Redis unavailable, using in-memory state")
        self.state_manager = SharedStateManager(None)
```
**Usage**: Never fail if Redis unavailable - graceful degradation

## Insight 3: Performance Reordering Fix
**Problem**: Only partially sorting levels, appending rest unsorted
**Solution**: Sort ALL levels, rebuild complete sequence
**Code**:
```python
# WRONG - partial sort
sorted_levels = sorted(level_performance.items(), key=lambda x: x[1])
reordered = []
for level, _ in sorted_levels:
    if performance_acceptable:
        reordered.append((level, services))
# Appends unsorted remainder

# CORRECT - complete sort
sorted_levels = sorted(level_performance.items(), key=lambda x: x[1])
level_to_services = dict(sequence)
reordered = [(level, level_to_services[level]) for level, _ in sorted_levels]
```
**Usage**: When reordering, always maintain complete sequence

## Insight 4: Frequency Calculation Accuracy
**Problem**: Using max(time_span_hours, 1.0) creates incorrect frequencies
**Solution**: Handle sub-hour intervals properly
**Code**:
```python
# WRONG
return len(self.access_times) / max(time_span_hours, 1.0)

# CORRECT
time_span_seconds = (newest - oldest).total_seconds()
if time_span_seconds < 1:
    return len(self.access_times) * 3600  # Extrapolate
time_span_hours = time_span_seconds / 3600
return len(self.access_times) / time_span_hours
```
**Usage**: Never artificially cap denominators in rate calculations
