# Assessment Flow - API & Integration Tasks

## Overview
This document tracks all API endpoints, service integrations, and external system connections for the Assessment Flow implementation.

## Key Implementation Context
- **API v1 endpoints** to align with current platform reality (v3 adoption incomplete)
- **Multi-tenant headers** for proper client account and engagement scoping
- **HTTP/2 events** for real-time agent completion notifications
- **Flow state synchronization** to prevent context header mismatches
- **Pause/resume API patterns** for user interaction at each node

---

## 🔌 API Development Tasks

### API-001: Create Assessment Flow Core API Endpoints
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 14 hours  
**Dependencies**: Backend Core (BE-001), Database Foundation (DB-001)  
**Sprint**: API Week 5-6  

**Description**: Implement core FastAPI endpoints for assessment flow management with multi-tenant support and state synchronization

**Location**: `backend/app/api/v1/assessment_flow.py`

**Technical Requirements**:
- FastAPI endpoints with proper dependency injection
- Multi-tenant security with client_account_id validation
- Flow state management with pause/resume capabilities
- Integration with UnifiedAssessmentFlow execution
- Error handling and response standardization

**API Endpoint Implementation**:
```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.security import get_current_user, verify_client_access
from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase
from app.services.crewai_flows.unified_assessment_flow import UnifiedAssessmentFlow
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import (
    AssessmentFlowCreateRequest,
    AssessmentFlowResponse,
    AssessmentFlowStatusResponse,
    ResumeFlowRequest
)

router = APIRouter(prefix="/api/v1/assessment-flow", tags=["assessment-flow"])

@router.post("/initialize", response_model=AssessmentFlowResponse)
async def initialize_assessment_flow(
    request: AssessmentFlowCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    client_account_id: int = Depends(verify_client_access),
    engagement_id: int = Header(..., alias="X-Engagement-ID")
):
    """
    Initialize new assessment flow with selected applications
    """
    try:
        logger.info(f"Initializing assessment flow for {len(request.selected_application_ids)} applications")
        
        # Verify user has access to engagement
        await verify_engagement_access(db, engagement_id, client_account_id)
        
        # Verify applications are ready for assessment
        await verify_applications_ready_for_assessment(
            db, request.selected_application_ids, client_account_id
        )
        
        # Create assessment flow repository
        repository = AssessmentFlowRepository(db, client_account_id)
        
        # Initialize flow
        flow_id = await repository.create_assessment_flow(
            engagement_id=engagement_id,
            selected_application_ids=request.selected_application_ids,
            created_by=current_user.email
        )
        
        # Create flow context
        flow_context = FlowContext(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=current_user.id,
            db_session=db
        )
        
        # Initialize UnifiedAssessmentFlow
        assessment_flow = UnifiedAssessmentFlow(
            crewai_service=get_crewai_service(),
            context=flow_context
        )
        
        # Start flow execution in background
        background_tasks.add_task(
            execute_assessment_flow_initialization,
            assessment_flow,
            flow_context
        )
        
        return AssessmentFlowResponse(
            flow_id=flow_id,
            status="initialized",
            current_phase="architecture_minimums",
            next_phase="architecture_minimums",
            selected_applications=len(request.selected_application_ids),
            message="Assessment flow initialized successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Assessment flow initialization validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Assessment flow initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Assessment flow initialization failed")

@router.get("/{flow_id}/status", response_model=AssessmentFlowStatusResponse)
async def get_assessment_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    client_account_id: int = Depends(verify_client_access)
):
    """
    Get current status and progress of assessment flow
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")
        
        # Get phase-specific data based on current phase
        phase_data = await get_phase_specific_data(repository, flow_id, flow_state.current_phase)
        
        return AssessmentFlowStatusResponse(
            flow_id=flow_id,
            status=flow_state.status,
            progress=flow_state.progress,
            current_phase=flow_state.current_phase.value,
            next_phase=flow_state.next_phase.value if flow_state.next_phase else None,
            pause_points=flow_state.pause_points,
            user_inputs_captured=bool(flow_state.user_inputs),
            phase_results=flow_state.phase_results,
            apps_ready_for_planning=flow_state.apps_ready_for_planning,
            last_user_interaction=flow_state.last_user_interaction,
            phase_data=phase_data,
            created_at=flow_state.created_at,
            updated_at=flow_state.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment flow status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flow status")

@router.post("/{flow_id}/resume", response_model=AssessmentFlowResponse)
async def resume_assessment_flow(
    flow_id: str,
    request: ResumeFlowRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    client_account_id: int = Depends(verify_client_access)
):
    """
    Resume assessment flow from current phase with user input
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")
        
        if flow_state.status != "paused_for_user_input":
            raise HTTPException(status_code=400, detail="Flow is not in paused state")
        
        # Validate user input for current phase
        await validate_phase_user_input(flow_state.current_phase, request.user_input)
        
        # Create flow context
        flow_context = FlowContext(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=flow_state.engagement_id,
            user_id=current_user.id,
            db_session=db
        )
        
        # Create assessment flow instance
        assessment_flow = UnifiedAssessmentFlow(
            crewai_service=get_crewai_service(),
            context=flow_context
        )
        
        # Resume flow execution in background
        background_tasks.add_task(
            resume_assessment_flow_execution,
            assessment_flow,
            flow_state.current_phase,
            request.user_input
        )
        
        # Update flow status to processing
        await repository.update_flow_phase(
            flow_id,
            flow_state.current_phase.value,
            flow_state.next_phase.value if flow_state.next_phase else None,
            flow_state.progress
        )
        
        return AssessmentFlowResponse(
            flow_id=flow_id,
            status="processing",
            current_phase=flow_state.current_phase.value,
            next_phase=flow_state.next_phase.value if flow_state.next_phase else None,
            message="Assessment flow resumed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume assessment flow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resume assessment flow")

@router.put("/{flow_id}/navigate-to-phase/{phase}")
async def navigate_to_assessment_phase(
    flow_id: str,
    phase: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    client_account_id: int = Depends(verify_client_access)
):
    """
    Navigate to specific phase in assessment flow (for user going back)
    """
    try:
        # Validate phase
        try:
            target_phase = AssessmentPhase(phase)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}")
        
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")
        
        # Determine next phase based on navigation
        next_phase = get_next_phase_for_navigation(target_phase)
        
        # Update flow phase
        await repository.update_flow_phase(
            flow_id,
            target_phase.value,
            next_phase.value if next_phase else None,
            get_progress_for_phase(target_phase)
        )
        
        return {"message": f"Navigated to phase {phase}", "next_phase": next_phase.value if next_phase else None}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to navigate to phase: {str(e)}")
        raise HTTPException(status_code=500, detail="Phase navigation failed")

# Background task functions
async def execute_assessment_flow_initialization(
    assessment_flow: UnifiedAssessmentFlow,
    flow_context: FlowContext
):
    """Execute assessment flow initialization in background"""
    try:
        await assessment_flow.initialize_assessment()
        logger.info(f"Assessment flow {flow_context.flow_id} initialized successfully")
    except Exception as e:
        logger.error(f"Assessment flow initialization failed: {str(e)}")
        # Update flow status to error state
        await update_flow_error_state(flow_context.flow_id, str(e))

async def resume_assessment_flow_execution(
    assessment_flow: UnifiedAssessmentFlow,
    phase: AssessmentPhase,
    user_input: Dict[str, Any]
):
    """Resume assessment flow execution from specific phase"""
    try:
        await assessment_flow.resume_from_phase(phase, user_input)
        logger.info(f"Assessment flow resumed from phase {phase.value}")
    except Exception as e:
        logger.error(f"Assessment flow resume failed: {str(e)}")
        await update_flow_error_state(assessment_flow.context.flow_id, str(e))

# Helper functions
async def verify_applications_ready_for_assessment(
    db: AsyncSession,
    application_ids: List[str], 
    client_account_id: int
):
    """Verify all applications are ready for assessment"""
    # Implementation to check application readiness status
    pass

async def get_phase_specific_data(
    repository: AssessmentFlowRepository,
    flow_id: str,
    phase: AssessmentPhase
) -> Dict[str, Any]:
    """Get phase-specific data for status response"""
    # Implementation to return relevant data for each phase
    pass

async def validate_phase_user_input(phase: AssessmentPhase, user_input: Dict[str, Any]):
    """Validate user input for specific phase"""
    # Implementation for phase-specific input validation
    pass

def get_next_phase_for_navigation(current_phase: AssessmentPhase) -> Optional[AssessmentPhase]:
    """Determine next phase based on navigation"""
    phase_sequence = [
        AssessmentPhase.ARCHITECTURE_MINIMUMS,
        AssessmentPhase.TECH_DEBT_ANALYSIS,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES,
        AssessmentPhase.APP_ON_PAGE_GENERATION,
        AssessmentPhase.FINALIZATION
    ]
    
    try:
        current_index = phase_sequence.index(current_phase)
        if current_index < len(phase_sequence) - 1:
            return phase_sequence[current_index + 1]
    except ValueError:
        pass
    
    return None

def get_progress_for_phase(phase: AssessmentPhase) -> int:
    """Get progress percentage for phase"""
    progress_map = {
        AssessmentPhase.INITIALIZATION: 10,
        AssessmentPhase.ARCHITECTURE_MINIMUMS: 20,
        AssessmentPhase.TECH_DEBT_ANALYSIS: 50,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES: 75,
        AssessmentPhase.APP_ON_PAGE_GENERATION: 90,
        AssessmentPhase.FINALIZATION: 100
    }
    
    return progress_map.get(phase, 0)

async def update_flow_error_state(flow_id: str, error_message: str):
    """Update flow to error state"""
    # Implementation to update flow status to error
    pass
```

