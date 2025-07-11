"""
Import Response Builder Module

Handles response formatting including:
- Response formatting and standardization
- Success/error response construction
- Data transformation for API responses
- Status message generation
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class ImportStorageResponse(BaseModel):
    """Response model for import storage operations."""
    success: bool
    data_import_id: Optional[str] = None
    flow_id: Optional[str] = None
    error: Optional[str] = None
    message: str
    records_stored: int = 0


class ImportResponseBuilder:
    """
    Builds standardized responses for import operations.
    """
    
    def __init__(self):
        pass
    
    def success_response(
        self,
        data_import_id: str,
        flow_id: Optional[str] = None,
        records_stored: int = 0,
        message: Optional[str] = None
    ) -> ImportStorageResponse:
        """
        Build a successful import response.
        
        Args:
            data_import_id: ID of the data import
            flow_id: ID of the created flow (if any)
            records_stored: Number of records stored
            message: Success message
            
        Returns:
            ImportStorageResponse: Formatted success response
        """
        if not message:
            if flow_id:
                message = f"Successfully stored {records_stored} records and initiated Discovery Flow"
            else:
                message = f"Successfully stored {records_stored} records"
        
        logger.info(f"✅ Building success response: {message}")
        
        return ImportStorageResponse(
            success=True,
            data_import_id=data_import_id,
            flow_id=flow_id,
            message=message,
            records_stored=records_stored
        )
    
    def error_response(
        self,
        error_message: str,
        data_import_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        records_stored: int = 0
    ) -> ImportStorageResponse:
        """
        Build an error response.
        
        Args:
            error_message: Error message to include
            data_import_id: ID of the data import (if any)
            flow_id: ID of the flow (if any)
            records_stored: Number of records stored before error
            
        Returns:
            ImportStorageResponse: Formatted error response
        """
        logger.error(f"❌ Building error response: {error_message}")
        
        return ImportStorageResponse(
            success=False,
            data_import_id=data_import_id,
            flow_id=flow_id,
            error=error_message,
            message=f"Import failed: {error_message}",
            records_stored=records_stored
        )
    
    def partial_success_response(
        self,
        data_import_id: str,
        records_stored: int,
        flow_error: str,
        flow_id: Optional[str] = None
    ) -> ImportStorageResponse:
        """
        Build a partial success response (data stored but flow failed).
        
        Args:
            data_import_id: ID of the data import
            records_stored: Number of records stored
            flow_error: Error message for flow failure
            flow_id: ID of the flow (if any)
            
        Returns:
            ImportStorageResponse: Formatted partial success response
        """
        message = f"Data stored ({records_stored} records) but Discovery Flow failed: {flow_error}"
        
        logger.warning(f"⚠️ Building partial success response: {message}")
        
        return ImportStorageResponse(
            success=False,  # Overall operation failed due to flow failure
            data_import_id=data_import_id,
            flow_id=flow_id,
            error=flow_error,
            message=message,
            records_stored=records_stored
        )
    
    def validation_error_response(
        self,
        validation_message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a validation error response.
        
        Args:
            validation_message: Validation error message
            field: Field that failed validation
            details: Additional validation details
            
        Returns:
            Dict: Formatted validation error response
        """
        logger.error(f"❌ Building validation error response: {validation_message}")
        
        response = {
            "success": False,
            "error": "validation_error",
            "message": validation_message,
            "data_import_id": None,
            "flow_id": None,
            "records_stored": 0
        }
        
        if field:
            response["field"] = field
        
        if details:
            response["details"] = details
        
        return response
    
    def conflict_response(
        self,
        conflict_message: str,
        existing_flow: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build a conflict response (e.g., incomplete flow exists).
        
        Args:
            conflict_message: Conflict message
            existing_flow: Information about the existing flow
            recommendations: List of recommendations
            
        Returns:
            Dict: Formatted conflict response
        """
        logger.warning(f"⚠️ Building conflict response: {conflict_message}")
        
        response = {
            "success": False,
            "error": "conflict",
            "message": conflict_message,
            "data_import_id": None,
            "flow_id": None,
            "records_stored": 0
        }
        
        if existing_flow:
            response["existing_flow"] = existing_flow
        
        if recommendations:
            response["recommendations"] = recommendations
        
        return response
    
    def progress_response(
        self,
        flow_id: str,
        current_phase: str,
        progress_percentage: float,
        message: str,
        data_import_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a progress response for ongoing operations.
        
        Args:
            flow_id: ID of the flow
            current_phase: Current phase of the operation
            progress_percentage: Progress percentage (0-100)
            message: Progress message
            data_import_id: ID of the data import
            
        Returns:
            Dict: Formatted progress response
        """
        logger.info(f"🔄 Building progress response: {current_phase} - {progress_percentage}%")
        
        return {
            "success": True,
            "flow_id": flow_id,
            "data_import_id": data_import_id,
            "status": "in_progress",
            "current_phase": current_phase,
            "progress_percentage": progress_percentage,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def completion_response(
        self,
        flow_id: str,
        data_import_id: str,
        final_status: str,
        completion_message: str,
        summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a completion response for finished operations.
        
        Args:
            flow_id: ID of the flow
            data_import_id: ID of the data import
            final_status: Final status of the operation
            completion_message: Completion message
            summary: Summary of the operation
            
        Returns:
            Dict: Formatted completion response
        """
        logger.info(f"🎯 Building completion response: {final_status}")
        
        response = {
            "success": final_status in ["completed", "success"],
            "flow_id": flow_id,
            "data_import_id": data_import_id,
            "status": final_status,
            "message": completion_message,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        if summary:
            response["summary"] = summary
        
        return response
    
    def status_response(
        self,
        flow_id: str,
        status: str,
        phase_data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a status response for flow queries.
        
        Args:
            flow_id: ID of the flow
            status: Current status
            phase_data: Phase data
            message: Status message
            
        Returns:
            Dict: Formatted status response
        """
        logger.info(f"📊 Building status response: {status}")
        
        response = {
            "success": True,
            "flow_id": flow_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if message:
            response["message"] = message
        
        if phase_data:
            response["phase_data"] = phase_data
        
        return response
    
    def format_import_metadata(
        self,
        data_import,
        records_count: int,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format import metadata for response.
        
        Args:
            data_import: DataImport object
            records_count: Number of records
            additional_info: Additional metadata
            
        Returns:
            Dict: Formatted metadata
        """
        metadata = {
            "filename": data_import.filename or "Unknown",
            "import_type": data_import.import_type,
            "imported_at": data_import.completed_at.isoformat() if data_import.completed_at else None,
            "total_records": records_count,
            "import_id": str(data_import.id),
            "client_account_id": str(data_import.client_account_id),
            "engagement_id": str(data_import.engagement_id),
            "status": data_import.status
        }
        
        if additional_info:
            metadata.update(additional_info)
        
        return metadata
    
    def format_performance_metrics(
        self,
        start_time: datetime,
        records_processed: int,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format performance metrics for response.
        
        Args:
            start_time: Start time of the operation
            records_processed: Number of records processed
            additional_metrics: Additional metrics
            
        Returns:
            Dict: Formatted performance metrics
        """
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        metrics = {
            "response_time_ms": duration * 1000,
            "records_processed": records_processed,
            "records_per_second": records_processed / duration if duration > 0 else 0,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        if additional_metrics:
            metrics.update(additional_metrics)
        
        return metrics