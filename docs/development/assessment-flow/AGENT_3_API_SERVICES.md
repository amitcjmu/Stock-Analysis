# AI Coding Agent 3: API & Service Layer Implementation

## Agent Overview
You are responsible for creating the API endpoints, service layer, and ensuring proper integration between the frontend and backend. Your work provides the REST API interface for the Assessment Flow feature.

## Context

### Project Overview
The Assessment Flow API provides v3 endpoints following RESTful principles. The API must:
- Handle flow initialization from selected applications
- Execute flow phases asynchronously
- Support user review and override capabilities
- Maintain multi-tenant data isolation
- Provide real-time status updates

### Technical Stack
- **Framework**: FastAPI with async/await
- **API Version**: v3 (new endpoints)
- **Authentication**: Multi-tenant headers (X-Client-Account-ID, X-Engagement-ID)
- **Response Format**: JSON with proper error handling
- **Documentation**: OpenAPI/Swagger auto-generated

### API Design Principles
- RESTful resource-based URLs
- Proper HTTP status codes
- Comprehensive error responses
- Request/response validation with Pydantic
- Multi-tenant isolation at all levels

## Your Assigned Tasks

### 🐍 Backend Tasks

#### BE-006: Create Assessment Service Layer
**Priority**: P1 - High  
**Effort**: 8 hours  
**Location**: `backend/app/services/assessment_service.py`