**Pydantic Schemas**:
```python
# In app/schemas/assessment_flow.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.assessment_flow import AssessmentPhase

class AssessmentFlowCreateRequest(BaseModel):
    selected_application_ids: List[str] = Field(..., min_items=1, max_items=100)

class AssessmentFlowResponse(BaseModel):
    flow_id: str
    status: str
    current_phase: str
    next_phase: Optional[str] = None
    selected_applications: Optional[int] = None
    message: str

class AssessmentFlowStatusResponse(BaseModel):
    flow_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    current_phase: str
    next_phase: Optional[str] = None
    pause_points: List[str] = []
    user_inputs_captured: bool
    phase_results: Dict[str, Any] = {}
    apps_ready_for_planning: List[str] = []
    last_user_interaction: Optional[datetime] = None
    phase_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class ResumeFlowRequest(BaseModel):
    user_input: Dict[str, Any] = Field(..., description="User input for current phase")
    save_progress: bool = Field(default=True, description="Whether to save progress")
```

**Acceptance Criteria**:
- [ ] Core CRUD endpoints for assessment flow management
- [ ] Multi-tenant security with proper access controls
- [ ] Pause/resume functionality with state persistence
- [ ] Background task execution for long-running flows
- [ ] Phase navigation support for user interactions
- [ ] Comprehensive error handling and status reporting
- [ ] Integration with UnifiedAssessmentFlow execution
- [ ] Proper request/response schema validation

