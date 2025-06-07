"""
Asset Processing Module - Asset creation and processing workflows.
Handles raw data to asset conversion, CrewAI integration, and agentic processing.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
import logging

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import RawImportRecord
from app.models.asset import Asset

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process-raw-to-assets")
async def process_raw_to_assets(
    import_session_id: str = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    CrewAI Flow endpoint to process raw import records into assets using agentic intelligence.
    Now uses proper CrewAI Flow state management pattern for complete application and server classification.
    """
    try:
        logger.info(f"🚀 Starting enhanced CrewAI Flow processing with state management for session: {import_session_id}")
        
        # Use the new CrewAI Flow Data Processing Service with proper state management
        try:
            from app.services.crewai_flow_data_processing import CrewAIFlowDataProcessingService
            flow_service = CrewAIFlowDataProcessingService()
            
            # Process using CrewAI Flow with state management
            result = await flow_service.process_import_session(
                import_session_id=import_session_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                user_id=context.user_id
            )
            
            # Enhanced response with detailed classification results
            if result.get("status") == "success":
                logger.info(f"✅ CrewAI Flow completed successfully!")
                logger.info(f"   📊 Processing Status: {result.get('processing_status')}")
                logger.info(f"   📱 Applications: {result.get('classification_results', {}).get('applications', 0)}")
                logger.info(f"   🖥️  Servers: {result.get('classification_results', {}).get('servers', 0)}")
                logger.info(f"   🗄️  Databases: {result.get('classification_results', {}).get('databases', 0)}")
                logger.info(f"   🔗 Dependencies: {result.get('classification_results', {}).get('dependencies', 0)}")
                
                return {
                    "status": "success",
                    "message": f"CrewAI Flow successfully processed {result.get('total_processed', 0)} assets with intelligent classification",
                    "processed_count": result.get("total_processed", 0),
                    "flow_id": result.get("flow_id"),
                    "processing_status": result.get("processing_status"),
                    "progress_percentage": result.get("progress_percentage", 100),
                    "agentic_intelligence": {
                        "crewai_flow_active": result.get("crewai_flow_used", False),
                        "state_management": True,
                        "intelligent_classification": True,
                        "asset_breakdown": result.get("classification_results", {}),
                        "field_mappings_applied": len(result.get("field_mappings", {})),
                        "processing_method": "crewai_flow_with_state_management"
                    },
                    "classification_results": result.get("classification_results", {}),
                    "processed_asset_ids": result.get("processed_asset_ids", []),
                    "processing_errors": result.get("processing_errors", []),
                    "import_session_id": import_session_id,
                    "completed_at": result.get("completed_at")
                }
            else:
                logger.warning(f"CrewAI Flow returned error, falling back: {result.get('error', 'Unknown error')}")
                return await _fallback_raw_to_assets_processing(import_session_id, db, context)
                
        except ImportError as e:
            logger.warning(f"CrewAI Flow Data Processing service not available: {e}")
            return await _fallback_raw_to_assets_processing(import_session_id, db, context)
        
    except Exception as e:
        logger.error(f"Error in enhanced CrewAI Flow processing: {e}")
        # Fallback to non-agentic processing
        return await _fallback_raw_to_assets_processing(import_session_id, db, context)

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
    import_session_id: str,
    db: AsyncSession,
    context: RequestContext
) -> Dict[str, Any]:
    """Fallback processing when CrewAI Flow is not available."""
    
    logger.info("🔄 Using fallback processing (non-agentic) for raw import records")
    
    # Get unprocessed raw records
    if import_session_id:
        raw_records_query = await db.execute(
            select(RawImportRecord).where(
                and_(
                    RawImportRecord.data_import_id == import_session_id,
                    RawImportRecord.asset_id.is_(None)
                )
            )
        )
    else:
        raw_records_query = await db.execute(
            select(RawImportRecord).where(
                RawImportRecord.asset_id.is_(None)
            )
        )
    
    raw_records = raw_records_query.scalars().all()
    
    if not raw_records:
        return {
            "status": "no_data",
            "message": "No unprocessed raw import records found",
            "processed_count": 0
        }
    
    # Simple processing without agentic intelligence
    processed_count = 0
    for record in raw_records:
        try:
            raw_data = record.raw_data
            
            # Basic field mapping
            asset_data = {
                "id": uuid.uuid4(),
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "name": (raw_data.get("hostname") or 
                        raw_data.get("name") or 
                        raw_data.get("asset_name") or
                        f"Asset_{record.row_number}"),
                "hostname": raw_data.get("hostname"),
                "asset_type": _determine_asset_type_agentic(raw_data, None),
                "ip_address": raw_data.get("ip_address"),
                "operating_system": raw_data.get("os") or raw_data.get("operating_system"),
                "environment": raw_data.get("environment"),
                "business_owner": raw_data.get("business_owner"),
                "department": raw_data.get("department"),
                "discovery_source": "fallback_cmdb_import",
                "discovery_method": "basic_mapping",
                "discovery_timestamp": datetime.utcnow(),
                "imported_by": context.user_id,
                "imported_at": datetime.utcnow(),
                "source_filename": f"import_session_{record.data_import_id}",
                "raw_data": raw_data,
                "created_at": datetime.utcnow(),
                "created_by": context.user_id,
                "is_mock": False
            }
            
            # Create Asset
            asset = Asset(**asset_data)
            db.add(asset)
            await db.flush()
            
            # Update raw record
            record.asset_id = asset.id
            record.is_processed = True
            record.processed_at = datetime.utcnow()
            record.processing_notes = "Processed by fallback method (non-agentic)"
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error in fallback processing for record {record.id}: {e}")
            continue
    
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Fallback processing completed: {processed_count} assets created",
        "processed_count": processed_count,
        "total_raw_records": len(raw_records),
        "agentic_intelligence": False,
        "import_session_id": import_session_id
    } 