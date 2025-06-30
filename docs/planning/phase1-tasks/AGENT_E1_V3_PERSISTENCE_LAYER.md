# Phase 1.5 - Agent E1: V3 API Persistence Layer Implementation

## Critical Context
**This is an URGENT blocking task**. The V3 APIs created in Phase 1 are currently just facades with no persistence. The frontend is built for V3 APIs but they don't save any data. This task implements the missing persistence layer.

### Problem Statement
- V3 APIs exist but have no database models or persistence
- All V3 endpoints return mock data when services fail
- Data is lost on server restart
- Frontend cannot retrieve previously saved data

### Prerequisites
- V3 API routes already created (✓ from AGENT_B1)
- PostgreSQL state management ready (✓ from AGENT_D1)
- Understanding of existing V1/V2 models

## Your Specific Tasks

### 1. Create V3 Database Models
**File to create**: `backend/app/models/v3/__init__.py`

```python
"""
V3 Database Models for unified API
"""

from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer, Float, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid
from datetime import datetime
import enum

class FlowStatus(str, enum.Enum):
    """Flow execution status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ImportStatus(str, enum.Enum):
    """Data import status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MappingStatus(str, enum.Enum):
    """Field mapping status"""
    SUGGESTED = "suggested"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"

class V3DataImport(Base):
    """V3 unified data import model"""
    __tablename__ = "v3_data_imports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Import metadata
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    source_system = Column(String)
    
    # Status tracking
    status = Column(Enum(ImportStatus), default=ImportStatus.PENDING)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Error tracking
    error_message = Column(String)
    error_details = Column(JSON)
    
    # Relationships
    discovery_flow = relationship("V3DiscoveryFlow", back_populates="data_import", uselist=False)
    raw_records = relationship("V3RawImportRecord", back_populates="data_import")
    field_mappings = relationship("V3FieldMapping", back_populates="data_import")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_imports_client_status', 'client_account_id', 'status'),
        Index('idx_v3_imports_created', 'created_at'),
    )

class V3DiscoveryFlow(Base):
    """V3 unified discovery flow model"""
    __tablename__ = "v3_discovery_flows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Flow identification
    flow_name = Column(String)
    flow_type = Column(String, default="unified_discovery")
    
    # Import reference
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("v3_data_imports.id"))
    
    # Status tracking
    status = Column(Enum(FlowStatus), default=FlowStatus.INITIALIZING)
    current_phase = Column(String)
    phases_completed = Column(JSON, default=list)
    progress_percentage = Column(Float, default=0.0)
    
    # Flow state
    flow_state = Column(JSON, default=dict)
    crew_outputs = Column(JSON, default=dict)
    
    # Results storage
    field_mappings = Column(JSON)
    discovered_assets = Column(JSON)
    dependencies = Column(JSON)
    tech_debt_analysis = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Error tracking
    error_message = Column(String)
    error_phase = Column(String)
    error_details = Column(JSON)
    
    # Relationships
    data_import = relationship("V3DataImport", back_populates="discovery_flow")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_flows_client_status', 'client_account_id', 'status'),
        Index('idx_v3_flows_import', 'data_import_id'),
    )

class V3RawImportRecord(Base):
    """V3 raw import records"""
    __tablename__ = "v3_raw_import_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("v3_data_imports.id"), nullable=False)
    
    # Record data
    record_index = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    is_valid = Column(Boolean)
    validation_errors = Column(JSON)
    
    # Cleansed data
    cleansed_data = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    data_import = relationship("V3DataImport", back_populates="raw_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_records_import', 'data_import_id'),
        Index('idx_v3_records_processed', 'is_processed'),
    )

class V3FieldMapping(Base):
    """V3 field mappings"""
    __tablename__ = "v3_field_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("v3_data_imports.id"), nullable=False)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Mapping definition
    source_field = Column(String, nullable=False)
    target_field = Column(String, nullable=False)
    
    # AI suggestions
    confidence_score = Column(Float)
    match_type = Column(String)  # exact, fuzzy, semantic
    suggested_by = Column(String, default="ai_agent")
    
    # User actions
    status = Column(Enum(MappingStatus), default=MappingStatus.SUGGESTED)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    
    # Transformation rules
    transformation_rules = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    data_import = relationship("V3DataImport", back_populates="field_mappings")
    
    # Indexes
    __table_args__ = (
        Index('idx_v3_mappings_import', 'data_import_id'),
        Index('idx_v3_mappings_source', 'source_field'),
        Index('idx_v3_mappings_status', 'status'),
    )
```

