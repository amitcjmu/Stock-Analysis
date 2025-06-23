"""
Clean Data Import API Handler - Streamlined data import with proper flow state management.
Handles file upload and storage with CrewAI Discovery Flow integration.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import_session import DataImportSession, SessionStatus, SessionType
from app.models.workflow_state import WorkflowState
from app.services.crewai_flow_service import CrewAIFlowService, get_crewai_flow_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class FileUploadRequest(BaseModel):
    filename: str
    sample_data: List[Dict[str, Any]]
    headers: List[str]
    upload_type: str
    user_id: str

class UploadResponse(BaseModel):
    session_id: str
    status: str
    message: str
    flow_id: str = None
    current_phase: str = "initialization"

async def _ensure_data_import_session_exists_direct(
    db: AsyncSession,
    session_id: str,
    metadata: Dict[str, Any],
    context: RequestContext
):
    """Create data import session and corresponding workflow state for proper flow continuity."""
    try:
        logger.info(f"🔄 Creating data import session with flow state: {session_id}")
        
        # Get client and engagement context
        client_id = context.client_account_id
        engagement_id = context.engagement_id
        user_id = context.user_id or "demo-user"
        
        # Use demo UUID for development
        demo_user_uuid = uuid.UUID("44444444-4444-4444-4444-444444444444")
        
        session_data = {
            "id": uuid.UUID(session_id),
            "client_account_id": uuid.UUID(client_id),
            "engagement_id": uuid.UUID(engagement_id),
            "session_name": f"crewai-discovery-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "description": "Auto-created session for CrewAI discovery workflow",
            "is_default": False,
            "session_type": "data_import",
            "auto_created": True,
            "source_filename": metadata.get("filename", "discovery_flow.csv"),
            "status": "active",
            "created_by": demo_user_uuid,
            "business_context": {
                "import_purpose": "discovery_flow",
                "data_source_description": "CrewAI automated discovery workflow",
                "expected_changes": ["asset_classification", "field_mapping", "data_validation"]
            },
            "agent_insights": {
                "classification_confidence": 0.0,
                "data_quality_issues": [],
                "recommendations": [],
                "learning_outcomes": []
            }
        }
        
        # Create data import session
        new_session = DataImportSession(**session_data)
        db.add(new_session)
        
        # 🚀 CRITICAL FIX: Create corresponding WorkflowState for flow continuity
        flow_id = str(uuid.uuid4())
        workflow_state = WorkflowState(
            flow_id=uuid.UUID(flow_id),
            session_id=uuid.UUID(session_id),
            client_account_id=uuid.UUID(client_id),
            engagement_id=uuid.UUID(engagement_id),
            user_id=user_id,
            workflow_type="unified_discovery",
            current_phase="data_import",
            status="running",
            progress_percentage=10.0,  # Data import completed
            phase_completion={
                "data_import": True,  # Mark data import as complete
                "field_mapping": False,
                "data_cleansing": False,
                "asset_inventory": False,
                "dependency_analysis": False,
                "tech_debt_analysis": False
            },
            crew_status={},
            state_data={
                "session_id": session_id,
                "client_account_id": client_id,
                "engagement_id": engagement_id,
                "user_id": user_id,
                "raw_data": metadata.get("sample_data", []),
                "metadata": metadata,
                "started_at": datetime.utcnow().isoformat(),
                "current_phase": "data_import",
                "status": "running"
            },
            raw_data=metadata.get("sample_data", []),
            field_mappings={},
            cleaned_data=[],
            asset_inventory={},
            dependencies={},
            technical_debt={},
            data_quality_metrics={},
            agent_insights=[],
            success_criteria={},
            errors=[],
            warnings=[],
            workflow_log=[
                f"Data import session created: {session_id}",
                f"File uploaded: {metadata.get('filename', 'unknown')}",
                f"Records imported: {len(metadata.get('sample_data', []))}"
            ],
            discovery_summary={},
            assessment_flow_package={},
            database_assets_created=[],
            database_integration_status={},
            shared_memory_id="",
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(workflow_state)
        
        # Commit both records together
        await db.commit()
        await db.refresh(new_session)
        await db.refresh(workflow_state)
        
        logger.info(f"✅ Created data import session AND workflow state: {session_id}")
        logger.info(f"✅ Flow ID: {flow_id}, Phase: {workflow_state.current_phase}, Progress: {workflow_state.progress_percentage}%")
        
        return {
            "session_id": session_id,
            "flow_id": flow_id,
            "workflow_state_created": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create session with workflow state: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/data-imports", response_model=UploadResponse)
async def upload_data_file_clean(
    file_request: FileUploadRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    crewai_service: CrewAIFlowService = Depends(get_crewai_flow_service)
) -> UploadResponse:
    """
    Clean data import endpoint with proper flow state management.
    Creates both DataImportSession and WorkflowState for flow continuity.
    """
    try:
        context = await get_current_context(request)
        logger.info(f"🚀 Clean data import for client: {context.client_account_id}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Prepare data for CrewAI flow in the expected format
        data_source = {
            "file_data": file_request.sample_data,  # The actual data records
            "metadata": {
                "filename": file_request.filename,
                "upload_type": file_request.upload_type,
                "headers": file_request.headers,
                "total_records": len(file_request.sample_data),
                "user_id": file_request.user_id,
                "session_id": session_id,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "sample_data": file_request.sample_data,  # Include sample data for workflow state
                "options": {
                    "enable_parallel_execution": True,
                    "enable_retry_logic": True,
                    "max_retries": 3,
                    "timeout_seconds": 300
                }
            }
        }
        
        # CRITICAL FIX: Create data import session AND workflow state for flow continuity
        session_result = await _ensure_data_import_session_exists_direct(
            db=db,
            session_id=session_id,
            metadata=data_source.get("metadata", {}),
            context=context
        )
        
        flow_id = session_result.get("flow_id")
        
        logger.info(f"✅ Data import completed with flow state: session={session_id}, flow={flow_id}")
        logger.info(f"🎯 Next phase: field_mapping (ready for attribute mapping page)")
        
        # Return clean response with flow information
        return UploadResponse(
            session_id=session_id,
            status="completed",
            message="Data import completed successfully with flow state created",
            flow_id=flow_id,
            current_phase="field_mapping"  # Ready for next phase
        )
        
    except Exception as e:
        logger.error(f"❌ Clean data import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data import failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for clean data import API."""
    return {
        "status": "healthy",
        "service": "clean_data_import",
        "timestamp": datetime.utcnow().isoformat()
    } 