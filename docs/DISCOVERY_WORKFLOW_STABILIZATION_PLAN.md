# Discovery Workflow Stabilization Plan

## Overview
This plan focuses on enhancing the existing `crewai_flow_handlers` architecture to improve the reliability and robustness of the discovery workflow. The goal is to add proper error handling, retry mechanisms, and state management while maintaining the current architecture.

## Current Architecture

1. **Workflow Manager**: `DiscoveryWorkflowManager` orchestrates the workflow
2. **Handlers**: Individual handlers for each workflow step (data source analysis, validation, etc.)
3. **State Management**: `DiscoveryFlowState` tracks the workflow state

## Key Issues to Address

1. **Error Handling**
   - Inconsistent error handling across handlers
   - No retry mechanism for transient failures
   - Limited error context in logs

2. **State Management**
   - State transitions not explicitly validated
   - Limited visibility into workflow progress
   - No recovery mechanism for failed steps

3. **Observability**
   - Limited logging of workflow progress
   - No metrics on step execution times
   - Difficult to track down issues

## Implementation Plan

### Phase 1: Core Enhancements (2 days)

#### 1.1 Add Retry Mechanism
```python
# backend/app/services/crewai_flow_handlers/utils/retry.py
"""
Retry decorator for async functions with exponential backoff.
"""
import asyncio
import functools
import logging
from typing import Type, TypeVar, Callable, Any, Optional

logger = logging.getLogger(__name__)
T = TypeVar('T')

def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator that adds retry behavior to async functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.warning(
                            f"Retry {attempt}/{max_retries} for {func.__name__} "
                            f"after error: {str(last_exception)}"
                        )
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate next delay with exponential backoff
                    sleep_time = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Retrying {func.__name__} in {sleep_time:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(sleep_time)
            
            # This should never be reached due to the raise above
            raise RuntimeError("Unexpected error in retry logic")
            
        return wrapper
    return decorator
```

#### 1.2 Add State Validation
```python
# backend/app/services/crewai_flow_handlers/state_validation.py
"""
State validation for the discovery workflow.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, validator
from app.schemas.flow_schemas import DiscoveryFlowState

class WorkflowStateValidator:
    """Validates workflow state transitions and content."""
    
    @classmethod
    def validate_state_transition(
        cls, 
        current_state: DiscoveryFlowState, 
        new_state: DiscoveryFlowState
    ) -> bool:
        """Validate if the state transition is allowed."""
        # Define valid state transitions
        valid_transitions = {
            'pending': ['data_source_analysis', 'failed'],
            'data_source_analysis': ['data_validation', 'failed'],
            'data_validation': ['field_mapping', 'failed'],
            'field_mapping': ['asset_classification', 'failed'],
            'asset_classification': ['dependency_analysis', 'failed'],
            'dependency_analysis': ['database_integration', 'failed'],
            'database_integration': ['completed', 'failed'],
            'failed': ['retrying'],
            'retrying': [
                'data_source_analysis', 
                'data_validation', 
                'field_mapping', 
                'asset_classification', 
                'dependency_analysis', 
                'database_integration', 
                'failed'
            ],
            'completed': []  # Terminal state
        }
        
        current_phase = current_state.current_phase or 'pending'
        new_phase = new_state.current_phase or 'pending'
        
        if current_phase not in valid_transitions:
            raise ValueError(f"Unknown current phase: {current_phase}")
            
        if new_phase not in valid_transitions:
            raise ValueError(f"Unknown target phase: {new_phase}")
            
        if new_phase not in valid_transitions[current_phase]:
            raise ValueError(
                f"Invalid transition from '{current_phase}' to '{new_phase}'. "
                f"Allowed: {valid_transitions[current_phase]}"
            )
            
        return True
    
    @classmethod
    def validate_required_fields(
        cls,
        state: DiscoveryFlowState,
        phase: str
    ) -> None:
        """Validate that required fields are present for the current phase."""
        required_fields = {
            'data_source_analysis': ['cmdb_data', 'source_analysis'],
            'data_validation': ['validation_results'],
            'field_mapping': ['field_mappings'],
            'asset_classification': ['asset_classes'],
            'dependency_analysis': ['dependencies'],
            'database_integration': ['database_operations']
        }
        
        if phase not in required_fields:
            return
            
        missing = []
        for field in required_fields[phase]:
            if not hasattr(state, field) or getattr(state, field) is None:
                missing.append(field)
                
        if missing:
            raise ValueError(
                f"Missing required fields for phase '{phase}': {', '.join(missing)}"
            )

    @classmethod
    def validate_state_completion(
        cls,
        state: DiscoveryFlowState,
        phase: str
    ) -> bool:
        """Validate if the current phase is complete."""
        completion_flags = {
            'data_source_analysis': 'data_source_analysis_complete',
            'data_validation': 'data_validation_complete',
            'field_mapping': 'field_mapping_complete',
            'asset_classification': 'asset_classification_complete',
            'dependency_analysis': 'dependency_analysis_complete',
            'database_integration': 'database_integration_complete'
        }
        
        if phase not in completion_flags:
            return True
            
        return getattr(state, completion_flags[phase], False)
```