### 2. Create V3 Repository Layer
**File to create**: `backend/app/repositories/v3/base.py`

```python
"""
V3 Repository base classes
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.core.context_aware import ContextAwareRepository
from app.models.v3 import V3DataImport, V3DiscoveryFlow, V3FieldMapping, V3RawImportRecord
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class V3BaseRepository(ContextAwareRepository, Generic[T]):
    """Base repository for V3 models with context awareness"""
    
    def __init__(self, db: AsyncSession, model_class: T):
        """Initialize with session and model"""
        super().__init__(db, model_class)
        self.model_class = model_class
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create entity with context fields"""
        # Add context fields
        data = self.set_context_fields(data)
        
        # Create instance
        instance = self.model_class(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        
        return instance
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update entity with context validation"""
        # Get existing entity
        entity = await self.get_by_id(id)
        if not entity:
            return None
        
        # Update fields
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        await self.db.commit()
        await self.db.refresh(entity)
        
        return entity
    
    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Bulk create with context"""
        instances = []
        for item_data in items:
            data = self.set_context_fields(item_data)
            instance = self.model_class(**data)
            self.db.add(instance)
            instances.append(instance)
        
        await self.db.commit()
        
        # Refresh all instances
        for instance in instances:
            await self.db.refresh(instance)
        
        return instances
```

**File to create**: `backend/app/repositories/v3/data_import.py`

```python
"""
V3 Data Import Repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.v3.base import V3BaseRepository
from app.models.v3 import V3DataImport, ImportStatus
import logging

logger = logging.getLogger(__name__)

class V3DataImportRepository(V3BaseRepository[V3DataImport]):
    """Repository for V3 data imports"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, V3DataImport)
    
    async def get_by_status(self, status: ImportStatus) -> List[V3DataImport]:
        """Get imports by status"""
        query = select(V3DataImport).where(
            V3DataImport.status == status
        )
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_progress(
        self, 
        import_id: str,
        processed: int,
        failed: int = 0
    ) -> bool:
        """Update import progress"""
        query = update(V3DataImport).where(
            and_(
                V3DataImport.id == import_id,
                V3DataImport.client_account_id == self.context.client_account_id
            )
        ).values(
            processed_records=processed,
            failed_records=failed,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def complete_import(
        self,
        import_id: str,
        total_processed: int,
        total_failed: int
    ) -> bool:
        """Mark import as completed"""
        query = update(V3DataImport).where(
            and_(
                V3DataImport.id == import_id,
                V3DataImport.client_account_id == self.context.client_account_id
            )
        ).values(
            status=ImportStatus.COMPLETED,
            processed_records=total_processed,
            failed_records=total_failed,
            completed_at=func.now(),
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
```

**File to create**: `backend/app/repositories/v3/discovery_flow.py`