```python
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.assessment_repository import AssessmentRepository
from app.models.assessment_flow_state import AssessmentFlowState, SixRDecision
from app.services.crewai_flows.assessment_flow import AssessmentFlow
from app.services.crewai_service import CrewAIService
from app.core.flow_context import FlowContext
from app.core.exceptions import (
    FlowNotFoundError, 
    InvalidFlowStateError,
    UnauthorizedError
)

logger = logging.getLogger(__name__)

class AssessmentService:
    """Business logic service for assessment flows"""
    
    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id
        self.repository = AssessmentRepository(db, client_account_id)
        self.crewai_service = CrewAIService()
    
    async def initialize_assessment_flow(
        self,
        discovery_flow_id: str,
        selected_application_ids: List[str],
        engagement_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Initialize a new assessment flow from selected applications.
        
        Steps:
        1. Validate discovery flow exists and is completed
        2. Validate selected applications belong to discovery flow
        3. Create assessment flow record
        4. Initialize CrewAI flow execution
        5. Return flow details
        """
        logger.info(f"Initializing assessment flow for {len(selected_application_ids)} applications")
        
        try:
            # Validate discovery flow
            discovery_flow = await self._validate_discovery_flow(discovery_flow_id)
            
            # Validate selected applications
            await self._validate_selected_applications(
                discovery_flow_id, 
                selected_application_ids
            )
            
            # Create assessment flow record
            assessment_flow = await self.repository.create_assessment_flow(
                discovery_flow_id=discovery_flow_id,
                selected_application_ids=selected_application_ids,
                engagement_id=engagement_id
            )
            
            # Create flow context
            context = FlowContext(
                flow_id=str(assessment_flow.id),
                client_account_id=self.client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                discovery_flow_id=discovery_flow_id
            )
            
            # Initialize CrewAI flow
            flow = AssessmentFlow(self.crewai_service, context)
            
            # Create initial state
            initial_state = AssessmentFlowState(
                flow_id=str(assessment_flow.id),
                discovery_flow_id=discovery_flow_id,
                client_account_id=self.client_account_id,
                engagement_id=engagement_id,
                selected_application_ids=selected_application_ids,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Set flow state
            flow.state = initial_state
            
            # Start flow execution asynchronously
            # Note: In production, this would be queued to a background task
            await self._execute_flow_async(flow)
            
            return {
                "flow_id": str(assessment_flow.id),
                "status": assessment_flow.status,
                "progress": assessment_flow.progress,
                "selected_applications": len(selected_application_ids),
                "next_phase": "architecture_verification"
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize assessment flow: {str(e)}")
            raise
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get current status and progress of assessment flow"""
        flow = await self.repository.get_assessment_flow(flow_id)
        
        if not flow:
            raise FlowNotFoundError(f"Assessment flow {flow_id} not found")
        
        return {
            "flow_id": flow_id,
            "status": flow.status,
            "progress": flow.progress,
            "current_phase": flow.current_phase,
            "phase_results": flow.phase_results or {},
            "created_at": flow.created_at.isoformat(),
            "updated_at": flow.updated_at.isoformat(),
            "completed_at": flow.completed_at.isoformat() if flow.completed_at else None
        }
    
    async def execute_flow_phase(
        self, 
        flow_id: str, 
        phase: str,
        phase_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a specific phase of the assessment flow"""
        # Validate flow exists and is in correct state
        flow_record = await self.repository.get_assessment_flow(flow_id)
        
        if not flow_record:
            raise FlowNotFoundError(f"Assessment flow {flow_id} not found")
        
        # Check if phase execution is allowed
        if flow_record.status == "completed":
            raise InvalidFlowStateError("Cannot execute phase on completed flow")
        
        # Execute phase based on current state
        # This would typically trigger the CrewAI flow to continue
        # For now, return phase status
        
        return {
            "phase": phase,
            "status": "executed",
            "next_phase": self._get_next_phase(phase)
        }
    
    async def get_architecture_requirements(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get architecture requirements for the assessment"""
        requirements = await self.repository.get_architecture_requirements(flow_id)
        
        return [
            {
                "id": str(req.id),
                "type": req.requirement_type,
                "description": req.description,
                "mandatory": req.mandatory,
                "verification_status": req.verification_status,
                "verified_at": req.verified_at.isoformat() if req.verified_at else None
            }
            for req in requirements
        ]
    
    async def update_architecture_verification(
        self,
        flow_id: str,
        requirement_id: str,
        verification_status: str,
        notes: Optional[str] = None,
        verified_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update architecture requirement verification status"""
        await self.repository.update_architecture_requirement(
            requirement_id=requirement_id,
            verification_status=verification_status,
            notes=notes,
            verified_by=verified_by
        )
        
        return {
            "requirement_id": requirement_id,
            "verification_status": verification_status,
            "updated": True
        }
    
    async def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get technical debt analysis results"""
        tech_debt_items = await self.repository.get_tech_debt_analysis(flow_id)
        
        # Group by application
        debt_by_app = {}
        for item in tech_debt_items:
            app_id = str(item.application_id)
            if app_id not in debt_by_app:
                debt_by_app[app_id] = {
                    "overall_score": 0,
                    "items": []
                }
            
            debt_by_app[app_id]["items"].append({
                "category": item.debt_category,
                "severity": item.severity,
                "description": item.description,
                "remediation_effort_hours": item.remediation_effort_hours,
                "impact_on_migration": item.impact_on_migration
            })
        
        # Calculate overall scores
        for app_data in debt_by_app.values():
            app_data["overall_score"] = self._calculate_tech_debt_score(app_data["items"])
        
        return {"applications": debt_by_app}
    
    async def get_sixr_decisions(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get 6R strategy decisions for all applications"""
        decisions = await self.repository.get_sixr_decisions(flow_id)
        
        return [
            {
                "application_id": str(decision.application_id),
                "application_name": decision.application_name,
                "recommended_strategy": decision.recommended_strategy,
                "confidence_score": decision.confidence_score,
                "rationale": decision.rationale,
                "risk_factors": decision.risk_factors or [],
                "estimated_effort_hours": decision.estimated_effort_hours,
                "estimated_cost": float(decision.estimated_cost) if decision.estimated_cost else 0,
                "user_override_strategy": decision.user_override_strategy,
                "override_reason": decision.override_reason,
                "override_by": decision.override_by,
                "override_at": decision.override_at.isoformat() if decision.override_at else None
            }
            for decision in decisions
        ]
    
    async def override_sixr_decision(
        self,
        flow_id: str,
        application_id: str,
        override_strategy: str,
        override_reason: str,
        override_by: str
    ) -> Dict[str, Any]:
        """Override AI-recommended 6R strategy"""
        # Validate strategy
        valid_strategies = ["rehost", "replatform", "refactor", "repurchase", "retire", "retain"]
        if override_strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy: {override_strategy}")
        
        # Update decision
        decision = await self.repository.update_sixr_decision_override(
            flow_id=flow_id,
            application_id=application_id,
            override_strategy=override_strategy,
            override_reason=override_reason,
            override_by=override_by
        )
        
        # Capture learning feedback
        await self._capture_learning_feedback(
            flow_id=flow_id,
            decision_id=str(decision.id),
            original_strategy=decision.recommended_strategy,
            override_strategy=override_strategy,
            reason=override_reason
        )
        
        return {
            "application_id": application_id,
            "override_strategy": override_strategy,
            "updated": True
        }
    
    async def finalize_assessment(self, flow_id: str) -> Dict[str, Any]:
        """Finalize the assessment flow"""
        # Update flow status
        await self.repository.update_flow_status(
            flow_id=flow_id,
            status="completed",
            progress=100,
            current_phase="finalized"
        )
        
        # Get summary statistics
        decisions = await self.repository.get_sixr_decisions(flow_id)
        
        strategy_distribution = {}
        user_overrides = 0
        
        for decision in decisions:
            strategy = decision.user_override_strategy or decision.recommended_strategy
            strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
            
            if decision.user_override_strategy:
                user_overrides += 1
        
        return {
            "status": "completed",
            "summary": {
                "total_applications": len(decisions),
                "strategy_distribution": strategy_distribution,
                "user_overrides": user_overrides
            }
        }
    
    async def generate_assessment_report(self, flow_id: str) -> Dict[str, Any]:
        """Generate comprehensive assessment report"""
        # Gather all assessment data
        flow = await self.repository.get_assessment_flow(flow_id)
        requirements = await self.get_architecture_requirements(flow_id)
        tech_debt = await self.get_tech_debt_analysis(flow_id)
        decisions = await self.get_sixr_decisions(flow_id)
        
        return {
            "flow_id": flow_id,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": self._generate_executive_summary(flow, decisions),
            "detailed_findings": {
                "architecture_compliance": requirements,
                "technical_debt": tech_debt,
                "sixr_decisions": decisions
            },
            "recommendations": self._generate_recommendations(decisions, tech_debt)
        }
    
    # Private helper methods
    async def _validate_discovery_flow(self, discovery_flow_id: str) -> Any:
        """Validate discovery flow exists and is completed"""
        # Implementation
        pass
    
    async def _validate_selected_applications(
        self, 
        discovery_flow_id: str,
        selected_ids: List[str]
    ) -> None:
        """Validate selected applications belong to discovery flow"""
        # Implementation
        pass
    
    async def _execute_flow_async(self, flow: AssessmentFlow) -> None:
        """Execute flow asynchronously (would be queued in production)"""
        # In production, this would be sent to a task queue
        # For now, we'll just start the flow
        try:
            flow.kickoff()
        except Exception as e:
            logger.error(f"Flow execution failed: {str(e)}")
    
    def _get_next_phase(self, current_phase: str) -> str:
        """Determine next phase in flow"""
        phase_order = [
            "initialization",
            "architecture_verification",
            "tech_debt_analysis",
            "sixr_strategy",
            "collaborative_review",
            "finalized"
        ]
        
        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass
        
        return "finalized"
    
    def _calculate_tech_debt_score(self, debt_items: List[Dict[str, Any]]) -> float:
        """Calculate overall tech debt score"""
        # Implementation
        return 0.0
    
    async def _capture_learning_feedback(
        self,
        flow_id: str,
        decision_id: str,
        original_strategy: str,
        override_strategy: str,
        reason: str
    ) -> None:
        """Capture feedback for agent learning"""
        # Implementation
        pass
    
    def _generate_executive_summary(self, flow: Any, decisions: List[Dict[str, Any]]) -> str:
        """Generate executive summary for report"""
        # Implementation
        return "Executive summary..."
    
    def _generate_recommendations(
        self, 
        decisions: List[Dict[str, Any]],
        tech_debt: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on assessment"""
        # Implementation
        return ["Recommendation 1", "Recommendation 2"]
```

