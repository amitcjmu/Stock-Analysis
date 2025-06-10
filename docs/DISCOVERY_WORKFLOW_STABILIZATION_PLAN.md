...
                    raise WorkflowStateError("Invalid state transition")
                    
                # Save to database within transaction
                await self._save_to_db(workflow_id, new_state)
                await transaction.commit()
                
                logger.info(f"Updated workflow {workflow_id} state")
                return new_state
                
            except Exception as e:
                await transaction.rollback()
                logger.error(f"Failed to update workflow state: {e}")
                raise WorkflowStateError(f"Failed to update workflow state: {str(e)}")
                
    async def _load_from_db(self, workflow_id: str) -> Dict:
        """Load workflow state from database."""
        # Implementation depends on your database schema
        # Example using SQLAlchemy:
        # result = await self.db.execute(
        #     select(WorkflowState).where(WorkflowState.id == workflow_id)
        # )
        # return result.scalar_one_or_none()
        pass
        
    async def _save_to_db(self, workflow_id: str, state: Dict):
        """Save workflow state to database."""
        # Implementation depends on your database schema
        # Example using SQLAlchemy:
        # stmt = (
        #     insert(WorkflowState)
        #     .values(id=workflow_id, state=state)
        #     .on_conflict_do_update(
        #         index_elements=['id'],
        #         set_=dict(state=state, updated_at=datetime.utcnow())
        #     )
        # )
        # await self.db.execute(stmt)
        pass
        
    def _validate_state_structure(self, state: Dict):
        """Validate the structure of the workflow state."""
        required_fields = ['status', 'created_at', 'updated_at']
        for field in required_fields:
            if field not in state:
                raise WorkflowStateError(f"Missing required field: {field}")
                
    def _validate_state_transition(self, current: Dict, new: Dict) -> bool:
        """Validate if the state transition is allowed."""
        # Implement your state transition validation logic here
        # Example:
        # valid_transitions = {
        #     'pending': ['running', 'failed'],
        #     'running': ['completed', 'failed'],
        #     'failed': ['retrying', 'cancelled'],
        #     'retrying': ['running', 'failed']
        # }
        # return new['status'] in valid_transitions.get(current['status'], [])
        return True
```

#### 1.2 Implement Workflow Step Retry with Database Tracking
```python
# backend/app/services/workflow/step_runner.py
class WorkflowStepRunner:
    """Handles execution of individual workflow steps with retry and database tracking."""
    
    def __init__(self, db_session, max_retries=3, backoff_factor=1.5):
        self.db = db_session
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def run_step(self, step_func, step_name: str, workflow_id: str, *args, **kwargs):
        """Run a workflow step with retry logic and database tracking."""
        last_error = None
        
        async with self.db.begin() as transaction:
            try:
                # Log step start
                await self._log_step_start(workflow_id, step_name)
                
                for attempt in range(self.max_retries + 1):
                    try:
                        result = await step_func(*args, **kwargs)
                        # Log successful completion
                        await self._log_step_completion(workflow_id, step_name, True)
                        await transaction.commit()
                        return result
                        
                    except (TimeoutError, ConnectionError, DatabaseError) as e:
                        last_error = e
                        if attempt == self.max_retries:
                            break
                            
                        # Log retry attempt
                        await self._log_step_retry(
                            workflow_id, 
                            step_name, 
                            attempt + 1, 
                            str(e)
                        )
                        
                        # Exponential backoff
                        delay = (self.backoff_factor ** attempt) * 0.5
                        await asyncio.sleep(delay)
                        continue
                
                # If we get here, all retries failed
                await self._log_step_failure(workflow_id, step_name, str(last_error))
                raise WorkflowStepError(
                    f"Step '{step_name}' failed after {self.max_retries} attempts"
                ) from last_error
                
            except Exception as e:
                await transaction.rollback()
                await self._log_step_failure(workflow_id, step_name, str(e))
                raise
    
    async def _log_step_start(self, workflow_id: str, step_name: str):
        """Log the start of a workflow step."""
        # Implementation depends on your database schema
        pass
        
    async def _log_step_completion(self, workflow_id: str, step_name: str, success: bool):
        """Log the completion of a workflow step."""
        # Implementation depends on your database schema
        pass
        
    async def _log_step_retry(self, workflow_id: str, step_name: str, attempt: int, error: str):
        """Log a retry attempt for a workflow step."""
        # Implementation depends on your database schema
        pass
        
    async def _log_step_failure(self, workflow_id: str, step_name: str, error: str):
        """Log a workflow step failure."""
        # Implementation depends on your database schema
        pass