```python
"""
V3 Discovery Flow Repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.v3.base import V3BaseRepository
from app.models.v3 import V3DiscoveryFlow, FlowStatus
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class V3DiscoveryFlowRepository(V3BaseRepository[V3DiscoveryFlow]):
    """Repository for V3 discovery flows"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, V3DiscoveryFlow)
    
    async def get_active_flows(self) -> List[V3DiscoveryFlow]:
        """Get all active flows"""
        query = select(V3DiscoveryFlow).where(
            V3DiscoveryFlow.status.in_([
                FlowStatus.INITIALIZING,
                FlowStatus.RUNNING,
                FlowStatus.PAUSED
            ])
        )
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_import_id(self, import_id: str) -> Optional[V3DiscoveryFlow]:
        """Get flow by import ID"""
        query = select(V3DiscoveryFlow).where(
            V3DiscoveryFlow.data_import_id == import_id
        )
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_flow_state(
        self,
        flow_id: str,
        phase: str,
        state: Dict[str, Any],
        progress: float
    ) -> bool:
        """Update flow state and progress"""
        # Get current flow
        flow = await self.get_by_id(flow_id)
        if not flow:
            return False
        
        # Update phases completed
        phases_completed = flow.phases_completed or []
        if phase not in phases_completed and phase != flow.current_phase:
            phases_completed.append(flow.current_phase)
        
        # Update flow
        query = update(V3DiscoveryFlow).where(
            and_(
                V3DiscoveryFlow.id == flow_id,
                V3DiscoveryFlow.client_account_id == self.context.client_account_id
            )
        ).values(
            current_phase=phase,
            phases_completed=phases_completed,
            flow_state=state,
            progress_percentage=progress,
            status=FlowStatus.RUNNING,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def complete_flow(
        self,
        flow_id: str,
        final_state: Dict[str, Any]
    ) -> bool:
        """Mark flow as completed"""
        query = update(V3DiscoveryFlow).where(
            and_(
                V3DiscoveryFlow.id == flow_id,
                V3DiscoveryFlow.client_account_id == self.context.client_account_id
            )
        ).values(
            status=FlowStatus.COMPLETED,
            flow_state=final_state,
            progress_percentage=100.0,
            completed_at=func.now(),
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def fail_flow(
        self,
        flow_id: str,
        error_message: str,
        error_phase: str,
        error_details: Dict[str, Any]
    ) -> bool:
        """Mark flow as failed"""
        query = update(V3DiscoveryFlow).where(
            and_(
                V3DiscoveryFlow.id == flow_id,
                V3DiscoveryFlow.client_account_id == self.context.client_account_id
            )
        ).values(
            status=FlowStatus.FAILED,
            error_message=error_message,
            error_phase=error_phase,
            error_details=error_details,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
```

**File to create**: `backend/app/repositories/v3/field_mapping.py`

```python
"""
V3 Field Mapping Repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.v3.base import V3BaseRepository
from app.models.v3 import V3FieldMapping, MappingStatus
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class V3FieldMappingRepository(V3BaseRepository[V3FieldMapping]):
    """Repository for V3 field mappings"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, V3FieldMapping)
    
    async def get_by_import(self, import_id: str) -> List[V3FieldMapping]:
        """Get all mappings for an import"""
        query = select(V3FieldMapping).where(
            V3FieldMapping.data_import_id == import_id
        )
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_source_field(
        self,
        import_id: str,
        source_field: str
    ) -> Optional[V3FieldMapping]:
        """Get mapping by source field"""
        query = select(V3FieldMapping).where(
            and_(
                V3FieldMapping.data_import_id == import_id,
                V3FieldMapping.source_field == source_field
            )
        )
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def approve_mapping(
        self,
        mapping_id: str,
        approved_by: str
    ) -> bool:
        """Approve a field mapping"""
        query = update(V3FieldMapping).where(
            and_(
                V3FieldMapping.id == mapping_id,
                V3FieldMapping.client_account_id == self.context.client_account_id
            )
        ).values(
            status=MappingStatus.APPROVED,
            approved_by=approved_by,
            approved_at=func.now(),
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def reject_mapping(
        self,
        mapping_id: str,
        rejected_by: str
    ) -> bool:
        """Reject a field mapping"""
        query = update(V3FieldMapping).where(
            and_(
                V3FieldMapping.id == mapping_id,
                V3FieldMapping.client_account_id == self.context.client_account_id
            )
        ).values(
            status=MappingStatus.REJECTED,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def update_mapping(
        self,
        mapping_id: str,
        target_field: str,
        transformation_rules: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update mapping target and rules"""
        values = {
            "target_field": target_field,
            "status": MappingStatus.MODIFIED,
            "updated_at": func.now()
        }
        
        if transformation_rules:
            values["transformation_rules"] = transformation_rules
        
        query = update(V3FieldMapping).where(
            and_(
                V3FieldMapping.id == mapping_id,
                V3FieldMapping.client_account_id == self.context.client_account_id
            )
        ).values(**values)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def bulk_create_mappings(
        self,
        import_id: str,
        mappings: List[Dict[str, Any]]
    ) -> List[V3FieldMapping]:
        """Create multiple mappings at once"""
        # Add import_id to all mappings
        for mapping in mappings:
            mapping["data_import_id"] = import_id
        
        return await self.bulk_create(mappings)
```

