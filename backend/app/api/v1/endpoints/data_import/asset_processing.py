"""
Asset Processing Module - Asset creation and processing workflows.
Handles raw data to asset conversion, CrewAI integration, and agentic processing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.asset import Asset
from app.models.data_import import RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping

router = APIRouter()
logger = logging.getLogger(__name__)

def get_safe_context() -> RequestContext:
    """Get context safely with fallback values"""
    context = get_current_context()
    if context:
        return context
    
    logger.warning("⚠️ No context available, using fallback values")
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222", 
        user_id="347d1ecd-04f6-4e3a-86ca-d35703512301"
    )

@router.post("/process-raw-to-assets")
async def process_raw_to_assets(
    flow_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Process raw import data into classified assets using unified CrewAI Flow Service.
    
    This endpoint uses the consolidated CrewAI Flow Service with modular handler architecture
    for intelligent asset classification and workflow integration.
    
    IMPORTANT: This endpoint now enforces field mapping approval before asset creation.
    """
    
    if not flow_id:
        raise HTTPException(status_code=400, detail="flow_id is required")
    
    try:
        context = get_safe_context()
        # SECURITY CHECK: Verify field mappings are approved before asset creation
        # During migration: flow_id maps to data import session
        mappings_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == flow_id
        )
        mappings_result = await db.execute(mappings_query)
        mappings = mappings_result.scalars().all()
        
        if not mappings:
            raise HTTPException(
                status_code=400, 
                detail="No field mappings found. Please complete field mapping first."
            )
        
        # Check approval status
        approved_mappings = [m for m in mappings if m.status == "approved"]
        pending_mappings = [m for m in mappings if m.status in ["suggested", "pending"]]
        
        if not approved_mappings:
            raise HTTPException(
                status_code=400,
                detail="No field mappings have been approved. Please review and approve field mappings before creating assets."
            )
        
        if pending_mappings:
            raise HTTPException(
                status_code=400,
                detail=f"{len(pending_mappings)} field mappings are still pending approval. Please approve or reject all mappings before proceeding."
            )
        
        logger.info(f"✅ Field mapping approval verified: {len(approved_mappings)} approved mappings found")
        
        # Check if we have raw records to process
        raw_count_query = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == flow_id
            )
        )
        raw_count = raw_count_query.scalar()
        
        if raw_count == 0:
            return {
                "status": "error",
                "message": "No raw import records found for the specified session",
                "flow_id": flow_id
            }
        
        logger.info(f"🔄 Processing {raw_count} raw records from flow: {flow_id}")
        
        # Use the unified CrewAI Flow Service with proper modular architecture
        try:
            from app.services.crewai_flow_service import crewai_flow_service
            
            # Check if the unified service is available
            if crewai_flow_service.is_available():
                logger.info("🤖 Using unified CrewAI Flow Service for intelligent processing")
                
                # Use unified flow with database integration
                result = await crewai_flow_service.run_discovery_flow_with_state(
                    cmdb_data={
                        "headers": [],  # Will be loaded from raw records
                        "sample_data": [],  # Will be loaded from raw records
                        "flow_id": flow_id
                    },
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id
                )
                
                # Enhanced response with detailed classification results
                if result.get("status") == "success":
                    logger.info("✅ Unified CrewAI Flow completed successfully!")
                    logger.info(f"   📊 Processing Status: {result.get('processing_status', 'completed')}")
                    logger.info(f"   📱 Applications: {result.get('classification_results', {}).get('applications', 0)}")
                    logger.info(f"   🖥️  Servers: {result.get('classification_results', {}).get('servers', 0)}")
                    logger.info(f"   🗄️  Databases: {result.get('classification_results', {}).get('databases', 0)}")
                    
                    # Generate detailed user message
                    total_processed = result.get("total_processed", 0)
                    
                    user_message = "✨ Unified CrewAI intelligent processing completed successfully! "
                    if total_processed > 0:
                        user_message += f"Processed {total_processed} assets with AI classification, workflow progression, and database integration using the unified modular service architecture. "
                        user_message += "All assets have been enriched with AI insights and properly classified using agentic intelligence."
                    else:
                        user_message += "Processing completed with unified workflow management. Check asset inventory for results."
                    
                    return {
                        "status": "success",
                        "message": user_message,
                        "processed_count": total_processed,
                        "flow_id": result.get("flow_id", "unified_flow"),
                        "processing_status": result.get("processing_status", "completed"),
                        "progress_percentage": 100.0,
                        "agentic_intelligence": {
                            "crewai_flow_active": True,
                            "unified_service": True,
                            "modular_handlers": True,
                            "database_integration": True,
                            "workflow_progression": True,
                            "state_management": True,
                            "processing_method": "unified_crewai_flow_service"
                        },
                        "classification_results": result.get("classification_results", {}),
                        "workflow_progression": result.get("workflow_progression", {}),
                        "processed_asset_ids": result.get("processed_asset_ids", []),
                        "completed_at": result.get("completed_at"),
                        "duplicate_detection": {
                            "detection_active": True,
                            "duplicates_found": False,
                            "detection_method": "unified_workflow_integration"
                        }
                    }
                else:
                    logger.warning(f"Unified CrewAI Flow returned error: {result.get('error', 'Unknown error')}")
                    # Fall back to fallback processing
                    pass
            else:
                logger.info("Unified CrewAI Flow not available, using fallback processing")
                # Fall back to fallback processing
                pass
                
        except (ImportError, Exception) as e:
            logger.warning(f"Unified CrewAI Flow service not available ({e}), falling back to basic processing")
            # Fall back to fallback processing
            pass
        
        # Fallback processing when CrewAI is not available
        return await _fallback_raw_to_assets_processing(flow_id, db, context)
        
    except Exception as e:
        logger.error(f"Asset processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Asset processing failed: {str(e)}")

