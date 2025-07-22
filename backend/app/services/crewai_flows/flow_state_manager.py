"""
Flow State Manager - PostgreSQL-only implementation
Manages CrewAI flow state with PostgreSQL as single source of truth
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.flow_state_validator import FlowStateValidator

from .persistence.postgres_store import ConcurrentModificationError, PostgresFlowStateStore, StateValidationError
from .persistence.state_recovery import FlowStateRecovery, StateRecoveryError

logger = logging.getLogger(__name__)

class InvalidTransitionError(Exception):
    """Raised when an invalid phase transition is attempted"""
    pass

class FlowStateManager:
    """
    Manages CrewAI flow state with PostgreSQL as single source of truth
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()
        self.recovery = FlowStateRecovery(db, context)
    
    async def create_flow_state(
        self, 
        flow_id: str, 
        initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new flow state"""
        try:
            logger.info(f"🔄 Creating new flow state: {flow_id}")
            
            # Create initial state structure
            flow_state = {
                'flow_id': flow_id,
                'client_account_id': str(self.context.client_account_id),
                'engagement_id': str(self.context.engagement_id),
                'user_id': str(self.context.user_id),
                'current_phase': 'initialization',
                'status': 'running',
                'progress_percentage': 0.0,
                'phase_completion': {
                    'data_import': False,
                    'field_mapping': False,
                    'data_cleansing': False,
                    'asset_creation': False,
                    'asset_inventory': False,
                    'dependency_analysis': False,
                    'tech_debt_analysis': False
                },
                'crew_status': {},
                'raw_data': initial_data.get('raw_data', []),
                'metadata': initial_data.get('metadata', {}),
                'errors': [],
                'warnings': [],
                'agent_insights': [],
                'user_clarifications': [],
                'workflow_log': [],
                'agent_confidences': {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Validate initial state
            validation_result = self.validator.validate_complete_state(flow_state)
            if not validation_result['valid']:
                raise StateValidationError(f"Invalid initial state: {validation_result['errors']}")
            
            # Save to PostgreSQL
            await self.store.save_state(
                flow_id=flow_id,
                state=flow_state,
                phase='initialization'
            )
            
            # Create initial checkpoint
            checkpoint_id = await self.store.create_checkpoint(flow_id, 'initialization')
            
            logger.info(f"✅ Flow state created: {flow_id}")
            return {
                'flow_id': flow_id,
                'status': 'created',
                'checkpoint_id': checkpoint_id,
                'created_at': flow_state['created_at']
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create flow state for {flow_id}: {e}")
            raise
    
    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current flow state for agent analysis
        
        ADR-012: Uses child flow data for operational decisions, not master flow
        """
        try:
            # ADR-012: Get operational state from child flow repository
            logger.info(f"🔄 [ADR-012] Getting operational state from child flow: {flow_id}")
            
            # First, determine flow type to get appropriate child flow
            from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
            master_repo = CrewAIFlowStateExtensionsRepository(self.db, self.context.client_account_id, self.context.engagement_id, self.context.user_id)
            master_flow = await master_repo.get_by_flow_id(flow_id)
            
            if not master_flow:
                logger.warning(f"⚠️ Master flow not found: {flow_id}")
                return None
            
            # Get child flow based on type (assuming discovery for now)
            if master_flow.flow_type == "discovery":
                from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
                child_repo = DiscoveryFlowRepository(self.db, self.context.client_account_id, self.context.engagement_id, self.context.user_id)
                child_flow = await child_repo.get_by_flow_id(flow_id)
                
                if child_flow:
                    # Create UnifiedDiscoveryFlowState from child flow operational data
                    state = {
                        'flow_id': flow_id,
                        'client_account_id': str(self.context.client_account_id),
                        'engagement_id': str(self.context.engagement_id),
                        'user_id': str(self.context.user_id),
                        'current_phase': child_flow.current_phase,
                        'status': child_flow.status,  # ADR-012: Use child flow operational status
                        'progress_percentage': child_flow.progress_percentage,
                        'phase_completion': {
                            'data_import': child_flow.data_import_completed or False,
                            'field_mapping': child_flow.field_mapping_completed or False,
                            'data_cleansing': child_flow.data_cleansing_completed or False,
                            'asset_inventory': child_flow.asset_inventory_completed or False
                        },
                        'errors': child_flow.error_details or [],
                        'raw_data': child_flow.imported_data or [],
                        'field_mappings': child_flow.field_mappings or {},
                        'validation_results': child_flow.validation_results or {},
                        'created_at': child_flow.created_at.isoformat() if child_flow.created_at else None,
                        'updated_at': child_flow.updated_at.isoformat() if child_flow.updated_at else None
                    }
                    
                    logger.info(f"✅ [ADR-012] Operational state loaded from child flow: {flow_id}")
                    return state
                else:
                    logger.warning(f"⚠️ Child flow not found: {flow_id}")
                    return None
            else:
                # For non-discovery flows, fall back to master flow data (to be expanded)
                logger.warning(f"⚠️ [ADR-012] Non-discovery flow type not yet supported: {master_flow.flow_type}")
                # Fall back to original behavior for now
                state = await self.store.load_state(flow_id)
                if state:
                    return state
                else:
                    return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get flow state for {flow_id}: {e}")
            return None
    
    async def update_flow_state(
        self, 
        flow_id: str, 
        state_updates: Dict[str, Any],
        version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update flow state with validation"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")
            
            # Apply updates
            updated_state = current_state.copy()
            updated_state.update(state_updates)
            updated_state['updated_at'] = datetime.utcnow().isoformat()
            
            # Validate updated state
            validation_result = self.validator.validate_complete_state(updated_state)
            if not validation_result['valid']:
                raise StateValidationError(f"Invalid state update: {validation_result['errors']}")
            
            # Save updated state
            await self.store.save_state(
                flow_id=flow_id,
                state=updated_state,
                phase=updated_state.get('current_phase', 'unknown'),
                version=version
            )
            
            logger.info(f"✅ Flow state updated: {flow_id}")
            return {
                'flow_id': flow_id,
                'status': 'updated',
                'updated_at': updated_state['updated_at']
            }
            
        except ConcurrentModificationError as e:
            logger.warning(f"⚠️ Concurrent modification detected for {flow_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update flow state for {flow_id}: {e}")
            raise
    
    async def transition_phase(
        self, 
        flow_id: str, 
        new_phase: str,
        phase_data: Optional[Dict[str, Any]] = None,
        force_transition: bool = False
    ) -> Dict[str, Any]:
        """Handle phase transitions with validation"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")
            
            current_phase = current_state.get('current_phase', 'unknown')
            
            # Add debug logging for phase transitions
            logger.info(f"🔄 Phase transition requested: {flow_id}")
            logger.info(f"  - current_phase: {current_phase}")
            logger.info(f"  - new_phase: {new_phase}")
            logger.info(f"  - force_transition: {force_transition}")
            
            # Validate phase transition unless forced (for resumption scenarios)
            if not force_transition and not self.validator.validate_phase_transition(current_state, new_phase):
                logger.warning(f"❌ Phase transition validation failed: {current_phase} -> {new_phase}")
                raise InvalidTransitionError(f"Invalid transition from {current_phase} to {new_phase}")
            
            if force_transition:
                logger.info(f"⚡ Forced phase transition allowed: {current_phase} -> {new_phase}")
            
            # Create checkpoint before transition
            checkpoint_id = await self.store.create_checkpoint(flow_id, current_phase)
            
            # Update state for new phase
            current_state['current_phase'] = new_phase
            current_state['updated_at'] = datetime.utcnow().isoformat()
            
            # Add phase-specific data if provided
            if phase_data:
                phase_data_key = f"{new_phase}_data"
                current_state[phase_data_key] = phase_data
            
            # Update progress based on phase
            progress_mapping = {
                'initialization': 0.0,
                'data_import': 10.0,
                'field_mapping': 25.0,
                'data_cleansing': 40.0,
                'asset_creation': 55.0,
                'asset_inventory': 70.0,
                'dependency_analysis': 85.0,
                'tech_debt_analysis': 95.0,
                'completed': 100.0
            }
            current_state['progress_percentage'] = progress_mapping.get(new_phase, current_state.get('progress_percentage', 0.0))
            
            # Save updated state
            await self.store.save_state(
                flow_id=flow_id,
                state=current_state,
                phase=new_phase
            )
            
            logger.info(f"✅ Phase transition completed: {flow_id} -> {new_phase}")
            return {
                'flow_id': flow_id,
                'previous_phase': current_state.get('current_phase'),
                'new_phase': new_phase,
                'checkpoint_id': checkpoint_id,
                'progress_percentage': current_state['progress_percentage'],
                'transitioned_at': current_state['updated_at']
            }
            
        except Exception as e:
            logger.error(f"❌ Phase transition failed for {flow_id}: {e}")
            raise
    
    async def resume_flow_state(
        self, 
        flow_id: str, 
        target_phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resume flow state during flow resumption - uses force transition to handle edge cases
        """
        try:
            logger.info(f"🔄 Resuming flow state: {flow_id}")
            
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found for resume: {flow_id}")
            
            current_phase = current_state.get('current_phase', 'initialization')
            
            # If no target phase specified, stay in current phase
            if not target_phase:
                target_phase = current_phase
            
            # Update flow status to running
            current_state['status'] = 'running'
            current_state['updated_at'] = datetime.utcnow().isoformat()
            
            # If we need to transition phases during resume, use force transition
            if target_phase != current_phase:
                logger.info(f"🔄 Resume requires phase transition: {current_phase} -> {target_phase}")
                return await self.transition_phase(
                    flow_id=flow_id,
                    new_phase=target_phase,
                    phase_data={'resumed_from': current_phase, 'resume_reason': 'flow_resumption'},
                    force_transition=True  # Allow transition during resume
                )
            else:
                # Save current state with updated status
                await self.store.save_state(
                    flow_id=flow_id,
                    state=current_state,
                    phase=current_phase
                )
                
                logger.info(f"✅ Flow state resumed in current phase: {current_phase}")
                return {
                    'flow_id': flow_id,
                    'current_phase': current_phase,
                    'status': 'running',
                    'resumed_at': current_state['updated_at']
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to resume flow state for {flow_id}: {e}")
            raise
    
    async def complete_phase(
        self, 
        flow_id: str, 
        phase: str, 
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mark a phase as completed with results"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")
            
            # Update phase completion
            if 'phase_completion' not in current_state:
                current_state['phase_completion'] = {}
            
            current_state['phase_completion'][phase] = True
            current_state['updated_at'] = datetime.utcnow().isoformat()
            
            # Store phase results
            results_key = f"{phase}_results"
            current_state[results_key] = results
            
            # Add to workflow log
            if 'workflow_log' not in current_state:
                current_state['workflow_log'] = []
            
            current_state['workflow_log'].append({
                'timestamp': current_state['updated_at'],
                'event': 'phase_completed',
                'phase': phase,
                'results_summary': {
                    'status': results.get('status'),
                    'records_processed': results.get('records_processed', 0),
                    'errors': len(results.get('errors', [])),
                    'warnings': len(results.get('warnings', []))
                }
            })
            
            # Create checkpoint after completion
            checkpoint_id = await self.store.create_checkpoint(flow_id, phase)
            
            # Save updated state
            await self.store.save_state(
                flow_id=flow_id,
                state=current_state,
                phase=phase
            )
            
            logger.info(f"✅ Phase completed: {flow_id} -> {phase}")
            return {
                'flow_id': flow_id,
                'phase': phase,
                'checkpoint_id': checkpoint_id,
                'completed_at': current_state['updated_at'],
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to complete phase {phase} for {flow_id}: {e}")
            raise
    
    async def handle_flow_error(
        self, 
        flow_id: str, 
        error: str, 
        phase: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle flow errors with automatic recovery attempts"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")
            
            # Add error to state
            if 'errors' not in current_state:
                current_state['errors'] = []
            
            error_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'phase': phase,
                'error': error,
                'details': details or {}
            }
            current_state['errors'].append(error_entry)
            
            # Update status
            current_state['status'] = 'failed'
            current_state['updated_at'] = datetime.utcnow().isoformat()
            
            # Save error state
            await self.store.save_state(
                flow_id=flow_id,
                state=current_state,
                phase=phase
            )
            
            # Attempt automatic recovery
            try:
                recovery_result = await self.recovery.recover_failed_flow(flow_id)
                logger.info(f"✅ Automatic recovery attempted for {flow_id}: {recovery_result['status']}")
                
                return {
                    'flow_id': flow_id,
                    'error_logged': True,
                    'recovery_attempted': True,
                    'recovery_result': recovery_result,
                    'handled_at': current_state['updated_at']
                }
                
            except StateRecoveryError as recovery_error:
                logger.error(f"❌ Automatic recovery failed for {flow_id}: {recovery_error}")
                
                return {
                    'flow_id': flow_id,
                    'error_logged': True,
                    'recovery_attempted': False,
                    'recovery_error': str(recovery_error),
                    'handled_at': current_state['updated_at']
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to handle error for {flow_id}: {e}")
            raise
    
    async def cleanup_flow_state(self, flow_id: str, archive: bool = True) -> Dict[str, Any]:
        """Clean up flow state with optional archiving"""
        try:
            if archive:
                # Create final checkpoint before cleanup
                await self.store.create_checkpoint(flow_id, 'cleanup')
            
            # Clean up old versions (keep last 2)
            cleaned_versions = await self.store.cleanup_old_versions(flow_id, keep_versions=2)
            
            logger.info(f"✅ Flow state cleaned up: {flow_id}, removed {cleaned_versions} old versions")
            return {
                'flow_id': flow_id,
                'archived': archive,
                'versions_cleaned': cleaned_versions,
                'cleaned_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup flow state for {flow_id}: {e}")
            raise
    
    async def get_flow_history(self, flow_id: str) -> Dict[str, Any]:
        """Get complete history for a flow"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            
            # Get version history
            versions = await self.store.get_flow_versions(flow_id)
            
            # Get recovery status
            recovery_status = await self.recovery.get_recovery_status(flow_id)
            
            return {
                'flow_id': flow_id,
                'current_state': current_state,
                'version_history': versions,
                'recovery_status': recovery_status,
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get flow history for {flow_id}: {e}")
            return {
                'flow_id': flow_id,
                'error': str(e),
                'retrieved_at': datetime.utcnow().isoformat()
            }


# Utility functions for flow state management

async def create_flow_manager(context: RequestContext) -> FlowStateManager:
    """Create a flow state manager with database session"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        return FlowStateManager(db, context)


async def get_flow_summary(flow_id: str, context: RequestContext) -> Dict[str, Any]:
    """Get a summary of flow state"""
    manager = await create_flow_manager(context)
    state = await manager.get_flow_state(flow_id)
    
    if not state:
        return {'flow_id': flow_id, 'status': 'not_found'}
    
    return {
        'flow_id': flow_id,
        'current_phase': state.get('current_phase'),
        'status': state.get('status'),
        'progress_percentage': state.get('progress_percentage'),
        'errors_count': len(state.get('errors', [])),
        'warnings_count': len(state.get('warnings', [])),
        'last_updated': state.get('updated_at'),
        'phase_completion': state.get('phase_completion', {})
    }