### 3. Create V3 Service Layer
**File to create**: `backend/app/services/v3/data_import_service.py`

```python
"""
V3 Data Import Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.v3.data_import import V3DataImportRepository
from app.repositories.v3.discovery_flow import V3DiscoveryFlowRepository
from app.repositories.v3.field_mapping import V3FieldMappingRepository
from app.models.v3 import V3DataImport, V3DiscoveryFlow, ImportStatus, FlowStatus
from app.core.context import get_current_context
import logging
import uuid

logger = logging.getLogger(__name__)

class V3DataImportService:
    """Service for V3 data import operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.import_repo = V3DataImportRepository(db)
        self.flow_repo = V3DiscoveryFlowRepository(db)
        self.mapping_repo = V3FieldMappingRepository(db)
    
    async def create_import(
        self,
        filename: str,
        file_data: bytes,
        source_system: Optional[str] = None
    ) -> V3DataImport:
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
        
        return {
            "import": data_import,
            "flow": flow,
            "mappings": await self.mapping_repo.get_by_import(import_id)
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
            
            # Store raw records (implement in next step)
            # await self._store_raw_records(import_id, records)
            
            # Trigger discovery flow
            flow = await self.flow_repo.get_by_import_id(import_id)
            if flow:
                await self.flow_repo.update_flow_state(
                    flow.id,
                    "data_validation",
                    {"records_received": len(records)},
                    10.0
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process import: {e}")
            await self.import_repo.update(
                import_id,
                {
                    "status": ImportStatus.FAILED,
                    "error_message": str(e)
                }
            )
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
```

**File to create**: `backend/app/services/v3/discovery_flow_service.py`

```python
"""
V3 Discovery Flow Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.v3.discovery_flow import V3DiscoveryFlowRepository
from app.repositories.v3.field_mapping import V3FieldMappingRepository
from app.models.v3 import V3DiscoveryFlow, FlowStatus
from app.services.flows.manager import flow_manager
import logging

logger = logging.getLogger(__name__)

class V3DiscoveryFlowService:
    """Service for V3 discovery flow operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.flow_repo = V3DiscoveryFlowRepository(db)
        self.mapping_repo = V3FieldMappingRepository(db)
    
    async def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive flow status"""
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            return None
        
        # Get field mappings if available
        mappings = None
        if flow.data_import_id:
            mappings = await self.mapping_repo.get_by_import(flow.data_import_id)
        
        return {
            "flow_id": str(flow.id),
            "status": flow.status,
            "current_phase": flow.current_phase,
            "phases_completed": flow.phases_completed or [],
            "progress_percentage": flow.progress_percentage,
            "data_import_id": str(flow.data_import_id) if flow.data_import_id else None,
            "field_mappings": self._serialize_mappings(mappings) if mappings else None,
            "discovered_assets": flow.discovered_assets,
            "dependencies": flow.dependencies,
            "tech_debt_analysis": flow.tech_debt_analysis,
            "error": {
                "message": flow.error_message,
                "phase": flow.error_phase,
                "details": flow.error_details
            } if flow.error_message else None,
            "created_at": flow.created_at.isoformat() if flow.created_at else None,
            "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
        }
    
    async def continue_flow(self, flow_id: str) -> bool:
        """Continue a paused or failed flow"""
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            return False
        
        if flow.status not in [FlowStatus.PAUSED, FlowStatus.FAILED]:
            logger.warning(f"Cannot continue flow {flow_id} in status {flow.status}")
            return False
        
        # Update status
        await self.flow_repo.update(
            flow_id,
            {"status": FlowStatus.RUNNING}
        )
        
        # Resume via flow manager
        from app.core.context import get_current_context
        context = get_current_context()
        
        return await flow_manager.resume_flow(flow_id, self.db, context)
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active flows for current context"""
        flows = await self.flow_repo.get_active_flows()
        
        return [
            {
                "flow_id": str(flow.id),
                "flow_name": flow.flow_name,
                "status": flow.status,
                "current_phase": flow.current_phase,
                "progress_percentage": flow.progress_percentage,
                "created_at": flow.created_at.isoformat() if flow.created_at else None
            }
            for flow in flows
        ]
    
    async def cancel_flow(self, flow_id: str) -> bool:
        """Cancel a running flow"""
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            return False
        
        if flow.status not in [FlowStatus.RUNNING, FlowStatus.PAUSED]:
            return False
        
        # Update status
        await self.flow_repo.update(
            flow_id,
            {"status": FlowStatus.CANCELLED}
        )
        
        # Cancel via flow manager
        await flow_manager.pause_flow(flow_id)
        
        return True
    
    def _serialize_mappings(self, mappings) -> List[Dict[str, Any]]:
        """Serialize field mappings for API response"""
        return [
            {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "confidence_score": mapping.confidence_score,
                "match_type": mapping.match_type,
                "status": mapping.status,
                "transformation_rules": mapping.transformation_rules
            }
            for mapping in mappings
        ]
```