---

### 🔌 API Tasks

#### API-001: Create Assessment Flow Router
**Priority**: P0 - Critical  
**Effort**: 4 hours  
**Location**: `backend/app/api/v3/assessment_flow.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.api.deps import get_db, get_current_client_account_id, get_current_user
from app.services.assessment_service import AssessmentService
from app.schemas.assessment import (
    AssessmentFlowInitRequest,
    AssessmentFlowInitResponse,
    AssessmentFlowStatusResponse,
    ArchitectureRequirementResponse,
    ArchitectureVerificationRequest,
    TechDebtAnalysisResponse,
    SixRDecisionResponse,
    SixROverrideRequest,
    AssessmentReportResponse
)
from app.core.exceptions import handle_flow_exceptions

router = APIRouter(prefix="/assessment-flow", tags=["assessment"])

@router.post("/initialize", response_model=AssessmentFlowInitResponse)
async def initialize_assessment_flow(
    request: AssessmentFlowInitRequest,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id),
    current_user: dict = Depends(get_current_user)
) -> AssessmentFlowInitResponse:
    """
    Initialize a new assessment flow with selected applications from discovery.
    
    This endpoint:
    1. Validates the discovery flow exists and is completed
    2. Validates selected applications belong to the discovery flow
    3. Creates a new assessment flow record
    4. Starts the CrewAI assessment process asynchronously
    5. Returns the flow ID for tracking
    """
    service = AssessmentService(db, client_account_id)
    
    try:
        result = await service.initialize_assessment_flow(
            discovery_flow_id=request.discovery_flow_id,
            selected_application_ids=request.selected_application_ids,
            engagement_id=request.engagement_id,
            user_id=current_user["id"]
        )
        
        return AssessmentFlowInitResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to initialize assessment flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{flow_id}/status", response_model=AssessmentFlowStatusResponse)
async def get_assessment_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id)
) -> AssessmentFlowStatusResponse:
    """
    Get the current status and progress of an assessment flow.
    
    Returns:
    - Current flow status (initialized, in_progress, awaiting_review, completed)
    - Progress percentage (0-100)
    - Current phase
    - Phase results
    - Timestamps
    """
    service = AssessmentService(db, client_account_id)
    
    try:
        result = await service.get_flow_status(flow_id)
        return AssessmentFlowStatusResponse(**result)
        
    except FlowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/{flow_id}/execute/{phase}")
async def execute_flow_phase(
    flow_id: str,
    phase: str,
    phase_input: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id)
) -> Dict[str, Any]:
    """
    Execute a specific phase of the assessment flow.
    
    Phases:
    - architecture_verification
    - tech_debt_analysis
    - sixr_strategy
    - collaborative_review
    - finalize
    """
    service = AssessmentService(db, client_account_id)
    
    valid_phases = [
        "architecture_verification",
        "tech_debt_analysis", 
        "sixr_strategy",
        "collaborative_review",
        "finalize"
    ]
    
    if phase not in valid_phases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase: {phase}"
        )
    
    try:
        result = await service.execute_flow_phase(flow_id, phase, phase_input)
        return result
        
    except (FlowNotFoundError, InvalidFlowStateError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{flow_id}/architecture-requirements", response_model=List[ArchitectureRequirementResponse])
async def get_architecture_requirements(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id)
) -> List[ArchitectureRequirementResponse]:
    """Get architecture requirements and their verification status"""
    service = AssessmentService(db, client_account_id)
    
    requirements = await service.get_architecture_requirements(flow_id)
    return [ArchitectureRequirementResponse(**req) for req in requirements]

@router.put("/{flow_id}/architecture-requirements/{req_id}")
async def update_architecture_verification(
    flow_id: str,
    req_id: str,
    request: ArchitectureVerificationRequest,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update verification status for an architecture requirement"""
    service = AssessmentService(db, client_account_id)
    
    result = await service.update_architecture_verification(
        flow_id=flow_id,
        requirement_id=req_id,
        verification_status=request.verification_status,
        notes=request.notes,
        verified_by=current_user["email"]
    )
    
    return result

@router.get("/{flow_id}/tech-debt", response_model=TechDebtAnalysisResponse)
async def get_tech_debt_analysis(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id)
) -> TechDebtAnalysisResponse:
    """Get technical debt analysis results for all applications"""
    service = AssessmentService(db, client_account_id)
    
    analysis = await service.get_tech_debt_analysis(flow_id)
    return TechDebtAnalysisResponse(**analysis)

@router.get("/{flow_id}/sixr-decisions", response_model=List[SixRDecisionResponse])
async def get_sixr_decisions(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id)
) -> List[SixRDecisionResponse]:
    """Get 6R strategy decisions for all applications"""
    service = AssessmentService(db, client_account_id)
    
    decisions = await service.get_sixr_decisions(flow_id)
    return [SixRDecisionResponse(**decision) for decision in decisions]

@router.put("/{flow_id}/sixr-decisions/{app_id}")
async def override_sixr_decision(
    flow_id: str,
    app_id: str,
    request: SixROverrideRequest,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Override the AI-recommended 6R strategy for an application"""
    service = AssessmentService(db, client_account_id)
    
    result = await service.override_sixr_decision(
        flow_id=flow_id,
        application_id=app_id,
        override_strategy=request.override_strategy,
        override_reason=request.override_reason,
        override_by=current_user["email"]
    )
    
    return result

@router.post("/{flow_id}/finalize")
async def finalize_assessment(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id)
) -> Dict[str, Any]:
    """
    Finalize the assessment flow and prepare for Planning Flow.
    
    This endpoint:
    1. Marks the assessment as completed
    2. Calculates summary statistics
    3. Prepares data for the next flow
    """
    service = AssessmentService(db, client_account_id)
    
    result = await service.finalize_assessment(flow_id)
    return result

@router.get("/{flow_id}/report", response_model=AssessmentReportResponse)
async def get_assessment_report(
    flow_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db),
    client_account_id: int = Depends(get_current_client_account_id)
) -> AssessmentReportResponse:
    """
    Generate a comprehensive assessment report.
    
    Formats supported:
    - json (default)
    - pdf (future enhancement)
    """
    service = AssessmentService(db, client_account_id)
    
    report = await service.generate_assessment_report(flow_id)
    return AssessmentReportResponse(**report)

# Include router in main app
# In app/api/v3/__init__.py:
# from app.api.v3.assessment_flow import router as assessment_router
# api_router.include_router(assessment_router)
```