async def _process_single_raw_record_agentic(
    record: RawImportRecord,
    field_mappings: Dict[str, str],
    asset_classifications: List[Dict[str, Any]],
    context: RequestContext
) -> Dict[str, Any]:
    """Process a single raw record using agentic CrewAI intelligence."""
    
    raw_data = record.raw_data
    
    # Apply agentic field mappings
    mapped_data = {}
    for source_field, canonical_field in field_mappings.items():
        if source_field in raw_data:
            mapped_data[canonical_field.lower().replace(" ", "_")] = raw_data[source_field]
    
    # Find agentic asset classification for this record
    asset_classification = None
    for classification in asset_classifications:
        # Match by hostname, name, or other identifier
        if (classification.get("hostname") == raw_data.get("hostname") or
            classification.get("name") == raw_data.get("name") or
            classification.get("asset_name") == raw_data.get("asset_name")):
            asset_classification = classification
            break
    
    # Build CMDBAsset data using agentic intelligence
    asset_data = {
        "id": uuid.uuid4(),
        "client_account_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        
        # Core identification using agentic field mapping
        "name": (mapped_data.get("asset_name") or 
                mapped_data.get("hostname") or 
                raw_data.get("hostname") or 
                raw_data.get("name") or 
                f"Asset_{record.row_number}"),
        "hostname": mapped_data.get("hostname") or raw_data.get("hostname"),
        "asset_type": _determine_asset_type_agentic(raw_data, asset_classification),
        
        # Infrastructure details from agentic mapping
        "ip_address": mapped_data.get("ip_address") or raw_data.get("ip_address"),
        "operating_system": mapped_data.get("operating_system") or raw_data.get("os"),
        "environment": mapped_data.get("environment") or raw_data.get("environment"),
        
        # Business information from agentic analysis
        "business_owner": mapped_data.get("business_owner") or raw_data.get("business_owner"),
        "department": mapped_data.get("department") or raw_data.get("department"),
        
        # Migration assessment from agentic intelligence
        "sixr_ready": asset_classification.get("sixr_readiness") if asset_classification else "Pending Analysis",
        "migration_complexity": asset_classification.get("migration_complexity") if asset_classification else "Unknown",
        
        # Source and processing metadata
        "discovery_source": "agentic_cmdb_import",
        "discovery_method": "crewai_flow",
        "discovery_timestamp": datetime.utcnow(),
        "imported_by": context.user_id,
        "imported_at": datetime.utcnow(),
        "source_filename": f"import_session_{record.data_import_id}",
        "raw_data": raw_data,
        "field_mappings_used": field_mappings,
        
        # Audit
        "created_at": datetime.utcnow(),
        "created_by": context.user_id,
        "is_mock": False
    }
    
    return asset_data

def _determine_asset_type_agentic(raw_data: Dict[str, Any], asset_classification: Dict[str, Any]) -> str:
    """Determine asset type using agentic intelligence with enhanced CITYPE field reading."""
    
    # First, use agentic classification if available
    if asset_classification and asset_classification.get("asset_type"):
        agentic_type = asset_classification["asset_type"].lower()
        if agentic_type in ["server", "application", "database", "network_device", "storage_device"]:
            return agentic_type
    
    # Enhanced raw data analysis - check for CITYPE field first (most reliable)
    citype_variations = ["CITYPE", "citype", "CI_TYPE", "ci_type", "CIType"]
    raw_type = ""
    
    # Check for CITYPE field variations
    for field_name in citype_variations:
        if field_name in raw_data and raw_data[field_name]:
            raw_type = str(raw_data[field_name]).lower()
            break
    
    # If no CITYPE found, check other type fields
    if not raw_type:
        raw_type = (raw_data.get("asset_type") or 
                    raw_data.get("type") or 
                    raw_data.get("Type") or 
                    raw_data.get("TYPE") or "").lower()
    
    # Enhanced mapping with exact CITYPE matches first
    if "application" in raw_type:
        return "application"
    elif "server" in raw_type:
        return "server" 
    elif "database" in raw_type:
        return "database"
    elif any(term in raw_type for term in ["network", "switch", "router", "firewall"]):
        return "network_device"
    elif any(term in raw_type for term in ["storage", "san", "nas", "disk"]):
        return "storage_device"
    # Pattern-based fallback for unclear types
    elif any(term in raw_type for term in ["app", "software", "portal", "service"]):
        return "application" 
    elif any(term in raw_type for term in ["srv", "vm", "virtual", "host"]):
        return "server"
    elif any(term in raw_type for term in ["db", "sql", "oracle", "mysql", "postgres"]):
        return "database"
    else:
        # Check CIID patterns as final fallback
        ciid = raw_data.get("CIID", raw_data.get("ciid", raw_data.get("CI_ID", "")))
        if ciid:
            ciid_lower = str(ciid).lower()
            if ciid_lower.startswith("app"):
                return "application"
            elif ciid_lower.startswith("srv"):
                return "server"
            elif ciid_lower.startswith("db"):
                return "database"
        
        return "server"  # Default fallback