**File to create**: `backend/app/services/v3/field_mapping_service.py`

```python
"""
V3 Field Mapping Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.v3.field_mapping import V3FieldMappingRepository
from app.models.v3 import V3FieldMapping, MappingStatus
from app.core.context import get_current_context
import logging

logger = logging.getLogger(__name__)

class V3FieldMappingService:
    """Service for V3 field mapping operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mapping_repo = V3FieldMappingRepository(db)
    
    async def create_ai_suggestions(
        self,
        import_id: str,
        suggestions: List[Dict[str, Any]]
    ) -> List[V3FieldMapping]:
        """Create AI-suggested field mappings"""
        try:
            # Prepare mapping data
            mappings_data = []
            for suggestion in suggestions:
                mappings_data.append({
                    "data_import_id": import_id,
                    "source_field": suggestion["source_field"],
                    "target_field": suggestion["target_field"],
                    "confidence_score": suggestion.get("confidence", 0.0),
                    "match_type": suggestion.get("match_type", "fuzzy"),
                    "status": MappingStatus.SUGGESTED,
                    "transformation_rules": suggestion.get("transformation_rules")
                })
            
            # Bulk create mappings
            mappings = await self.mapping_repo.bulk_create_mappings(
                import_id,
                mappings_data
            )
            
            logger.info(f"Created {len(mappings)} AI suggestions for import {import_id}")
            
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to create AI suggestions: {e}")
            raise
    
    async def get_mappings_for_import(self, import_id: str) -> List[Dict[str, Any]]:
        """Get all mappings for an import"""
        mappings = await self.mapping_repo.get_by_import(import_id)
        
        return [
            {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "confidence_score": mapping.confidence_score,
                "match_type": mapping.match_type,
                "status": mapping.status,
                "transformation_rules": mapping.transformation_rules,
                "approved_by": mapping.approved_by,
                "approved_at": mapping.approved_at.isoformat() if mapping.approved_at else None
            }
            for mapping in mappings
        ]
    
    async def approve_mapping(
        self,
        mapping_id: str,
        approved_by: Optional[str] = None
    ) -> bool:
        """Approve a field mapping"""
        context = get_current_context()
        approved_by = approved_by or context.user_id
        
        success = await self.mapping_repo.approve_mapping(mapping_id, approved_by)
        
        if success:
            # Trigger agent learning
            await self._trigger_agent_learning(mapping_id, "approved")
        
        return success
    
    async def reject_mapping(
        self,
        mapping_id: str,
        rejected_by: Optional[str] = None
    ) -> bool:
        """Reject a field mapping"""
        context = get_current_context()
        rejected_by = rejected_by or context.user_id
        
        success = await self.mapping_repo.reject_mapping(mapping_id, rejected_by)
        
        if success:
            # Trigger agent learning
            await self._trigger_agent_learning(mapping_id, "rejected")
        
        return success
    
    async def update_mapping(
        self,
        mapping_id: str,
        target_field: str,
        transformation_rules: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update mapping with new target"""
        success = await self.mapping_repo.update_mapping(
            mapping_id,
            target_field,
            transformation_rules
        )
        
        if success:
            # Trigger agent learning
            await self._trigger_agent_learning(mapping_id, "modified")
        
        return success
    
    async def _trigger_agent_learning(
        self,
        mapping_id: str,
        action: str
    ) -> None:
        """Trigger agent learning from user feedback"""
        try:
            # Get the mapping
            mapping = await self.mapping_repo.get_by_id(mapping_id)
            if not mapping:
                return
            
            # Log learning event
            logger.info(
                f"Agent learning: {action} mapping {mapping.source_field} -> {mapping.target_field}"
            )
            
            # TODO: Integrate with actual agent learning system
            
        except Exception as e:
            logger.error(f"Failed to trigger agent learning: {e}")
```