#### API-002 through API-005: Individual Endpoint Implementations
These are covered in the router above. Focus on:
- Proper error handling
- Request/response validation
- Multi-tenant security
- Async execution

---

### Additional Tasks

#### Create Pydantic Schemas
**Location**: `backend/app/schemas/assessment.py`

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SixRStrategyEnum(str, Enum):
    REHOST = "rehost"
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    REPURCHASE = "repurchase"
    RETIRE = "retire"
    RETAIN = "retain"

class AssessmentFlowInitRequest(BaseModel):
    discovery_flow_id: str = Field(..., description="ID of completed discovery flow")
    selected_application_ids: List[str] = Field(..., min_items=1)
    engagement_id: int = Field(..., gt=0)
    
    @validator('selected_application_ids')
    def validate_app_ids(cls, v):
        if len(v) > 1000:
            raise ValueError("Cannot assess more than 1000 applications at once")
        return v

class AssessmentFlowInitResponse(BaseModel):
    flow_id: str
    status: str
    progress: int
    selected_applications: int
    next_phase: str

class AssessmentFlowStatusResponse(BaseModel):
    flow_id: str
    status: str
    progress: int = Field(..., ge=0, le=100)
    current_phase: str
    phase_results: Dict[str, Any]
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    estimated_completion: Optional[str]