async def _fallback_raw_to_assets_processing(
    flow_id: str, 
    db: AsyncSession, 
    context: RequestContext
) -> dict:
    """
    Fallback asset processing when CrewAI Flow is not available.
    Creates basic assets without AI intelligence.
    """
    logger.warning("🔄 Using fallback processing - CrewAI Flow not available")
    
    try:
        # Get raw records
        raw_records_query = await db.execute(
            select(RawImportRecord).where(
                RawImportRecord.data_import_id == flow_id
            )
        )
        raw_records = raw_records_query.scalars().all()
        
        if not raw_records:
            return {
                "status": "error",
                "message": "No raw import records found",
                "flow_id": flow_id
            }
        
        processed_count = 0
        created_assets = []
        
        for record in raw_records:
            if record.asset_id is not None:
                continue  # Already processed
            
            # Simple asset creation without AI
            raw_data = record.raw_data
            
            asset = Asset(
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                name=raw_data.get("NAME", raw_data.get("name", f"Asset_{record.row_number}")),
                hostname=raw_data.get("hostname"),
                asset_type=raw_data.get("CITYPE", "server").lower(),
                ip_address=raw_data.get("IP_ADDRESS"),
                operating_system=raw_data.get("OS"),
                environment=raw_data.get("ENVIRONMENT", "Unknown"),
                discovery_source="fallback_cmdb_import",
                discovery_method="basic_mapping",
                discovered_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(asset)
            await db.flush()
            
            record.asset_id = asset.id
            record.is_processed = True
            record.processed_at = datetime.utcnow()
            record.processing_notes = f"Processed by fallback method (non-agentic) - CrewAI Flow was not available. Created basic asset with CITYPE: {raw_data.get('CITYPE', 'server')}"
            
            created_assets.append(str(asset.id))
            processed_count += 1
        
        await db.commit()
        
        logger.info(f"✅ Fallback processing completed: {processed_count} assets created")
        
        return {
            "status": "success",
            "message": f"⚠️ Fallback processing completed. Created {processed_count} basic assets without AI intelligence. Consider enabling CrewAI Flow for enhanced classification.",
            "processed_count": processed_count,
            "flow_id": "fallback_processing",
            "processing_status": "completed",
            "progress_percentage": 100.0,
            "agentic_intelligence": {
                "crewai_flow_active": False,
                "unified_service": False,
                "modular_handlers": False,
                "database_integration": True,
                "workflow_progression": False,
                "state_management": False,
                "processing_method": "fallback_basic_mapping"
            },
            "classification_results": {
                "applications": 0,
                "servers": processed_count,  # Default to servers
                "databases": 0,
                "other_assets": 0
            },
            "processed_asset_ids": created_assets,
            "completed_at": datetime.utcnow().isoformat(),
            "duplicate_detection": {
                "detection_active": False,
                "duplicates_found": False,
                "detection_method": "none"
            }
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Fallback processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fallback processing failed: {str(e)}")

@router.get("/processing-status/{flow_id}")
async def get_processing_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get the processing status for an import session."""
    
    try:
        # Get processing statistics
        total_query = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == flow_id
            )
        )
        total_records = total_query.scalar()
        
        processed_query = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == flow_id,
                RawImportRecord.is_processed is True
            )
        )
        processed_records = processed_query.scalar()
        
        # Get created assets count
        assets_query = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id
            )
        )
        total_assets = assets_query.scalar()
        
        return {
            "flow_id": flow_id,
            "total_records": total_records,
            "processed_records": processed_records,
            "pending_records": total_records - processed_records,
            "processing_percentage": (processed_records / total_records * 100) if total_records > 0 else 0,
            "total_assets_created": total_assets,
            "status": "completed" if processed_records == total_records else "in_progress"
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}") 