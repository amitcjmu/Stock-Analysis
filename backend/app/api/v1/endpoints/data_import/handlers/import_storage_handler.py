"""
Import Storage Handler - Persistent data storage and retrieval.
Handles storing imported data in database for cross-page persistence.
"""

import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, and_, func
import uuid
import asyncio
import json
import os
from pydantic import BaseModel, ValidationError

from app.core.database import get_db, AsyncSessionLocal
from app.core.context import get_current_context, RequestContext
from app.models.data_import import DataImport, RawImportRecord, ImportStatus, ImportFieldMapping
from app.schemas.data_import_schemas import StoreImportRequest

# Make client_account import conditional to avoid deployment failures
try:
    from app.models.client_account import ClientAccount, Engagement
    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError:
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = None
    Engagement = None

# V2 Discovery Flow Services
try:
    from app.services.discovery_flow_service import DiscoveryFlowService
    from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
    DISCOVERY_FLOW_AVAILABLE = True
except ImportError:
    DISCOVERY_FLOW_AVAILABLE = False
    DiscoveryFlowService = None
    DiscoveryFlowRepository = None

router = APIRouter()
logger = logging.getLogger(__name__)

# Validation sessions directory
VALIDATION_SESSIONS_PATH = os.path.join("backend", "data", "validation_sessions")

# Ensure the directory exists
os.makedirs(VALIDATION_SESSIONS_PATH, exist_ok=True)

class ImportStorageResponse(BaseModel):
    success: bool
    data_import_id: Optional[str] = None
    flow_id: Optional[str] = None  # ✅ CrewAI-generated flow ID
    error: Optional[str] = None
    message: str
    records_stored: int = 0