class ArchitectureRequirementResponse(BaseModel):
    id: str
    type: str
    description: str
    mandatory: bool
    verification_status: str
    verified_at: Optional[str]

class ArchitectureVerificationRequest(BaseModel):
    verification_status: str = Field(..., regex="^(pending|verified|failed)$")
    notes: Optional[str] = Field(None, max_length=1000)

class TechDebtItemResponse(BaseModel):
    category: str
    severity: str
    description: str
    remediation_effort_hours: int
    impact_on_migration: str

class TechDebtAnalysisResponse(BaseModel):
    applications: Dict[str, Dict[str, Any]]

class SixRDecisionResponse(BaseModel):
    application_id: str
    application_name: str
    recommended_strategy: SixRStrategyEnum
    confidence_score: float = Field(..., ge=0, le=1)
    rationale: str
    risk_factors: List[str]
    estimated_effort_hours: int
    estimated_cost: float
    user_override_strategy: Optional[SixRStrategyEnum]
    override_reason: Optional[str]
    override_by: Optional[str]
    override_at: Optional[str]

class SixROverrideRequest(BaseModel):
    override_strategy: SixRStrategyEnum
    override_reason: str = Field(..., min_length=10, max_length=500)

class AssessmentReportResponse(BaseModel):
    flow_id: str
    generated_at: str
    executive_summary: str
    detailed_findings: Dict[str, Any]
    recommendations: List[str]