```

### Phase 2: Context Management (2 days)

#### 2.1 Context Validation Middleware
```python
# backend/app/middleware/context_middleware.py
class ContextValidationMiddleware:
    """Validates and enriches context for workflow requests."""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        request = Request(scope, receive)
        
        # Extract and validate context
        try:
            context = self._extract_context(request)
            await self._validate_context(context)
            
            # Add to request state
            scope["state"]["context"] = context
            
            return await self.app(scope, receive, send)
            
        except InvalidContextError as e:
            return JSONResponse(
                status_code=400,
                content={"error": str(e)}
            )
```

#### 2.2 Context-Aware Workflow Steps
```python
# backend/app/services/workflow/steps/base_step.py
class WorkflowStep:
    """Base class for workflow steps with context management."""
    
    def __init__(self, context: Dict, state_manager: DiscoveryStateManager):
        self.context = context
        self.state_manager = state_manager
        self.logger = logging.getLogger(f"workflow.step.{self.__class__.__name__}")
    
    async def execute(self) -> Dict:
        """Execute the workflow step with proper context handling."""
        try:
            self._validate_context()
            result = await self._execute()
            await self._update_workflow_state(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Step failed: {e}", exc_info=True)
            await self._handle_error(e)
            raise
```

### Phase 3: Error Handling and Recovery (2 days)

#### 3.1 Workflow Error Handler
```python
# backend/app/services/workflow/error_handler.py
class WorkflowErrorHandler:
    """Handles errors during workflow execution."""
    
    def __init__(self, state_manager: DiscoveryStateManager):
        self.state_manager = state_manager
    
    async def handle_error(self, workflow_id: str, step: str, error: Exception):
        """Handle workflow step error with recovery options."""
        error_info = self._extract_error_info(error)
        
        # Update workflow state with error
        await self.state_manager.update_workflow_state(
            workflow_id,
            {
                "status": "error",
                "current_step": step,
                "error": error_info,
                "can_retry": self._is_retryable(error)
            }
        )
        
        # Log error and trigger alerts if needed
        self._log_error(workflow_id, step, error_info)
        
        # Return recovery options
        return self._get_recovery_options(error)
```

#### 3.2 Workflow Recovery Service
```python
# backend/app/services/workflow/recovery_service.py
class WorkflowRecoveryService:
    """Manages workflow recovery from failures."""
    
    async def recover_workflow(self, workflow_id: str):
        """Attempt to recover a failed workflow."""
        state = await self.state_manager.get_workflow_state(workflow_id)
        
        if not state.get("can_retry"):
            raise WorkflowRecoveryError("Workflow cannot be automatically recovered")
            
        # Get the step that failed
        failed_step = state["current_step"]
        
        # Reset step state
        await self.state_manager.update_workflow_state(
            workflow_id,
            {
                "status": "running",
                "retry_count": state.get("retry_count", 0) + 1
            }
        )
        
        # Return the step to retry
        return {
            "step": failed_step,
            "context": state["context"]
        }
```

## Implementation Roadmap

### Day 1-2: Core Workflow Infrastructure
- [ ] Implement `DiscoveryStateManager`
- [ ] Set up Redis caching layer
- [ ] Create base workflow step classes

### Day 3-4: Context Management
- [ ] Implement context validation middleware
- [ ] Add context enrichment for workflow steps
- [ ] Set up context propagation

### Day 5: Error Handling
- [ ] Implement error handler
- [ ] Add recovery service
- [ ] Set up error tracking and alerts

## Monitoring and Validation

1. **Logging**
   - Structured logging for all workflow steps
   - Correlation IDs for request tracing
   - Error tracking integration

2. **Metrics**
   - Step execution times
   - Success/failure rates
   - Context validation failures

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
