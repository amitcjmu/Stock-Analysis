"""
V3 Data Import Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.v3.data_import import V3DataImportRepository
from app.repositories.v3.discovery_flow import V3DiscoveryFlowRepository
from app.repositories.v3.field_mapping import V3FieldMappingRepository
from app.models import DataImport, DiscoveryFlow
from app.models.data_import.enums import ImportStatus
from app.repositories.v3.discovery_flow import FlowStatus
from app.core.context import get_current_context
import logging
import uuid

logger = logging.getLogger(__name__)

class V3DataImportService:
    """Service for V3 data import operations"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        self.db = db
        
        # Get context if not provided
        if not client_account_id or not engagement_id:
            try:
                context = get_current_context()
                client_account_id = client_account_id or str(context.client_account_id)
                engagement_id = engagement_id or str(context.engagement_id)
            except:
                # Default fallback if context not available
                client_account_id = client_account_id or str(uuid.uuid4())
                engagement_id = engagement_id or str(uuid.uuid4())
        
        self.import_repo = V3DataImportRepository(db, client_account_id, engagement_id)
        self.flow_repo = V3DiscoveryFlowRepository(db, client_account_id, engagement_id)
        self.mapping_repo = V3FieldMappingRepository(db, client_account_id, engagement_id)
    
    async def create_import(
        self,
        filename: str,
        file_data: bytes,
        source_system: Optional[str] = None
    ) -> DataImport:
        """Create new data import"""
        try:
            # Create import record
            import_data = {
                "filename": filename,
                "file_size": len(file_data),
                "mime_type": self._detect_mime_type(filename),
                "source_system": source_system or "unknown",
                "status": ImportStatus.PENDING
            }
            
            data_import = await self.import_repo.create(import_data)
            
            # Create associated discovery flow
            flow_data = {
                "data_import_id": data_import.id,
                "flow_name": f"Discovery for {filename}",
                "status": FlowStatus.INITIALIZING
            }
            
            discovery_flow = await self.flow_repo.create(flow_data)
            
            logger.info(f"Created import {data_import.id} with flow {discovery_flow.id}")
            
            return data_import
            
        except Exception as e:
            logger.error(f"Failed to create import: {e}")
            raise
    
    async def get_import_with_flow(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get import with associated flow"""
        data_import = await self.import_repo.get_by_id(import_id)
        if not data_import:
            return None
        
        flow = await self.flow_repo.get_by_import_id(import_id)
        mappings = await self.mapping_repo.get_by_import(import_id)
        
        return {
            "import": data_import,
            "flow": flow,
            "mappings": mappings
        }
    
    async def process_import_data(
        self,
        import_id: str,
        records: List[Dict[str, Any]]
    ) -> bool:
        """Process imported records"""
        try:
            # Update import status
            await self.import_repo.update(
                import_id,
                {
                    "status": ImportStatus.PROCESSING,
                    "total_records": len(records)
                }
            )
            
            # Store raw records (implement raw records repository if needed)
            # await self._store_raw_records(import_id, records)
            
            # Trigger discovery flow
            flow = await self.flow_repo.get_by_import_id(import_id)
            if flow:
                await self.flow_repo.update_flow_state(
                    str(flow.id),
                    "data_validation",
                    {"records_received": len(records)},
                    10.0
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process import: {e}")
            await self.import_repo.fail_import(
                import_id,
                str(e),
                {"error_type": "processing_error", "record_count": len(records)}
            )
            return False
    
    async def complete_import(
        self,
        import_id: str,
        processed_count: int,
        failed_count: int = 0
    ) -> bool:
        """Mark import as completed"""
        try:
            success = await self.import_repo.complete_import(
                import_id,
                processed_count,
                failed_count
            )
            
            if success:
                # Also update the associated flow
                flow = await self.flow_repo.get_by_import_id(import_id)
                if flow:
                    await self.flow_repo.update_flow_state(
                        str(flow.id),
                        "import_completed",
                        {
                            "processed_records": processed_count,
                            "failed_records": failed_count
                        },
                        25.0
                    )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to complete import: {e}")
            return False
    
    async def get_import_statistics(self, import_id: str) -> Dict[str, Any]:
        """Get comprehensive import statistics"""
        data_import = await self.import_repo.get_by_id(import_id)
        if not data_import:
            return {}
        
        mapping_stats = await self.mapping_repo.get_mapping_statistics(import_id)
        
        return {
            "import_id": str(data_import.id),
            "filename": data_import.filename,
            "status": data_import.status,
            "total_records": data_import.total_records,
            "processed_records": data_import.processed_records,
            "failed_records": data_import.failed_records,
            "processing_rate": (
                data_import.processed_records / data_import.total_records
                if data_import.total_records > 0 else 0.0
            ),
            "mapping_statistics": mapping_stats,
            "created_at": data_import.created_at.isoformat() if data_import.created_at else None,
            "completed_at": data_import.completed_at.isoformat() if data_import.completed_at else None
        }
    
    async def list_imports(
        self,
        status_filter: Optional[ImportStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List imports with optional filtering"""
        if status_filter:
            imports = await self.import_repo.get_by_status(status_filter)
        else:
            imports = await self.import_repo.list_all(limit=limit, offset=offset)
        
        return [
            {
                "import_id": str(imp.id),
                "filename": imp.filename,
                "status": imp.status,
                "total_records": imp.total_records,
                "processed_records": imp.processed_records,
                "created_at": imp.created_at.isoformat() if imp.created_at else None
            }
            for imp in imports
        ]
    
    async def delete_import(self, import_id: str, cascade: bool = False) -> bool:
        """Delete import and optionally associated data"""
        try:
            if cascade:
                # Delete associated flow
                flow = await self.flow_repo.get_by_import_id(import_id)
                if flow:
                    await self.flow_repo.delete(str(flow.id))
                
                # Delete associated mappings
                mappings = await self.mapping_repo.get_by_import(import_id)
                for mapping in mappings:
                    await self.mapping_repo.delete(str(mapping.id))
            
            # Delete the import
            success = await self.import_repo.delete(import_id)
            
            if success:
                logger.info(f"Deleted import {import_id} (cascade={cascade})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete import {import_id}: {e}")
            return False
    
    def _detect_mime_type(self, filename: str) -> str:
        """Detect MIME type from filename"""
        if filename.endswith('.csv'):
            return 'text/csv'
        elif filename.endswith('.json'):
            return 'application/json'
        elif filename.endswith('.xlsx'):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return 'application/octet-stream'