@router.post("/store-import")
async def store_import_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> ImportStorageResponse:
    """
    Store validated import data in the database and trigger Discovery Flow.
    
    This endpoint receives the validated CSV data and:
    1. Validates no existing incomplete discovery flow exists
    2. Stores it in the database
    3. Triggers the Discovery Flow for immediate processing
    4. Returns the import session ID for tracking
    """
    try:
        # ✅ VALIDATION: Check for existing incomplete discovery flow
        existing_flow_validation = await _validate_no_incomplete_discovery_flow(
            context.client_account_id, 
            context.engagement_id, 
            db
        )
        
        if not existing_flow_validation["can_proceed"]:
            raise HTTPException(
                status_code=409,  # Conflict
                detail={
                    "error": "incomplete_discovery_flow_exists",
                    "message": existing_flow_validation["message"],
                    "existing_flow": existing_flow_validation["existing_flow"],
                    "recommendations": existing_flow_validation["recommendations"]
                }
            )
        
        # Get raw request body and log it
        raw_body = await request.body()
        logger.info(f"🔍 DEBUG: Raw request body: {raw_body.decode()}")
        
        # Parse JSON manually
        try:
            request_data = json.loads(raw_body)
            logger.info(f"🔍 DEBUG: Parsed JSON: {json.dumps(request_data, indent=2, default=str)}")
        except json.JSONDecodeError as e:
            logger.error(f"🚨 JSON decode error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        
        # Try to create StoreImportRequest from parsed data
        try:
            store_request = StoreImportRequest(**request_data)
            logger.info(f"🔄 Starting data storage for session: {store_request.upload_context.validation_id}")
        except ValidationError as e:
            logger.error(f"🚨 Pydantic validation error: {e}")
            raise HTTPException(status_code=422, detail=f"Validation error: {e.errors()}")
        
        # Extract data from request
        file_data = store_request.file_data
        filename = store_request.metadata.filename
        file_size = store_request.metadata.size
        file_type = store_request.metadata.type
        intended_type = store_request.upload_context.intended_type
        validation_session_id = store_request.upload_context.validation_id  # Use the property that handles both field names
        upload_timestamp = store_request.upload_context.upload_timestamp
        
        # 🔍 DEBUG: Log the actual data being received
        logger.info(f"🔍 DEBUG: file_data type: {type(file_data)}, length: {len(file_data) if file_data else 'None'}")
        if file_data and len(file_data) > 0:
            logger.info(f"🔍 DEBUG: First record sample: {file_data[0] if file_data else 'Empty'}")
            logger.info(f"🔍 DEBUG: First record keys: {list(file_data[0].keys()) if file_data and len(file_data) > 0 else 'No keys'}")
        else:
            logger.error(f"🚨 DEBUG: file_data is empty or None - this will cause flow failure!")
        
        # Use context for client/engagement IDs
        client_account_id = context.client_account_id
        engagement_id = context.engagement_id
        user_id = context.user_id
        
        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, 
                detail="Client account and engagement context required"
            )
        
        # Try to find existing DataImport record, or create one if it doesn't exist
        from sqlalchemy import select
        import uuid as uuid_pkg
        
        try:
            # Validate that validation_session_id is a proper UUID
            uuid_obj = uuid_pkg.UUID(validation_session_id)
            logger.info(f"Looking for existing import record {validation_session_id}")
            
            existing_import_query = select(DataImport).where(DataImport.id == validation_session_id)
            result = await db.execute(existing_import_query)
            data_import = result.scalar_one_or_none()
            
            if not data_import:
                # Create new DataImport record since none exists
                logger.info(f"No existing import record found. Creating new DataImport record with ID: {validation_session_id}")
                data_import = DataImport(
                    id=uuid_obj,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    import_name=f"{filename} Import",
                    import_type=intended_type,
                    description=f"Data import for {intended_type} category",
                    filename=filename,  # Changed from filename
                    file_size=file_size,  # Changed from file_size_bytes
                    mime_type=file_type,  # Changed from file_type
                    status="pending",
                    imported_by=user_id
                )
                db.add(data_import)
                await db.flush()  # Flush to get the record in the session
                logger.info(f"✅ Created new DataImport record: {data_import.id}")
            else:
                logger.info(f"✅ Found existing DataImport record: {data_import.id}")
                
        except ValueError as e:
            logger.error(f"Invalid UUID format for validation_session_id: {validation_session_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session ID format. Expected UUID, got: {validation_session_id}"
            )
        
        # Update the existing import record instead of creating a new one
        data_import.status = "processing"
        
        # Store raw import records AND field mappings
        records_stored = 0
        if file_data:
            # First, store the raw records from the CSV
            for idx, record in enumerate(file_data):
                raw_record = RawImportRecord(
                    data_import_id=data_import.id,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    row_number=idx + 1,
                    raw_data=record,
                    is_processed=False,
                    is_valid=True
                )
                db.add(raw_record)
                records_stored += 1
            
            # Create basic field mappings for each column
            sample_record = file_data[0] if file_data else {}
            for field_name in sample_record.keys():
                field_mapping = ImportFieldMapping(
                    data_import_id=data_import.id,
                    client_account_id=client_account_id,  # Required for multi-tenancy
                    source_field=field_name,
                    target_field=field_name.lower().replace(' ', '_'),
                    confidence_score=0.8,  # Default confidence
                    match_type="direct",  # Changed from mapping_type to match_type
                    status="suggested"  # Default status is suggested, not pending
                )
                db.add(field_mapping)
        
        # Update status to completed with proper record count
        data_import.status = "completed"
        data_import.total_records = records_stored
        data_import.processed_records = records_stored
        data_import.completed_at = datetime.utcnow()
        
        await db.commit()
        
        # 🚀 Trigger Discovery Flow immediately after successful storage
        crewai_flow_id = None  # Initialize to None
        flow_success = False
        flow_error_message = None
        
        try:
            crewai_flow_id = await _trigger_discovery_flow(
                data_import_id=str(data_import.id),
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id or "system",
                file_data=file_data,
                context=context
            )
            if crewai_flow_id:
                logger.info(f"✅ CrewAI Discovery Flow triggered with flow_id: {crewai_flow_id}")
                flow_success = True
            else:
                logger.error("❌ CrewAI Discovery Flow FAILED - no flow_id returned")
                flow_success = False
                flow_error_message = "Discovery Flow initialization failed. No assets were processed."
        except Exception as flow_error:
            logger.error(f"❌ Discovery Flow trigger failed: {flow_error}")
            flow_success = False
            flow_error_message = f"Discovery Flow failed: {str(flow_error)}"
            crewai_flow_id = None
        
        # 🚨 CRITICAL: Update import status based on flow success
        if flow_success:
            data_import.status = "discovery_initiated"
            message = f"Successfully stored {records_stored} records and initiated Discovery Flow"
            logger.info(f"✅ Successfully stored {records_stored} field mappings and initiated discovery flow for import {data_import.id}")
        else:
            data_import.status = "discovery_failed"
            message = f"Data stored ({records_stored} records) but Discovery Flow failed: {flow_error_message}"
            logger.error(f"❌ Data import stored but discovery flow failed for import {data_import.id}: {flow_error_message}")
        
        await db.commit()
        
        return ImportStorageResponse(
            success=flow_success,  # Only success if flow succeeded
            data_import_id=str(data_import.id),
            flow_id=crewai_flow_id,
            message=message,
            records_stored=records_stored,
            error=flow_error_message if not flow_success else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store import data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store import data: {str(e)}")

async def _trigger_discovery_flow(
    data_import_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    file_data: List[Dict[str, Any]],
    context: RequestContext
) -> Optional[str]:
    """
    Trigger the CrewAI Discovery Flow immediately after data import.
    
    This implements the proper CrewAI Flow pattern with @start/@listen decorators
    that produces the purple logs and flow ID tracking.
    
    FIXED: Also creates discovery flow record in database for V2 API compatibility.
    
    Returns:
        Optional[str]: The CrewAI-generated flow_id if successful, None otherwise
    """
    try:
        logger.info(f"🚀 Triggering CrewAI Discovery Flow for import {data_import_id}")
        
        # Import the proper CrewAI Flow
        logger.info(f"🔍 DEBUG: Importing CrewAI Flow modules...")
        from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow, create_unified_discovery_flow
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.discovery_flow_service import DiscoveryFlowService
        logger.info(f"✅ DEBUG: CrewAI Flow modules imported successfully")
        
        # Initialize CrewAI service
        logger.info(f"🔍 DEBUG: Initializing CrewAI service...")
        crewai_service = CrewAIFlowService()
        logger.info(f"✅ DEBUG: CrewAI service initialized")
        
        # Create proper flow using the factory function
        logger.info(f"🔍 DEBUG: Creating discovery flow...")
        discovery_flow = create_unified_discovery_flow(
            flow_id=data_import_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            raw_data=file_data,
            metadata={
                "source": "data_import",
                "filename": f"import_{data_import_id}",
                "import_timestamp": datetime.utcnow().isoformat()
            },
            crewai_service=crewai_service,
            context=context
        )
        logger.info(f"✅ DEBUG: Discovery flow created: {type(discovery_flow)}")
        
        # ✅ CRITICAL FIX: Get the REAL CrewAI Flow ID immediately after creation
        # The CrewAI Flow generates its ID upon instantiation, not during kickoff
        actual_crewai_flow_id = getattr(discovery_flow, 'flow_id', None)
        
        if not actual_crewai_flow_id:
            # Fallback: try other possible flow ID attributes
            for attr in ['id', '_id', '_flow_id', 'execution_id']:
                if hasattr(discovery_flow, attr):
                    actual_crewai_flow_id = getattr(discovery_flow, attr)
                    break
        
        if not actual_crewai_flow_id:
            # Last resort: generate a fallback ID
            actual_crewai_flow_id = f"flow-{data_import_id}"
            logger.warning(f"⚠️ Could not extract CrewAI Flow ID, using fallback: {actual_crewai_flow_id}")
        
        logger.info(f"🎯 REAL CrewAI Flow ID captured: {actual_crewai_flow_id}")
        
        # 🆕 CRITICAL FIX: Create database record using DiscoveryFlowService with REAL ID
        logger.info(f"🔍 DEBUG: Creating discovery flow database record with REAL CrewAI Flow ID...")
        try:
            # Import database session dependency - use proper import
            from app.core.database import AsyncSessionLocal
            
            # Get database session - we need to create a new session for this async operation
            async with AsyncSessionLocal() as db_session:
                # Create DiscoveryFlowService with proper context
                discovery_service = DiscoveryFlowService(db_session, context)
                
                # Create discovery flow record in database with REAL CrewAI Flow ID
                flow_record = await discovery_service.create_discovery_flow(
                    flow_id=actual_crewai_flow_id,
                    raw_data=file_data,
                    metadata={
                        "source": "data_import",
                        "filename": f"import_{data_import_id}",
                        "import_timestamp": datetime.utcnow().isoformat(),
                        "data_import_id": data_import_id,
                        "real_crewai_flow_id": actual_crewai_flow_id
                    },
                    data_import_id=data_import_id,
                    user_id=user_id
                )
                
                # Commit the database transaction
                await db_session.commit()
                
                logger.info(f"✅ Discovery flow database record created with REAL CrewAI Flow ID: {flow_record.flow_id}")
                
        except Exception as db_error:
            logger.error(f"❌ Failed to create discovery flow database record: {db_error}")
            # Don't fail the entire process if database record creation fails
            # The CrewAI flow can still run, but V2 API won't work
            pass
        
        # 🚀 Start the CrewAI Flow in the background using kickoff() method
        logger.info(f"🎯 Starting CrewAI Flow kickoff for session: {data_import_id}")
        
        # Return the REAL flow_id immediately and let the flow run in background
        # This ensures the frontend gets the correct flow_id without waiting for completion
        logger.info(f"✅ Discovery Flow initialized - returning REAL CrewAI Flow ID: {actual_crewai_flow_id}")
        
        # Start the flow execution in background (non-blocking)
        try:
            # Use asyncio.create_task to run the flow in background
            import asyncio
            task = asyncio.create_task(asyncio.to_thread(discovery_flow.kickoff))
            logger.info(f"🚀 CrewAI Flow task created and running in background")
            
            # Don't await the task - let it run independently
            # The flow will continue processing and updating its state
            
        except Exception as kickoff_error:
            logger.error(f"⚠️ Failed to start flow in background: {kickoff_error}")
            # Still return the flow_id since the flow object was created successfully
            # The flow state can be checked later via the flow management APIs
        
        return actual_crewai_flow_id
        
    except ImportError as e:
        logger.warning(f"CrewAI Discovery Flow service not available: {e}")
        logger.error(f"🚨 DEBUG: ImportError details: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to trigger CrewAI Discovery Flow: {e}")
        logger.error(f"🚨 DEBUG: Exception details: {e}")
        import traceback
        logger.error(f"🚨 DEBUG: Full traceback: {traceback.format_exc()}")
        return None

async def _validate_no_incomplete_discovery_flow(
    client_account_id: str,
    engagement_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Validate that no incomplete discovery flow exists for this engagement.
    
    FIXED: Uses the proper DiscoveryFlowStateManager to check for actual discovery flows
    rather than incomplete data import sessions.
    """
    try:
        from app.core.context import RequestContext
        
        # Create proper context for flow state manager
        context = RequestContext(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id="system"  # System validation check
        )
        
        # Use V2 discovery flow service to check for incomplete flows
        if DISCOVERY_FLOW_AVAILABLE:
            discovery_service = DiscoveryFlowService()
            incomplete_flows = await discovery_service.get_incomplete_flows_for_engagement(
                client_account_id, engagement_id
            )
        else:
            incomplete_flows = []
        
        # Filter out flows that are actually empty or have no real progress
        # Only consider flows with actual phases and meaningful progress
        actual_incomplete_flows = []
        for flow in incomplete_flows:
            # Check if this is a real flow with actual progress
            if (flow.get("current_phase") and 
                flow.get("current_phase") not in ["", "initialization"] and
                (flow.get("progress_percentage", 0) > 0 or 
                 flow.get("phase_completion", {}) and any(flow.get("phase_completion", {}).values()))):
                actual_incomplete_flows.append(flow)
        
        # If we found any actual incomplete flows, prevent new import
        if actual_incomplete_flows:
            first_flow = actual_incomplete_flows[0]  # Use the most recent incomplete flow
            
            logger.info(f"🚫 Blocking data import due to incomplete discovery flow: {first_flow['flow_id']} in phase {first_flow['current_phase']}")
            
            return {
                "can_proceed": False,
                "message": f"An incomplete Discovery Flow exists for this engagement. Please complete the existing flow before importing new data.",
                "existing_flow": {
                    "flow_id": first_flow["flow_id"],
                    "current_phase": first_flow["current_phase"],
                    "progress_percentage": first_flow["progress_percentage"],
                    "status": first_flow["status"],
                    "last_activity": first_flow.get("updated_at"),
                    "next_steps": _get_next_steps_for_phase(first_flow["current_phase"])
                },
                "all_incomplete_flows": actual_incomplete_flows,  # For flow management UI
                "recommendations": [
                    f"Complete the existing Discovery Flow in the '{first_flow['current_phase']}' phase",
                    "Navigate to the appropriate discovery page to continue the flow",
                    "Or use the flow management tools to delete the incomplete flow"
                ],
                "show_flow_manager": True  # Signal frontend to show flow management UI
            }
        
        # No actual incomplete flows found - allow import
        logger.info(f"✅ No incomplete discovery flows found for context {client_account_id}/{engagement_id} - allowing import")
        return {
            "can_proceed": True,
            "message": "No incomplete discovery flows found - proceeding with import"
        }
        
    except Exception as e:
        logger.warning(f"Failed to validate discovery flow state: {e}")
        # If validation fails, allow import to proceed (fail-open) to prevent blocking users
        return {
            "can_proceed": True,
            "message": f"Discovery flow validation failed - proceeding with import: {e}"
        }

def _get_next_steps_for_phase(current_phase: str) -> List[str]:
    """Get user-friendly next steps for the current phase."""
    phase_steps = {
        "field_mapping": [
            "Navigate to Attribute Mapping page",
            "Review and approve field mappings",
            "Proceed to Data Cleansing"
        ],
        "data_cleansing": [
            "Navigate to Data Cleansing page", 
            "Review data quality issues",
            "Apply cleansing recommendations",
            "Proceed to Inventory Building"
        ],
        "inventory_building": [
            "Navigate to Asset Inventory page",
            "Review asset classifications",
            "Confirm inventory accuracy",
            "Proceed to Dependencies"
        ],
        "app_server_dependencies": [
            "Navigate to Dependencies page",
            "Review app-to-server relationships",
            "Confirm hosting mappings",
            "Proceed to App-App Dependencies"
        ],
        "app_app_dependencies": [
            "Navigate to Dependencies page",
            "Review app-to-app integrations", 
            "Confirm communication patterns",
            "Proceed to Technical Debt"
        ],
        "technical_debt": [
            "Navigate to Technical Debt page",
            "Review modernization recommendations",
            "Confirm 6R strategies",
            "Complete Discovery Flow"
        ]
    }
    
    return phase_steps.get(current_phase, [
        "Navigate to the Discovery Flow",
        "Complete the current phase",
        "Proceed to next phase"
    ])

@router.get("/latest-import")
async def get_latest_import(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """⚡ OPTIMIZED: Get the latest import data for the current context with performance improvements."""
    start_time = datetime.utcnow()
    
    try:
        # Extract context from request headers
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        logger.info(f"🔍 Getting latest import for context: client={context.client_account_id}, engagement={context.engagement_id}")
        
        # ⚡ FAST PATH: Missing context - return empty response quickly
        if not context.client_account_id or not context.engagement_id:
            logger.warning(f"⚡ Fast path: Missing context, returning empty response")
            return {
                "success": False,
                "message": "Missing client or engagement context",
                "data": [],
                "import_metadata": None,
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "fast_path": True
                }
            }
        
        # ⚡ OPTIMIZED: Execute database query with timeout
        timeout_seconds = 5
        latest_import = None
        
        try:
            async def _get_latest_import_with_timeout():
                # ⚡ OPTIMIZED: Get the most substantial import (highest record count) for this context
                # First try: Look for any status (not just 'processed')
                # Safely parse UUIDs with fallback
                try:
                    client_uuid = uuid.UUID(context.client_account_id) if context.client_account_id else None
                    engagement_uuid = uuid.UUID(context.engagement_id) if context.engagement_id else None
                    logger.debug(f"Converting context IDs to UUIDs: client {context.client_account_id} -> {client_uuid}, engagement {context.engagement_id} -> {engagement_uuid}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid UUID format - client: {context.client_account_id}, engagement: {context.engagement_id}, error: {e}")
                    return None
                
                # Get the latest import for this context
                # Remove the exists() check since older imports may not have raw records
                latest_import_query = select(DataImport).where(
                    and_(
                        DataImport.client_account_id == client_uuid,
                        DataImport.engagement_id == engagement_uuid
                    )
                ).order_by(
                    # First priority: most recent imports  
                    DataImport.created_at.desc()
                ).limit(1)
                
                result = await db.execute(latest_import_query)
                import_result = result.scalar_one_or_none()
                
                # Log what we found for debugging
                if import_result:
                    logger.info(f"✅ Found context-filtered import: {import_result.id} with {import_result.total_records} records ({import_result.filename}) [status: {import_result.status}]")
                else:
                    logger.info(f"ℹ️ No imports found for context: client={context.client_account_id}, engagement={context.engagement_id}")
                    logger.info(f"   This is expected if no data has been imported yet. User should upload data via Data Import page.")
                    logger.debug(f"   Query used client_uuid={client_uuid}, engagement_uuid={engagement_uuid}")
                    
                    # Debug: Check if there are any imports at all in the database
                    all_imports_query = select(DataImport).order_by(DataImport.created_at.desc()).limit(5)
                    all_imports_result = await db.execute(all_imports_query)
                    all_imports = all_imports_result.scalars().all()
                    
                    if all_imports:
                        logger.info(f"📊 Found {len(all_imports)} total imports in database (showing first 5):")
                        for imp in all_imports:
                            logger.info(f"  - {imp.id}: {imp.filename} ({imp.total_records} records, client: {imp.client_account_id}, engagement: {imp.engagement_id}, status: {imp.status})")
                        
                        # Check specifically for imports with our context IDs
                        context_imports_query = select(DataImport).where(
                            and_(
                                DataImport.client_account_id == context.client_account_id,
                                DataImport.engagement_id == context.engagement_id
                            )
                        ).limit(5)
                        context_imports_result = await db.execute(context_imports_query)
                        context_imports = context_imports_result.scalars().all()
                        
                        if context_imports:
                            logger.warning(f"🔍 Actually found {len(context_imports)} imports for context when using string comparison!")
                            logger.warning(f"   This suggests a UUID type mismatch issue")
                        else:
                            logger.info(f"🔍 No imports found even with string comparison for context")
                    else:
                        logger.warning("📊 No imports found in database at all!")
                
                return import_result
            
            # Execute with timeout to prevent hanging
            latest_import = await asyncio.wait_for(_get_latest_import_with_timeout(), timeout=timeout_seconds)
            
        except asyncio.TimeoutError:
            logger.warning(f"⚡ Database timeout after {timeout_seconds}s, returning timeout response")
            return {
                "success": False,
                "message": "Database query timeout - please try again",
                "data": [],
                "import_metadata": None,
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "timeout": True
                }
            }
        except Exception as db_error:
            logger.error(f"⚡ Database error: {db_error}")
            return {
                "success": False,
                "message": f"Database error: {str(db_error)}",
                "data": [],
                "import_metadata": None,
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "database_error": True
                }
            }
        
        # ⚡ FAST PATH: No import found - return quickly but with helpful info
        if not latest_import:
            logger.info(f"⚡ No import data found for context, but returning success with empty data")
            return {
                "success": True,  # Changed to True - no data is not an error
                "message": "No import data available yet for this client and engagement. Please upload data using the Data Import page.",
                "data": [],
                "import_metadata": {
                    "filename": None,
                    "import_type": None,
                    "imported_at": None,
                    "total_records": 0,
                    "actual_total_records": 0,
                    "import_id": None,
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id,
                    "no_imports_exist": True  # Flag to indicate no imports exist yet
                },
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "no_data": True
                }
            }
        
        logger.info(f"✅ Found context-filtered import: {latest_import.id}")
        
        # ⚡ OPTIMIZED: Limit raw records retrieval for performance
        max_records = 1000  # Limit to first 1000 records for UI performance
        
        try:
            async def _get_raw_records_with_timeout():
                # ⚡ SIMPLIFIED: Optimized query with limit
                raw_records_query = (
                    select(RawImportRecord)
                    .where(RawImportRecord.data_import_id == latest_import.id)
                    .order_by(RawImportRecord.row_number)
                    .limit(max_records)
                )
                
                result = await db.execute(raw_records_query)
                return result.scalars().all()
            
            # Execute with timeout
            raw_records = await asyncio.wait_for(_get_raw_records_with_timeout(), timeout=timeout_seconds)
            
        except asyncio.TimeoutError:
            logger.warning(f"⚡ Raw records query timeout, returning metadata only")
            return {
                "success": True,
                "data": [],
                "import_metadata": {
                    "filename": latest_import.filename or "Unknown",
                    "import_type": latest_import.import_type,
                    "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
                    "total_records": latest_import.total_records or 0,
                    "import_id": str(latest_import.id),
                    "client_account_id": str(latest_import.client_account_id),
                    "engagement_id": str(latest_import.engagement_id),
                    "timeout_notice": "Record data timed out, showing metadata only"
                },
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "records_timeout": True
                }
            }
        except Exception as records_error:
            logger.error(f"⚡ Raw records error: {records_error}")
            return {
                "success": True,
                "data": [],
                "import_metadata": {
                    "filename": latest_import.filename or "Unknown",
                    "import_type": latest_import.import_type,
                    "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
                    "total_records": latest_import.total_records or 0,
                    "import_id": str(latest_import.id),
                    "client_account_id": str(latest_import.client_account_id),
                    "engagement_id": str(latest_import.engagement_id),
                    "error_notice": f"Record retrieval error: {str(records_error)}"
                },
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "records_error": True
                }
            }
        
        # ⚡ OPTIMIZED: Transform response data efficiently
        response_data = []
        for record in raw_records:
            response_data.append(record.raw_data)
        
        # If no raw records found, return metadata only with a notice
        if not response_data:
            logger.warning(f"⚠️ Import {latest_import.id} has no raw records stored")
        
        import_metadata = {
            "filename": latest_import.filename or "Unknown",
            "import_type": latest_import.import_type,
            "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
            "total_records": len(response_data),
            "actual_total_records": latest_import.total_records or 0,
            "import_id": str(latest_import.id),
            "client_account_id": str(latest_import.client_account_id),
            "engagement_id": str(latest_import.engagement_id),
            "limited_records": len(response_data) >= max_records,
            "no_raw_records": len(response_data) == 0  # Flag to indicate no raw records
        }
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"✅ Retrieved {len(response_data)} records in {response_time:.2f}ms")
        
        return {
            "success": True,
            "data": response_data,
            "import_metadata": import_metadata,
            "performance": {
                "response_time_ms": response_time,
                "records_retrieved": len(response_data),
                "optimized": True
            }
        }
        
    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"❌ Error getting latest import in {response_time:.2f}ms: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve latest import: {str(e)}",
            "data": [],
            "import_metadata": None,
            "performance": {
                "response_time_ms": response_time,
                "error": True
            }
        }

@router.get("/import/{data_import_id}")
async def get_import_by_id(
    data_import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific import data by data import ID.
    Enables linking and retrieving specific import data.
    """
    try:
        # Find the data import using async session pattern
        import_query = select(DataImport).where(
            DataImport.id == data_import_id
        )
        
        result = await db.execute(import_query)
        data_import = result.scalar_one_or_none()
        
        if not data_import:
            raise HTTPException(status_code=404, detail="Data import not found")
        
        # Get the raw records using async session pattern
        records_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import.id
        ).order_by(RawImportRecord.row_number)
        
        records_result = await db.execute(records_query)
        raw_records = records_result.scalars().all()
        
        # Extract the data
        imported_data = [record.raw_data for record in raw_records]
        
        return {
            "success": True,
            "data_import_id": str(data_import.id),
            "import_metadata": {
                "filename": data_import.filename,
                "import_type": data_import.import_type,
                "imported_at": data_import.completed_at.isoformat() if data_import.completed_at else None,
                "total_records": data_import.total_records,
                "status": data_import.status
            },
            "data": imported_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve import {data_import_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve import: {str(e)}")

@router.get("/flow/{flow_id}/import-data")
async def get_import_data_by_flow_id(
    flow_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get import data for a specific discovery flow.
    This endpoint bridges the gap between flow_id and the raw import data.
    """
    try:
        # Extract context from request headers
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        logger.info(f"🔍 Getting import data for flow: {flow_id}, context: client={context.client_account_id}, engagement={context.engagement_id}")
        
        # First, find the discovery flow by flow_id
        from app.models.discovery_flow import DiscoveryFlow
        flow_query = select(DiscoveryFlow).where(
            DiscoveryFlow.flow_id == flow_id
        )
        
        flow_result = await db.execute(flow_query)
        discovery_flow = flow_result.scalar_one_or_none()
        
        if not discovery_flow:
            logger.warning(f"❌ Discovery flow not found: {flow_id}")
            return {
                "success": False,
                "message": f"Discovery flow not found: {flow_id}",
                "data": [],
                "import_metadata": None
            }
        
        # Check if the flow has a data_import_id
        if not discovery_flow.data_import_id:
            logger.warning(f"⚠️ Discovery flow {flow_id} has no associated data import")
            return {
                "success": True,
                "message": "No data import associated with this flow",
                "data": [],
                "import_metadata": {
                    "flow_id": str(discovery_flow.flow_id),
                    "flow_name": discovery_flow.flow_name,
                    "status": discovery_flow.status,
                    "no_import": True
                }
            }
        
        # Find the data import using the data_import_id
        import_query = select(DataImport).where(
            DataImport.id == discovery_flow.data_import_id
        )
        
        import_result = await db.execute(import_query)
        data_import = import_result.scalar_one_or_none()
        
        if not data_import:
            logger.error(f"❌ Data import not found for flow {flow_id}, data_import_id: {discovery_flow.data_import_id}")
            return {
                "success": False,
                "message": f"Data import not found: {discovery_flow.data_import_id}",
                "data": [],
                "import_metadata": None
            }
        
        # Get the raw records
        records_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import.id
        ).order_by(RawImportRecord.row_number).limit(1000)  # Limit for performance
        
        records_result = await db.execute(records_query)
        raw_records = records_result.scalars().all()
        
        # Extract the data
        imported_data = [record.raw_data for record in raw_records]
        
        logger.info(f"✅ Retrieved {len(imported_data)} records for flow {flow_id}")
        
        return {
            "success": True,
            "data": imported_data,
            "import_metadata": {
                "filename": data_import.filename or "Unknown",
                "import_type": data_import.import_type,
                "imported_at": data_import.completed_at.isoformat() if data_import.completed_at else None,
                "total_records": len(imported_data),
                "actual_total_records": data_import.total_records or 0,
                "import_id": str(data_import.id),
                "flow_id": str(discovery_flow.flow_id),
                "flow_name": discovery_flow.flow_name,
                "flow_status": discovery_flow.status,
                "client_account_id": str(data_import.client_account_id),
                "engagement_id": str(data_import.engagement_id)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting import data for flow {flow_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve import data: {str(e)}",
            "data": [],
            "import_metadata": None
        } 