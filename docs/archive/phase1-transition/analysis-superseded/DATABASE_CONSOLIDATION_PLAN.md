# Database Consolidation Plan
## Addressing Redundant Tables and Pattern Inconsistency

### Current State Analysis

#### Redundant Tables Identified:
1. **`workflow_states`** - Main CrewAI Flow state (Event Listener pattern)
2. **`workflow_progress`** - Asset-specific progress (custom pattern)  
3. **`import_processing_steps`** - Import step tracking (custom pattern)
4. **`crewai_flow_state_extensions`** - CrewAI analytics (Event Listener pattern)
5. **`data_import_sessions`** - Import sessions (custom pattern)

#### Pattern Analysis:
- **CrewAI Event Listener Pattern**: `workflow_states`, `crewai_flow_state_extensions`
- **Custom Patterns**: `workflow_progress`, `import_processing_steps`, `data_import_sessions`
- **Result**: Fragmented state management, duplicate data, inconsistent tracking

### Consolidation Strategy

#### Phase 1: Unified State Model
**Goal**: Single source of truth using CrewAI Event Listener pattern

**Primary Table**: `workflow_states` (enhanced)
- Becomes the single source of truth for ALL workflow tracking
- Enhanced with columns from other tables
- Follows CrewAI Event Listener documentation patterns

**Extension Table**: `crewai_flow_state_extensions` (enhanced)
- Stores CrewAI-specific analytics and performance data
- Links to `workflow_states` via foreign key
- Handles advanced CrewAI Flow features

#### Phase 2: Migration Plan

**Step 1: Enhance `workflow_states`**
```sql
-- Add missing columns from other tables
ALTER TABLE workflow_states ADD COLUMN IF NOT EXISTS asset_progress JSONB DEFAULT '{}';
ALTER TABLE workflow_states ADD COLUMN IF NOT EXISTS import_steps JSONB DEFAULT '[]';
ALTER TABLE workflow_states ADD COLUMN IF NOT EXISTS processing_metrics JSONB DEFAULT '{}';
ALTER TABLE workflow_states ADD COLUMN IF NOT EXISTS step_completion JSONB DEFAULT '{}';
```

**Step 2: Data Migration Script**
```python
async def migrate_fragmented_data():
    """Migrate data from redundant tables to unified workflow_states"""
    
    # Migrate workflow_progress data
    workflow_progress_data = await db.execute(
        select(WorkflowProgress).options(selectinload(WorkflowProgress.asset))
    )
    
    for progress in workflow_progress_data.scalars():
        # Update corresponding workflow_state with asset progress
        await db.execute(
            update(WorkflowState)
            .where(WorkflowState.session_id == progress.asset.session_id)
            .values(asset_progress=func.jsonb_set(
                WorkflowState.asset_progress,
                text(f"'{{{progress.asset.id}}}'"),
                {
                    "stage": progress.stage,
                    "status": progress.status,
                    "notes": progress.notes,
                    "started_at": progress.started_at.isoformat() if progress.started_at else None,
                    "completed_at": progress.completed_at.isoformat() if progress.completed_at else None
                }
            ))
        )
    
    # Migrate import_processing_steps data
    import_steps_data = await db.execute(
        select(ImportProcessingStep).options(selectinload(ImportProcessingStep.data_import))
    )
    
    for step in import_steps_data.scalars():
        # Update corresponding workflow_state with import step data
        await db.execute(
            update(WorkflowState)
            .where(WorkflowState.session_id == step.data_import.session_id)
            .values(import_steps=func.jsonb_insert(
                WorkflowState.import_steps,
                text("'$'"),
                {
                    "step_name": step.step_name,
                    "step_order": step.step_order,
                    "status": step.status,
                    "description": step.description,
                    "input_data": step.input_data,
                    "output_data": step.output_data,
                    "error_details": step.error_details,
                    "records_processed": step.records_processed,
                    "duration_seconds": step.duration_seconds,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None
                }
            ))
        )
```