```

#### Update API Router Registration
**Location**: `backend/app/api/v3/__init__.py`

Add the assessment router to v3 API.

## Development Guidelines

### API Standards
- Use proper HTTP status codes (200, 201, 400, 404, 500)
- Include detailed error messages
- Validate all inputs with Pydantic
- Use async/await for all database operations
- Include OpenAPI documentation

### Testing Your Implementation
```bash
# Test API endpoints
docker exec -it migration_backend python -m pytest tests/api/test_assessment_endpoints.py -v

# Test service layer
docker exec -it migration_backend python -m pytest tests/services/test_assessment_service.py -v

# Manual API testing
curl -X POST http://localhost:8000/api/v3/assessment-flow/initialize \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: 1" \
  -H "X-Engagement-ID: 1" \
  -d '{
    "discovery_flow_id": "test-discovery-001",
    "selected_application_ids": ["app1", "app2", "app3"],
    "engagement_id": 1
  }'
```

### Error Handling
```python
# Standard error responses
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]]
    request_id: str

# Use consistent error handling
try:
    # Your code
except FlowNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
except ValidationError as e:
    raise HTTPException(status_code=400, detail=e.errors())
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Multi-Tenant Security
- Always validate client_account_id from headers
- Use ContextAwareRepository for data isolation
- Never expose data from other tenants
- Log security-relevant events

### Performance Considerations
- Use pagination for large result sets
- Implement caching for frequently accessed data
- Use database indexes (coordinate with Agent 1)
- Monitor API response times

## Completion Checklist
- [ ] BE-006: Complete AssessmentService implementation
- [ ] API-001: Create Assessment Flow Router
- [ ] API-002: Initialize endpoint with validation
- [ ] API-003: Phase execution endpoints
- [ ] API-004: 6R decision endpoints with override
- [ ] API-005: Report generation endpoint
- [ ] Create all Pydantic schemas
- [ ] Update API router registration
- [ ] Write API integration tests
- [ ] Test multi-tenant isolation
- [ ] API documentation complete

## Dependencies
- Requires Agent 1's database models and repository
- Requires Agent 2's AssessmentFlow implementation
- Your API will be consumed by Agent 4's frontend

## Coordination Notes
- Ensure service methods handle async CrewAI execution
- Implement proper error propagation from service to API
- Consider WebSocket for real-time updates (future enhancement)
- Document all endpoints in OpenAPI format