### Phase 2: Workflow Manager Enhancements (2 days)

#### 2.1 Enhanced Workflow Manager

The `DiscoveryWorkflowManager` has been enhanced with:
- Retry logic for each step
- State validation
- Better error handling and logging
- Progress tracking

Key improvements include:
- Individual step methods with retry decorators
- Centralized error handling
- Detailed logging of step execution
- State transition validation
- Proper cleanup on failure

### Phase 3: Testing and Validation (2 days)

#### 3.1 Unit Tests

1. **Test Retry Mechanism**
   - Test successful execution on first attempt
   - Test retry on transient failures
   - Test failure after max retries

2. **Test State Validation**
   - Test valid state transitions
   - Test invalid state transitions
   - Test required field validation

3. **Test Workflow Execution**
   - Test successful workflow completion
   - Test workflow failure and recovery
   - Test step timeouts and retries

#### 3.2 Integration Tests

1. **End-to-End Workflow**
   - Test complete workflow with mock data
   - Verify state persistence
   - Validate error recovery

2. **Performance Testing**
   - Measure step execution times
   - Test under load
   - Monitor resource usage

## Monitoring and Metrics

1. **Logging**
   - Structured logging for all workflow steps
   - Correlation IDs for request tracing
   - Error tracking integration

2. **Metrics**
   - Step execution times
   - Success/failure rates
   - Retry counts

## Rollout Plan

1. **Development**
   - Implement core enhancements
   - Add unit tests
   - Code review

2. **Staging**
   - Deploy to staging environment
   - Run integration tests
   - Monitor performance

3. **Production**
   - Gradual rollout
   - Monitor closely
   - Gather feedback

## Future Improvements

1. **Advanced Recovery**
   - Manual intervention points
   - Partial workflow restart
   - Step timeouts

2. **Enhanced Observability**
   - Real-time monitoring
   - Alerting
   - Tracing

3. **Performance Optimizations**
   - Parallel step execution
   - Caching
   - Batch processing

## Implementation Roadmap

### Day 1-2: Core Workflow Infrastructure
- [ ] Implement retry mechanism for transient failures
- [ ] Enhance error handling with explicit error types and logging
- [ ] Introduce state validation for workflow transitions

### Day 3-4: State Management and Observability
- [ ] Implement recovery mechanism for failed steps
- [ ] Enhance logging for workflow progress and step execution times
- [ ] Introduce metrics for step execution times and success/failure rates

### Day 5: Testing and Validation
- [ ] Write unit tests for error handling and state management
- [ ] Perform integration testing for workflow steps
- [ ] Validate metrics and logging for workflow execution
3. **Validation**
   - Unit tests for all components
   - Integration tests for workflow steps
   - Load testing for state management

## Rollout Strategy

1. **Phase 1**: Deploy to staging environment
2. **Phase 2**: Enable for a subset of workflows
3. **Phase 3**: Full production rollout

## Success Criteria

1. **Reliability**
   - 99.9% workflow completion rate
   - No data loss during failures
   - Consistent state across retries

2. **Performance**
   - Sub-100ms state updates
   - Linear scaling with workflow count
   - Minimal overhead from context management

3. **Observability**
   - Complete audit trail of workflow execution
   - Real-time status updates
   - Actionable error messages