---

### API-002: Create Architecture Standards API Endpoints
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 10 hours  
**Dependencies**: API-001, Backend Core (BE-001)  
**Sprint**: API Week 5-6  

**Description**: Implement API endpoints for managing engagement-level architecture standards and application-specific overrides

**Location**: `backend/app/api/v1/architecture_standards.py`

**Technical Requirements**:
- CRUD operations for engagement architecture standards
- Application-specific override management
- RBAC-based access control for standards modification
- Integration with assessment flow architecture capture phase
- Template and seed data management

**API Implementation**:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.architecture_standards import (
    ArchitectureStandardCreate,
    ArchitectureStandardResponse,
    ArchitectureStandardUpdate,
    ApplicationOverrideCreate,
    ApplicationOverrideResponse
)

router = APIRouter(prefix="/api/v1/assessment-flow", tags=["architecture-standards"])

@router.get("/{flow_id}/architecture-minimums")
async def get_architecture_standards(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    client_account_id: int = Depends(verify_client_access)
):
    """
    Get architecture standards for assessment flow
    """
    try:
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")
        
        # Get engagement standards
        engagement_standards = await repository.get_engagement_standards(flow_state.engagement_id)
        
        # Get application overrides
        app_overrides = await repository.get_application_overrides(flow_id)
        
        return {
            "engagement_standards": engagement_standards,
            "application_overrides": app_overrides,
            "templates_available": await get_available_templates()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get architecture standards: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve architecture standards")

@router.put("/{flow_id}/architecture-minimums")
async def update_architecture_standards(
    flow_id: str,
    request: ArchitectureStandardsUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    client_account_id: int = Depends(verify_client_access)
):
    """
    Update architecture standards and application overrides
    """
    try:
        # Verify user permissions for standards modification
        await verify_standards_modification_permission(current_user, client_account_id)
        
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(flow_id)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")
        
        # Update engagement standards
        if request.engagement_standards:
            await repository.save_architecture_standards(
                flow_state.engagement_id,
                request.engagement_standards
            )
        
        # Update application overrides
        if request.application_overrides:
            await repository.save_application_overrides(
                flow_id,
                request.application_overrides
            )
        
        # Mark architecture as captured
        await repository.update_architecture_captured_status(flow_id, True)
        
        return {"message": "Architecture standards updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update architecture standards: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update architecture standards")

@router.get("/templates/{domain}")
async def get_architecture_templates(
    domain: str,
    technology_focus: List[str] = Query(default=[]),
    current_user=Depends(get_current_user)
):
    """
    Get architecture standards templates for specific domain
    """
    try:
        from app.core.seed_data.assessment_standards import get_domain_templates
        
        templates = await get_domain_templates(domain, technology_focus)
        
        return {
            "domain": domain,
            "templates": templates,
            "customizable": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get architecture templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")

# Additional endpoints for standards management...
```

**Acceptance Criteria**:
- [ ] CRUD operations for architecture standards management
- [ ] Application override handling with RBAC controls
- [ ] Template and seed data integration
- [ ] Integration with assessment flow capture phase
- [ ] Proper validation and error handling

---

### API-003: Create Component and Tech Debt API Endpoints
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 12 hours  
**Dependencies**: API-001, Backend Core (BE-001)  
**Sprint**: API Week 5-6  

**Description**: Implement API endpoints for component identification, tech debt analysis, and user interaction during analysis phase

**Location**: `backend/app/api/v1/component_analysis.py`

**Technical Requirements**:
- Component CRUD operations with flexible structure support
- Tech debt analysis viewing and modification capabilities
- Integration with Component Analysis Crew results
- User feedback and override mechanisms
- Real-time updates during crew execution

**API Implementation Summary**:
```python
router = APIRouter(prefix="/api/v1/assessment-flow", tags=["component-analysis"])

@router.get("/{flow_id}/components")
async def get_application_components(flow_id: str, app_id: Optional[str] = None):
    """Get identified components for all or specific application"""
    
@router.put("/{flow_id}/components/{app_id}")
async def update_application_components(flow_id: str, app_id: str, components: List[ComponentUpdate]):
    """Update component identification for application"""
    
@router.get("/{flow_id}/tech-debt")
async def get_tech_debt_analysis(flow_id: str, app_id: Optional[str] = None):
    """Get technical debt analysis for applications"""
    
@router.put("/{flow_id}/tech-debt/{app_id}")
async def update_tech_debt_analysis(flow_id: str, app_id: str, updates: TechDebtUpdates):
    """Update tech debt analysis with user modifications"""
```

**Acceptance Criteria**:
- [ ] Component CRUD with flexible structure support
- [ ] Tech debt analysis viewing and modification
- [ ] User feedback integration
- [ ] Real-time crew execution updates

---

### API-004: Create 6R Decision and App-on-Page API Endpoints
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 14 hours  
**Dependencies**: API-001, Backend Core (BE-001)  
**Sprint**: API Week 6  

**Description**: Implement API endpoints for 6R decision management, app-on-page generation, and finalization processes

**Location**: `backend/app/api/v1/sixr_decisions.py`

**Technical Requirements**:
- 6R decision CRUD operations with component-level granularity
- App-on-page data generation and customization
- Assessment finalization with readiness validation
- Integration with Planning Flow handoff
- Comprehensive reporting and summary generation

**API Implementation Summary**:
```python
router = APIRouter(prefix="/api/v1/assessment-flow", tags=["sixr-decisions"])

@router.get("/{flow_id}/sixr-decisions")
async def get_sixr_decisions(flow_id: str):
    """Get 6R decisions for all applications in flow"""
    
@router.put("/{flow_id}/sixr-decisions/{app_id}")
async def update_sixr_decision(flow_id: str, app_id: str, decision: SixRDecisionUpdate):
    """Update 6R decision for application with user modifications"""
    
@router.get("/{flow_id}/app-on-page/{app_id}")
async def get_app_on_page(flow_id: str, app_id: str):
    """Get comprehensive app-on-page view"""
    
@router.post("/{flow_id}/finalize")
async def finalize_assessment(flow_id: str, finalization: AssessmentFinalization):
    """Finalize assessment and mark apps ready for planning"""
    
@router.get("/{flow_id}/report")
async def get_assessment_report(flow_id: str):
    """Get comprehensive assessment report"""
```

**Acceptance Criteria**:
- [ ] 6R decision management with component granularity
- [ ] App-on-page generation and customization
- [ ] Assessment finalization with validation
- [ ] Planning Flow integration and handoff
- [ ] Comprehensive reporting capabilities

---

## 🔗 Integration Tasks

### INT-001: Implement Real-time Agent Updates with HTTP/2 Events
**Status**: 🔴 Not Started  
**Priority**: P2 - Medium  
**Effort**: 8 hours  
**Dependencies**: API-001  
**Sprint**: API Week 6  

**Description**: Implement HTTP/2 Server-Sent Events for real-time updates during agent execution

**Location**: `backend/app/api/v1/assessment_events.py`

**Technical Requirements**:
- Server-Sent Events (SSE) endpoint for real-time updates
- Agent progress tracking and status broadcasting
- Client connection management with multi-tenant security
- Integration with CrewAI execution monitoring
- Graceful handling of connection failures

**Implementation Summary**:
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/v1/assessment-flow", tags=["events"])

@router.get("/{flow_id}/events")
async def stream_assessment_events(flow_id: str):
    """Stream real-time assessment flow events"""
    
    async def event_generator():
        # Implementation for SSE event streaming
        while True:
            event_data = await get_flow_events(flow_id)
            if event_data:
                yield event_data
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_generator())
```

**Acceptance Criteria**:
- [ ] SSE endpoint for real-time updates
- [ ] Agent progress tracking and broadcasting
- [ ] Multi-tenant connection security
- [ ] Integration with crew execution monitoring

---

### INT-002: Create Discovery Flow Integration Points
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 6 hours  
**Dependencies**: API-001  
**Sprint**: API Week 6  

**Description**: Implement integration points with Discovery Flow for application metadata and readiness management

**Location**: `backend/app/services/integrations/discovery_integration.py`

**Technical Requirements**:
- Application metadata retrieval from Discovery Flow results
- Readiness status management and validation
- Cross-flow data consistency and synchronization
- Integration with existing Discovery Flow APIs
- Error handling for missing or incomplete data

**Integration Implementation**:
```python
class DiscoveryFlowIntegration:
    """Integration service for Discovery Flow data access"""
    
    async def get_applications_ready_for_assessment(
        self, 
        client_account_id: int,
        engagement_id: int
    ) -> List[Dict[str, Any]]:
        """Get applications marked ready for assessment"""
        
    async def get_application_metadata(
        self,
        application_id: str,
        client_account_id: int
    ) -> Dict[str, Any]:
        """Get complete application metadata from Discovery"""
        
    async def update_application_readiness_status(
        self,
        application_ids: List[str],
        status: str,
        client_account_id: int
    ):
        """Update application readiness for next flow"""
```

**Acceptance Criteria**:
- [ ] Application metadata retrieval integration
- [ ] Readiness status management
- [ ] Cross-flow data consistency
- [ ] Error handling for data availability

---

### INT-003: Create Planning Flow Integration Points
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 6 hours  
**Dependencies**: API-004  
**Sprint**: API Week 6  

**Description**: Implement integration points with Planning Flow for 6R decision handoff and re-assessment support

**Location**: `backend/app/services/integrations/planning_integration.py`

**Technical Requirements**:
- 6R decision data export for Planning Flow consumption
- Re-assessment request handling from Planning Flow
- Move group hint integration and validation
- Bidirectional flow communication patterns
- Data consistency during flow transitions

**Integration Implementation Summary**:
```python
class PlanningFlowIntegration:
    """Integration service for Planning Flow handoff"""
    
    async def export_assessment_results(self, flow_id: str) -> Dict[str, Any]:
        """Export assessment results for Planning Flow"""
        
    async def handle_reassessment_request(
        self, 
        application_ids: List[str],
        planning_context: Dict[str, Any]
    ):
        """Handle re-assessment request from Planning Flow"""
```

**Acceptance Criteria**:
- [ ] 6R decision export for Planning Flow
- [ ] Re-assessment request handling
- [ ] Move group hint integration
- [ ] Bidirectional flow communication

---

## Next Steps

After completing these API and integration tasks, proceed to:
1. **Frontend & UX Tasks** (Document 04)
2. **Testing & DevOps Tasks** (Document 05)

## Dependencies Map

- **API-001** depends on Backend Core (BE-001) and Database Foundation (DB-001)
- **API-002** depends on **API-001** and Backend Core (BE-001)
- **API-003** depends on **API-001** and Backend Core (BE-001)
- **API-004** depends on **API-001** and Backend Core (BE-001)
- **INT-001** depends on **API-001**
- **INT-002** depends on **API-001**
- **INT-003** depends on **API-004**

Frontend development depends on completing these API tasks first.