**Step 3: Update Event Listener**
```python
# Update DiscoveryFlowEventListener to handle all tracking
class DiscoveryFlowEventListener(BaseEventListener):
    
    @crewai_event_bus.on(TaskCompletedEvent)
    def on_task_completed(source, event: TaskCompletedEvent):
        # Update unified workflow_states with task completion
        self._update_unified_state(
            flow_id=self._extract_flow_id(source, event),
            update_type="task_completion",
            data={
                "task": event.task.description,
                "agent": event.agent.role,
                "output": event.output,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @crewai_event_bus.on(CrewKickoffCompletedEvent)
    def on_crew_completed(source, event: CrewKickoffCompletedEvent):
        # Update unified workflow_states with crew completion
        self._update_unified_state(
            flow_id=self._extract_flow_id(source, event),
            update_type="crew_completion",
            data={
                "crew_name": event.crew_name,
                "output": event.output,
                "duration": event.duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

#### Phase 3: Service Layer Updates

**Unified State Service**
```python
class UnifiedWorkflowStateService:
    """Single service for all workflow state management"""
    
    async def update_asset_progress(self, session_id: str, asset_id: str, progress_data: Dict):
        """Update asset progress in unified workflow_states"""
        await self.db.execute(
            update(WorkflowState)
            .where(WorkflowState.session_id == session_id)
            .values(asset_progress=func.jsonb_set(
                WorkflowState.asset_progress,
                text(f"'{{{asset_id}}}'"),
                progress_data
            ))
        )
    
    async def add_processing_step(self, session_id: str, step_data: Dict):
        """Add processing step to unified workflow_states"""
        await self.db.execute(
            update(WorkflowState)
            .where(WorkflowState.session_id == session_id)
            .values(import_steps=func.jsonb_insert(
                WorkflowState.import_steps,
                text("'$'"),
                step_data
            ))
        )
    
    async def get_complete_workflow_state(self, session_id: str) -> Dict:
        """Get complete workflow state including all tracking data"""
        stmt = select(WorkflowState).options(
            selectinload(WorkflowState.crewai_extensions)
        ).where(WorkflowState.session_id == session_id)
        
        result = await self.db.execute(stmt)
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            return None
        
        return {
            "workflow_state": workflow.to_dict(),
            "asset_progress": workflow.asset_progress or {},
            "import_steps": workflow.import_steps or [],
            "processing_metrics": workflow.processing_metrics or {},
            "crewai_analytics": workflow.crewai_extensions.to_dict() if workflow.crewai_extensions else {}
        }
```

#### Phase 4: Cleanup Plan

**Step 1: Deprecate Redundant Tables**
```sql
-- After successful migration and validation
DROP TABLE IF EXISTS workflow_progress CASCADE;
DROP TABLE IF EXISTS import_processing_steps CASCADE;
-- Keep data_import_sessions for import history, but remove workflow tracking columns
```

**Step 2: Update Models**
```python
# Remove redundant models
# - WorkflowProgress (functionality moved to WorkflowState.asset_progress)
# - ImportProcessingStep (functionality moved to WorkflowState.import_steps)

# Update WorkflowState model with new columns
class WorkflowState(Base):
    # ... existing columns ...
    
    # Consolidated tracking data
    asset_progress = Column(JSONB, nullable=False, default={})
    import_steps = Column(JSONB, nullable=False, default=[])
    processing_metrics = Column(JSONB, nullable=False, default={})
    step_completion = Column(JSONB, nullable=False, default={})
```

### Benefits of Consolidation

#### 1. **Single Source of Truth**
- All workflow tracking in one place
- Consistent state management across the platform
- Eliminates data synchronization issues

#### 2. **CrewAI Event Listener Pattern**
- Follows official CrewAI documentation patterns
- Real-time state updates through event system
- Proper integration with CrewAI Flow lifecycle

#### 3. **Simplified Architecture**
- Reduced database complexity
- Easier maintenance and debugging
- Consistent API patterns

#### 4. **Performance Improvements**
- Fewer table joins required
- Reduced query complexity
- Better caching opportunities

### Implementation Timeline

**Week 1**: Database schema enhancement and migration scripts
**Week 2**: Event listener updates and service layer consolidation  
**Week 3**: Frontend updates to use unified state APIs
**Week 4**: Testing, validation, and redundant table cleanup

### Risk Mitigation

**Backup Strategy**: Full database backup before migration
**Rollback Plan**: Keep redundant tables until validation complete
**Validation**: Comprehensive testing of all workflow scenarios
**Monitoring**: Real-time monitoring during migration process 