### 4. Update V3 API Endpoints
**File to update**: `backend/app/api/v3/data_import.py`

Replace the mock handlers with actual service calls:

```python
# At the top of the file, add imports
from app.services.v3.data_import_service import V3DataImportService
from app.core.database_context import get_db

# Replace the handler initialization
@router.on_event("startup")
async def startup_event():
    """Initialize import handlers on startup"""
    # Service will be created per request with database session
    logger.info("V3 Data import endpoints ready")

# Update the store_import endpoint
@router.post("/store-import")
async def store_import(
    import_data: dict,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Store data import and initiate discovery flow"""
    try:
        service = V3DataImportService(db)
        
        # Create import
        data_import = await service.create_import(
            filename=import_data.get("filename", "Unknown"),
            file_data=import_data.get("data", b""),
            source_system=import_data.get("source_system")
        )
        
        # Process records if provided
        if "records" in import_data:
            await service.process_import_data(
                str(data_import.id),
                import_data["records"]
            )
        
        # Get full import with flow
        result = await service.get_import_with_flow(str(data_import.id))
        
        return {
            "success": True,
            "import_id": str(data_import.id),
            "flow_id": str(result["flow"].id) if result["flow"] else None,
            "message": "Data import created successfully"
        }
        
    except Exception as e:
        logger.error(f"Import creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**File to update**: `backend/app/api/v3/discovery_flow.py`

Replace mock handlers with actual service:

```python
# Add imports
from app.services.v3.discovery_flow_service import V3DiscoveryFlowService
from app.core.database_context import get_db

# Update endpoints
@router.get("/flows/active")
async def get_active_flows(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get all active discovery flows"""
    try:
        service = V3DiscoveryFlowService(db)
        flows = await service.get_active_flows()
        
        return {
            "flows": flows,
            "total": len(flows)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flows/{flow_id}/status")
async def get_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get detailed status of a discovery flow"""
    try:
        service = V3DiscoveryFlowService(db)
        status = await service.get_flow_status(flow_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get flow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**File to update**: `backend/app/api/v3/field_mapping.py`

Replace mock handlers with actual service:

```python
# Add imports
from app.services.v3.field_mapping_service import V3FieldMappingService
from app.core.database_context import get_db

# Update endpoints
@router.get("/imports/{import_id}/mappings")
async def get_field_mappings(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get field mappings for an import"""
    try:
        service = V3FieldMappingService(db)
        mappings = await service.get_mappings_for_import(import_id)
        
        return {
            "mappings": mappings,
            "total": len(mappings)
        }
        
    except Exception as e:
        logger.error(f"Failed to get mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mappings/{mapping_id}/approve")
async def approve_mapping(
    mapping_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Approve a field mapping"""
    try:
        service = V3FieldMappingService(db)
        success = await service.approve_mapping(mapping_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        return {
            "success": True,
            "message": "Mapping approved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. Create Database Migration
**File to create**: `backend/migrations/versions/add_v3_tables.py`

```python
"""Add V3 API tables

Revision ID: add_v3_tables_001
Revises: previous_migration_id
Create Date: 2024-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    """Create V3 tables"""
    
    # Create enums
    op.execute("CREATE TYPE flowstatus AS ENUM ('initializing', 'running', 'paused', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE importstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE mappingstatus AS ENUM ('suggested', 'approved', 'rejected', 'modified')")
    
    # Create v3_data_imports table
    op.create_table(
        'v3_data_imports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer()),
        sa.Column('mime_type', sa.String()),
        sa.Column('source_system', sa.String()),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='importstatus'), nullable=False),
        sa.Column('total_records', sa.Integer(), default=0),
        sa.Column('processed_records', sa.Integer(), default=0),
        sa.Column('failed_records', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('error_message', sa.String()),
        sa.Column('error_details', sa.JSON())
    )
    
    # Create indexes
    op.create_index('idx_v3_imports_client_status', 'v3_data_imports', ['client_account_id', 'status'])
    op.create_index('idx_v3_imports_created', 'v3_data_imports', ['created_at'])
    
    # Create v3_discovery_flows table
    op.create_table(
        'v3_discovery_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_name', sa.String()),
        sa.Column('flow_type', sa.String(), default='unified_discovery'),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v3_data_imports.id')),
        sa.Column('status', postgresql.ENUM('initializing', 'running', 'paused', 'completed', 'failed', 'cancelled', name='flowstatus'), nullable=False),
        sa.Column('current_phase', sa.String()),
        sa.Column('phases_completed', sa.JSON(), default=[]),
        sa.Column('progress_percentage', sa.Float(), default=0.0),
        sa.Column('flow_state', sa.JSON(), default={}),
        sa.Column('crew_outputs', sa.JSON(), default={}),
        sa.Column('field_mappings', sa.JSON()),
        sa.Column('discovered_assets', sa.JSON()),
        sa.Column('dependencies', sa.JSON()),
        sa.Column('tech_debt_analysis', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('error_message', sa.String()),
        sa.Column('error_phase', sa.String()),
        sa.Column('error_details', sa.JSON())
    )
    
    # Create indexes
    op.create_index('idx_v3_flows_client_status', 'v3_discovery_flows', ['client_account_id', 'status'])
    op.create_index('idx_v3_flows_import', 'v3_discovery_flows', ['data_import_id'])
    
    # Create v3_raw_import_records table
    op.create_table(
        'v3_raw_import_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v3_data_imports.id'), nullable=False),
        sa.Column('record_index', sa.Integer(), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('is_valid', sa.Boolean()),
        sa.Column('validation_errors', sa.JSON()),
        sa.Column('cleansed_data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime())
    )
    
    # Create indexes
    op.create_index('idx_v3_records_import', 'v3_raw_import_records', ['data_import_id'])
    op.create_index('idx_v3_records_processed', 'v3_raw_import_records', ['is_processed'])
    
    # Create v3_field_mappings table
    op.create_table(
        'v3_field_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v3_data_imports.id'), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_field', sa.String(), nullable=False),
        sa.Column('target_field', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('match_type', sa.String()),
        sa.Column('suggested_by', sa.String(), default='ai_agent'),
        sa.Column('status', postgresql.ENUM('suggested', 'approved', 'rejected', 'modified', name='mappingstatus'), nullable=False),
        sa.Column('approved_by', sa.String()),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('transformation_rules', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    
    # Create indexes
    op.create_index('idx_v3_mappings_import', 'v3_field_mappings', ['data_import_id'])
    op.create_index('idx_v3_mappings_source', 'v3_field_mappings', ['source_field'])
    op.create_index('idx_v3_mappings_status', 'v3_field_mappings', ['status'])

def downgrade():
    """Drop V3 tables"""
    op.drop_table('v3_field_mappings')
    op.drop_table('v3_raw_import_records')
    op.drop_table('v3_discovery_flows')
    op.drop_table('v3_data_imports')
    
    # Drop enums
    op.execute('DROP TYPE flowstatus')
    op.execute('DROP TYPE importstatus')
    op.execute('DROP TYPE mappingstatus')
```

### 6. Integration Tests
**File to create**: `backend/tests/integration/test_v3_persistence.py`

```python
"""
Integration tests for V3 persistence layer
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v3 import V3DataImport, V3DiscoveryFlow, V3FieldMapping
from app.services.v3.data_import_service import V3DataImportService
from app.services.v3.discovery_flow_service import V3DiscoveryFlowService
from app.services.v3.field_mapping_service import V3FieldMappingService
from app.core.context import with_context

@pytest.mark.asyncio
@with_context(
    client_account_id="test-client",
    engagement_id="test-engagement", 
    user_id="test-user"
)
async def test_v3_data_import_persistence(test_db: AsyncSession):
    """Test V3 data import creation and retrieval"""
    service = V3DataImportService(test_db)
    
    # Create import
    data_import = await service.create_import(
        filename="test_data.csv",
        file_data=b"test,data\n1,2",
        source_system="test_system"
    )
    
    assert data_import.id is not None
    assert data_import.filename == "test_data.csv"
    assert data_import.client_account_id == "test-client"
    
    # Retrieve import
    result = await service.get_import_with_flow(str(data_import.id))
    assert result is not None
    assert result["import"].id == data_import.id
    assert result["flow"] is not None

@pytest.mark.asyncio
@with_context(
    client_account_id="test-client",
    engagement_id="test-engagement",
    user_id="test-user"
)
async def test_v3_flow_persistence(test_db: AsyncSession):
    """Test V3 flow state persistence"""
    import_service = V3DataImportService(test_db)
    flow_service = V3DiscoveryFlowService(test_db)
    
    # Create import and flow
    data_import = await import_service.create_import(
        filename="test_flow.csv",
        file_data=b"data"
    )
    
    # Get flow status
    result = await import_service.get_import_with_flow(str(data_import.id))
    flow = result["flow"]
    
    status = await flow_service.get_flow_status(str(flow.id))
    assert status is not None
    assert status["status"] == "initializing"
    assert status["data_import_id"] == str(data_import.id)

@pytest.mark.asyncio
@with_context(
    client_account_id="test-client",
    engagement_id="test-engagement",
    user_id="test-user"
)
async def test_v3_field_mapping_persistence(test_db: AsyncSession):
    """Test V3 field mapping persistence"""
    import_service = V3DataImportService(test_db)
    mapping_service = V3FieldMappingService(test_db)
    
    # Create import
    data_import = await import_service.create_import(
        filename="test_mapping.csv",
        file_data=b"data"
    )
    
    # Create AI suggestions
    suggestions = [
        {
            "source_field": "old_name",
            "target_field": "new_name",
            "confidence": 0.95,
            "match_type": "exact"
        },
        {
            "source_field": "old_status",
            "target_field": "new_status",
            "confidence": 0.80,
            "match_type": "fuzzy"
        }
    ]
    
    mappings = await mapping_service.create_ai_suggestions(
        str(data_import.id),
        suggestions
    )
    
    assert len(mappings) == 2
    assert mappings[0].source_field == "old_name"
    assert mappings[0].status == "suggested"
    
    # Test approval
    success = await mapping_service.approve_mapping(str(mappings[0].id))
    assert success is True
    
    # Verify persistence
    saved_mappings = await mapping_service.get_mappings_for_import(str(data_import.id))
    assert len(saved_mappings) == 2
    assert saved_mappings[0]["status"] == "approved"
```

## Success Criteria
- [ ] V3 database models created with proper relationships
- [ ] V3 repository layer with context awareness
- [ ] V3 service layer handling business logic
- [ ] V3 API endpoints using real persistence
- [ ] Database migration applied successfully
- [ ] Data persists across server restarts
- [ ] Integration tests passing
- [ ] No more "service not available" warnings

## Testing Commands
```bash
# Run database migration
docker exec -it migration_backend alembic upgrade head

# Test V3 persistence
docker exec -it migration_backend python -m pytest tests/integration/test_v3_persistence.py -v

# Verify tables created
docker exec -it migration_db psql -U postgres -d migration_db -c "\dt v3_*"

# Test API endpoints
curl -X POST http://localhost:8000/api/v3/data-import/store-import \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-ID: test-client" \
  -d '{"filename": "test.csv", "records": [{"field1": "value1"}]}'
```

## Rollback Plan
If issues arise:
1. Revert API endpoints to use V2
2. Drop V3 tables: `alembic downgrade -1`
3. Update frontend to use V2 endpoints

## Definition of Done
- [ ] V3 models created and migrated
- [ ] V3 repositories implement proper persistence
- [ ] V3 services handle all business logic
- [ ] V3 APIs no longer return mock data
- [ ] Data persists in PostgreSQL
- [ ] Frontend can save and retrieve data
- [ ] Integration tests verify persistence
- [ ] No more warning logs about missing services
- [ ] PR created with title: "feat: [Phase1-E1] V3 API persistence layer"

## Notes
- This is a blocking issue for Phase 2
- Preserves existing V3 API contracts
- Adds proper persistence without breaking frontend
- Follows established patterns from V1/V2
- Maintains multi-tenant isolation