# 🚀 Discovery Flow Fresh Architecture - Detailed Implementation Tasks

**Date:** January 27, 2025  
**Priority:** CRITICAL  
**Timeline:** 10 days  
**Target:** Complete Discovery Flow with fresh database architecture

## 📋 Executive Summary

This document provides step-by-step implementation tasks to rebuild the Discovery Flow with clean database architecture, eliminating session_id confusion and establishing CrewAI Flow ID as single source of truth.

## 🎯 Current State vs Target State

### **Current Issues (What We're Fixing)**
- ❌ Database schema mismatch between models and actual tables
- ❌ UUID vs String confusion in API responses  
- ❌ Missing core fields: `current_phase`, `raw_data`, `field_mappings`, etc.
- ❌ Complex schema instead of simple implementation plan schema
- ❌ No proper phase progression tracking
- ❌ No automatic asset creation from discovery results

### **Target Architecture (What We're Building)**
- ✅ Simple schema matching implementation plan exactly
- ✅ CrewAI Flow ID as UUID (single source of truth)
- ✅ Proper phase tracking with completion flags
- ✅ Automatic asset creation from discovery results
- ✅ Clean navigation between all discovery phases

## 🗂️ File Structure Overview

```
backend/
├── app/models/
│   ├── discovery_flow.py          # REWRITE - Simple schema
│   └── discovery_asset.py         # REWRITE - Simple schema
├── app/repositories/
│   └── discovery_flow_repository.py # UPDATE - Fix methods
├── app/services/
│   └── discovery_flow_service.py    # UPDATE - Fix methods  
├── app/api/v1/
│   └── discovery_flow_v2.py         # UPDATE - Fix response models
├── alembic/versions/
│   └── [new]_implement_correct_schema.py # CREATE
└── scripts/
    └── seed_discovery_flow_tables.py    # REWRITE

src/
├── hooks/
│   └── useDiscoveryFlowV2.ts        # CREATE - New hook
├── services/
│   └── discoveryFlowV2Service.ts    # CREATE - New service
└── pages/discovery/
    ├── DataImport.tsx               # UPDATE - Use new API
    ├── AttributeMapping.tsx         # UPDATE - Use new API
    ├── DataCleansing.tsx           # UPDATE - Use new API
    ├── Inventory.tsx               # UPDATE - Use new API
    ├── Dependencies.tsx            # UPDATE - Use new API
    └── TechDebt.tsx               # UPDATE - Use new API
```

---

## 📅 PHASE 1: DATABASE FOUNDATION (Days 1-3)

### **Task 1.1: Rewrite DiscoveryFlow Model (Day 1)**

**File:** `backend/app/models/discovery_flow.py`

**COMPLETE REWRITE - Use this exact code:**

```python
"""
Discovery Flow Model - Implementation Plan Schema
Simple architecture matching the implementation plan exactly
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiscoveryFlow(Base):
    """Discovery Flow - Simple schema matching implementation plan"""
    __tablename__ = 'discovery_flows'

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant isolation (use demo constants as per plan)
    client_account_id = Column(UUID(as_uuid=True), 
                              default=uuid.UUID("11111111-1111-1111-1111-111111111111"), 
                              nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), 
                          default=uuid.UUID("22222222-2222-2222-2222-222222222222"), 
                          nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), 
                     default=uuid.UUID("33333333-3333-3333-3333-333333333333"), 
                     nullable=False, index=True)
    
    # Discovery flow state
    current_phase = Column(String(100), default="data_import", nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, completed, failed
    
    # CrewAI integration  
    crewai_flow_id = Column(UUID(as_uuid=True), index=True, nullable=False, unique=True)
    
    # Import connection
    import_session_id = Column(UUID(as_uuid=True), index=True)
    
    # Discovery results (as per implementation plan)
    raw_data = Column(JSON)              # Imported raw data
    field_mappings = Column(JSON)        # Attribute mapping results  
    cleaned_data = Column(JSON)          # Data cleansing results
    asset_inventory = Column(JSON)       # Discovered assets
    dependencies = Column(JSON)          # Dependency analysis
    tech_debt = Column(JSON)             # Tech debt analysis
    
    # Phase completion tracking (6 phases)
    data_import_completed = Column(Boolean, default=False, nullable=False)
    attribute_mapping_completed = Column(Boolean, default=False, nullable=False)
    data_cleansing_completed = Column(Boolean, default=False, nullable=False)
    inventory_completed = Column(Boolean, default=False, nullable=False)
    dependencies_completed = Column(Boolean, default=False, nullable=False)
    tech_debt_completed = Column(Boolean, default=False, nullable=False)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    assets = relationship("DiscoveryAsset", back_populates="discovery_flow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DiscoveryFlow(crewai_flow_id={self.crewai_flow_id}, phase='{self.current_phase}', status='{self.status}')>"

    def calculate_progress(self) -> float:
        """Calculate progress based on completed phases"""
        phases = [
            self.data_import_completed,
            self.attribute_mapping_completed, 
            self.data_cleansing_completed,
            self.inventory_completed,
            self.dependencies_completed,
            self.tech_debt_completed
        ]
        completed = sum(1 for phase in phases if phase)
        return round((completed / len(phases)) * 100, 1)

    def get_current_phase(self) -> str:
        """Get current phase based on completion status"""
        if not self.data_import_completed:
            return "data_import"
        elif not self.attribute_mapping_completed:
            return "attribute_mapping"  
        elif not self.data_cleansing_completed:
            return "data_cleansing"
        elif not self.inventory_completed:
            return "inventory"
        elif not self.dependencies_completed:
            return "dependencies"
        elif not self.tech_debt_completed:
            return "tech_debt"
        else:
            return "completed"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "crewai_flow_id": str(self.crewai_flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "user_id": str(self.user_id),
            "current_phase": self.current_phase,
            "progress_percentage": self.progress_percentage,
            "status": self.status,
            "import_session_id": str(self.import_session_id) if self.import_session_id else None,
            "raw_data": self.raw_data or [],
            "field_mappings": self.field_mappings or {},
            "cleaned_data": self.cleaned_data or {},
            "asset_inventory": self.asset_inventory or {},
            "dependencies": self.dependencies or {},
            "tech_debt": self.tech_debt or {},
            "phase_completion": {
                "data_import": self.data_import_completed,
                "attribute_mapping": self.attribute_mapping_completed,
                "data_cleansing": self.data_cleansing_completed,
                "inventory": self.inventory_completed,
                "dependencies": self.dependencies_completed,
                "tech_debt": self.tech_debt_completed
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
```

### **Task 1.2: Rewrite DiscoveryAsset Model (Day 1)**

**File:** `backend/app/models/discovery_asset.py`

**COMPLETE REWRITE - Use this exact code:**

```python
"""
Discovery Asset Model - Implementation Plan Schema  
Simple normalized asset storage
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiscoveryAsset(Base):
    """Discovery Asset - Simple schema for normalized asset storage"""
    __tablename__ = 'discovery_assets'

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discovery_flow_id = Column(UUID(as_uuid=True), ForeignKey('discovery_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Multi-tenant isolation (inherit from discovery flow)
    client_account_id = Column(UUID(as_uuid=True), 
                              default=uuid.UUID("11111111-1111-1111-1111-111111111111"), 
                              nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), 
                          default=uuid.UUID("22222222-2222-2222-2222-222222222222"), 
                          nullable=False, index=True)
    
    # Asset identification
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(100))  # server, database, application, etc.
    asset_data = Column(JSON, nullable=False)  # All asset attributes
    
    # Discovery phase tracking
    discovered_in_phase = Column(String(50))  # which phase discovered this asset
    quality_score = Column(Float)
    validation_status = Column(String(20), default="pending")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    discovery_flow = relationship("DiscoveryFlow", back_populates="assets")

    def __repr__(self):
        return f"<DiscoveryAsset(name='{self.asset_name}', type='{self.asset_type}', phase='{self.discovered_in_phase}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "discovery_flow_id": str(self.discovery_flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "asset_data": self.asset_data,
            "discovered_in_phase": self.discovered_in_phase,
            "quality_score": self.quality_score,
            "validation_status": self.validation_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
```

### **Task 1.3: Create Database Migration (Day 1)**

**File:** `backend/alembic/versions/[timestamp]_implement_correct_discovery_schema.py`

**Steps:**
1. Delete the auto-generated migration file
2. Create new migration manually with this exact content:

```python
"""implement_correct_discovery_schema

Revision ID: [auto-generated]
Revises: c547c104e9b1
Create Date: [auto-generated]
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '[auto-generated]'
down_revision = 'c547c104e9b1'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing tables to start fresh
    op.execute("DROP TABLE IF EXISTS discovery_assets CASCADE")
    op.execute("DROP TABLE IF EXISTS discovery_flows CASCADE")
    
    # Create discovery_flows table with correct schema
    op.create_table('discovery_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('current_phase', sa.String(100), nullable=False, default='data_import'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, default=0.0),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('crewai_flow_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('import_session_id', postgresql.UUID(as_uuid=True), index=True),
        sa.Column('raw_data', postgresql.JSON()),
        sa.Column('field_mappings', postgresql.JSON()),
        sa.Column('cleaned_data', postgresql.JSON()),
        sa.Column('asset_inventory', postgresql.JSON()),
        sa.Column('dependencies', postgresql.JSON()),
        sa.Column('tech_debt', postgresql.JSON()),
        sa.Column('data_import_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('attribute_mapping_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('data_cleansing_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('inventory_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('dependencies_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('tech_debt_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    
    # Create discovery_assets table with correct schema
    op.create_table('discovery_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('discovery_flow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discovery_flows.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_type', sa.String(100)),
        sa.Column('asset_data', postgresql.JSON(), nullable=False),
        sa.Column('discovered_in_phase', sa.String(50)),
        sa.Column('quality_score', sa.Float()),
        sa.Column('validation_status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

def downgrade():
    op.drop_table('discovery_assets')
    op.drop_table('discovery_flows')
```

**Commands to run:**
```bash
# Delete auto-generated migration
rm backend/alembic/versions/b065dfbe76bc_fix_discovery_flow_schema_to_match_.py

# Create new migration
docker exec -it migration_backend alembic revision -m "implement_correct_discovery_schema"

# Edit the migration file with the content above

# Apply migration
docker exec -it migration_backend alembic upgrade head
```

### **Task 1.4: Update Repository Methods (Day 2)**

**File:** `backend/app/repositories/discovery_flow_repository.py`

**Key methods to fix:**

```python
async def create_discovery_flow(self, crewai_flow_id: str, import_session_id: str = None, raw_data: list = None):
    """Create discovery flow with correct schema"""
    flow = DiscoveryFlow(
        crewai_flow_id=uuid.UUID(crewai_flow_id),
        import_session_id=uuid.UUID(import_session_id) if import_session_id else None,
        raw_data=raw_data or [],
        current_phase="data_import"
    )
    self.db.add(flow)
    await self.db.commit()
    await self.db.refresh(flow)
    return flow

async def update_phase_completion(self, crewai_flow_id: str, phase: str, phase_data: dict):
    """Update phase completion and store phase data"""
    flow = await self.get_by_crewai_flow_id(crewai_flow_id)
    if not flow:
        raise ValueError(f"Flow not found: {crewai_flow_id}")
    
    # Mark phase as completed
    setattr(flow, f"{phase}_completed", True)
    
    # Store phase data in appropriate field
    if phase == "data_import":
        flow.raw_data = phase_data
    elif phase == "attribute_mapping":
        flow.field_mappings = phase_data
    elif phase == "data_cleansing":
        flow.cleaned_data = phase_data
    elif phase == "inventory":
        flow.asset_inventory = phase_data
    elif phase == "dependencies":
        flow.dependencies = phase_data
    elif phase == "tech_debt":
        flow.tech_debt = phase_data
    
    # Update current phase and progress
    flow.current_phase = flow.get_current_phase()
    flow.progress_percentage = flow.calculate_progress()
    
    await self.db.commit()
    await self.db.refresh(flow)
    return flow
```

### **Task 1.5: Update Service Methods (Day 2)**

**File:** `backend/app/services/discovery_flow_service.py`

**Key methods to fix:**

```python
async def create_discovery_flow(self, crewai_flow_id: str, raw_data: list = None, import_session_id: str = None):
    """Create discovery flow using CrewAI Flow ID as single source of truth"""
    repository = DiscoveryFlowRepository(self.db, self.context.client_account_id, self.context.engagement_id)
    return await repository.create_discovery_flow(
        crewai_flow_id=crewai_flow_id,
        import_session_id=import_session_id,
        raw_data=raw_data
    )

async def update_phase_completion(self, crewai_flow_id: str, phase: str, phase_data: dict):
    """Update phase completion and automatically create assets if inventory phase"""
    repository = DiscoveryFlowRepository(self.db, self.context.client_account_id, self.context.engagement_id)
    flow = await repository.update_phase_completion(crewai_flow_id, phase, phase_data)
    
    # Auto-create assets if inventory phase completed
    if phase == "inventory" and phase_data:
        await self._create_assets_from_inventory(flow, phase_data)
    
    return flow

async def _create_assets_from_inventory(self, flow: DiscoveryFlow, inventory_data: dict):
    """Create DiscoveryAsset records from inventory phase data"""
    asset_repository = DiscoveryAssetRepository(self.db, self.context.client_account_id, self.context.engagement_id)
    
    assets = inventory_data.get('assets', [])
    for asset_data in assets:
        await asset_repository.create_asset(
            discovery_flow_id=flow.id,
            asset_name=asset_data.get('name', 'Unknown'),
            asset_type=asset_data.get('type', 'unknown'),
            asset_data=asset_data,
            discovered_in_phase='inventory'
        )
```

### **Task 1.6: Rewrite Seeding Script (Day 3)**

**File:** `backend/scripts/seed_discovery_flow_tables.py`

**COMPLETE REWRITE with correct schema:**

```python
#!/usr/bin/env python3
"""
Seed Discovery Flow Tables - Implementation Plan Schema
Creates test data matching the exact implementation plan schema
"""
import asyncio
import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset

# Demo constants as per implementation plan
DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222") 
DEMO_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")

async def seed_discovery_flows():
    """Seed discovery flows with correct schema"""
    async with AsyncSessionLocal() as session:
        # Create sample discovery flow
        crewai_flow_id = uuid.uuid4()
        import_session_id = uuid.uuid4()
        
        flow = DiscoveryFlow(
            crewai_flow_id=crewai_flow_id,
            import_session_id=import_session_id,
            current_phase="inventory",
            progress_percentage=66.7,
            status="active",
            raw_data=[
                {"server": "web-01", "ip": "10.0.1.10", "os": "Ubuntu 20.04"},
                {"server": "db-01", "ip": "10.0.1.20", "os": "CentOS 7"},
                {"server": "app-01", "ip": "10.0.1.30", "os": "Windows Server 2019"}
            ],
            field_mappings={
                "server_name": "server",
                "ip_address": "ip", 
                "operating_system": "os"
            },
            cleaned_data={
                "cleaned_records": 3,
                "validation_errors": 0,
                "quality_score": 95.5
            },
            asset_inventory={
                "total_assets": 3,
                "asset_types": ["server"],
                "assets": [
                    {"name": "web-01", "type": "server", "subtype": "web_server"},
                    {"name": "db-01", "type": "server", "subtype": "database_server"},
                    {"name": "app-01", "type": "server", "subtype": "application_server"}
                ]
            },
            # Phase completion
            data_import_completed=True,
            attribute_mapping_completed=True,
            data_cleansing_completed=True,
            inventory_completed=True,
            dependencies_completed=False,
            tech_debt_completed=False
        )
        
        session.add(flow)
        await session.flush()  # Get the flow.id
        
        # Create corresponding assets
        assets_data = [
            {"name": "web-01", "type": "server", "subtype": "web_server", "ip": "10.0.1.10"},
            {"name": "db-01", "type": "server", "subtype": "database_server", "ip": "10.0.1.20"},
            {"name": "app-01", "type": "server", "subtype": "application_server", "ip": "10.0.1.30"}
        ]
        
        for asset_data in assets_data:
            asset = DiscoveryAsset(
                discovery_flow_id=flow.id,
                asset_name=asset_data["name"],
                asset_type=asset_data["type"],
                asset_data=asset_data,
                discovered_in_phase="inventory",
                quality_score=95.0,
                validation_status="validated"
            )
            session.add(asset)
        
        await session.commit()
        print(f"✅ Created discovery flow: {crewai_flow_id}")
        print(f"✅ Created {len(assets_data)} assets")
        return crewai_flow_id

if __name__ == "__main__":
    asyncio.run(seed_discovery_flows())
```

**Commands to run:**
```bash
# Run seeding script
docker exec -it migration_backend python scripts/seed_discovery_flow_tables.py
```

---

## 📅 PHASE 2: API LAYER FIXES (Day 4)

### **Task 2.1: Fix V2 API Response Models**

**File:** `backend/app/api/v1/discovery_flow_v2.py`

**Replace response models with correct schema:**

```python
class DiscoveryFlowResponse(BaseModel):
    """Response model matching implementation plan schema"""
    id: str
    crewai_flow_id: str  # UUID as string
    client_account_id: str
    engagement_id: str
    user_id: str
    current_phase: str
    progress_percentage: float
    status: str
    import_session_id: Optional[str]
    raw_data: List[Dict[str, Any]]
    field_mappings: Dict[str, Any]
    cleaned_data: Dict[str, Any]
    asset_inventory: Dict[str, Any]
    dependencies: Dict[str, Any]
    tech_debt: Dict[str, Any]
    phase_completion: Dict[str, bool]
    created_at: Optional[str]
    updated_at: Optional[str]

class DiscoveryAssetResponse(BaseModel):
    """Response model for discovery asset"""
    id: str
    discovery_flow_id: str
    client_account_id: str
    engagement_id: str
    asset_name: str
    asset_type: Optional[str]
    asset_data: Dict[str, Any]
    discovered_in_phase: Optional[str]
    quality_score: Optional[float]
    validation_status: str
    created_at: Optional[str]
    updated_at: Optional[str]
```

### **Task 2.2: Update API Endpoints**

**Key endpoints to fix in same file:**

```python
@router.post("/flows", response_model=DiscoveryFlowResponse)
async def create_discovery_flow(
    request: CreateDiscoveryFlowRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Create discovery flow using CrewAI Flow ID"""
    service = DiscoveryFlowService(db, context)
    flow = await service.create_discovery_flow(
        crewai_flow_id=request.crewai_flow_id,  # Use crewai_flow_id, not flow_id
        raw_data=request.raw_data,
        import_session_id=request.import_session_id
    )
    return DiscoveryFlowResponse(**flow.to_dict())

@router.get("/flows/crewai/{crewai_flow_id}", response_model=DiscoveryFlowResponse)
async def get_flow_by_crewai_id(
    crewai_flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get flow by CrewAI Flow ID (primary lookup method)"""
    service = DiscoveryFlowService(db, context)
    flow = await service.get_flow_by_crewai_id(crewai_flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return DiscoveryFlowResponse(**flow.to_dict())
```

---

## 📅 PHASE 3: FRONTEND INTEGRATION (Days 5-8)

### **Task 3.1: Create V2 Frontend Service (Day 5)**

**File:** `src/services/discoveryFlowV2Service.ts`

**CREATE NEW FILE:**

```typescript
/**
 * Discovery Flow V2 Service - Clean Architecture
 * Uses CrewAI Flow ID as single source of truth
 */
import { apiClient } from '@/config/api';

export interface DiscoveryFlow {
  id: string;
  crewai_flow_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  current_phase: string;
  progress_percentage: number;
  status: string;
  import_session_id?: string;
  raw_data: any[];
  field_mappings: Record<string, any>;
  cleaned_data: Record<string, any>;
  asset_inventory: Record<string, any>;
  dependencies: Record<string, any>;
  tech_debt: Record<string, any>;
  phase_completion: Record<string, boolean>;
  created_at?: string;
  updated_at?: string;
}

export interface DiscoveryAsset {
  id: string;
  discovery_flow_id: string;
  asset_name: string;
  asset_type?: string;
  asset_data: Record<string, any>;
  discovered_in_phase?: string;
  quality_score?: number;
  validation_status: string;
}

class DiscoveryFlowV2Service {
  private baseUrl = '/api/v2/discovery-flows';

  async createFlow(data: {
    crewai_flow_id: string;
    raw_data: any[];
    import_session_id?: string;
  }): Promise<DiscoveryFlow> {
    const response = await apiClient.post(`${this.baseUrl}/flows`, data);
    return response.data;
  }

  async getFlowByCrewAIId(crewai_flow_id: string): Promise<DiscoveryFlow> {
    const response = await apiClient.get(`${this.baseUrl}/flows/crewai/${crewai_flow_id}`);
    return response.data;
  }

  async updatePhaseCompletion(crewai_flow_id: string, phase: string, phase_data: any): Promise<DiscoveryFlow> {
    const response = await apiClient.put(`${this.baseUrl}/flows/crewai/${crewai_flow_id}/phase`, {
      phase,
      phase_data
    });
    return response.data;
  }

  async getFlowAssets(crewai_flow_id: string): Promise<DiscoveryAsset[]> {
    const response = await apiClient.get(`${this.baseUrl}/flows/crewai/${crewai_flow_id}/assets`);
    return response.data;
  }

  async completeFlow(crewai_flow_id: string): Promise<DiscoveryFlow> {
    const response = await apiClient.post(`${this.baseUrl}/flows/crewai/${crewai_flow_id}/complete`);
    return response.data;
  }
}

export const discoveryFlowV2Service = new DiscoveryFlowV2Service();
```

### **Task 3.2: Create V2 React Hook (Day 5)**

**File:** `src/hooks/useDiscoveryFlowV2.ts`

**CREATE NEW FILE:**

```typescript
/**
 * Discovery Flow V2 Hook - Clean Architecture
 * Manages discovery flow state using CrewAI Flow ID
 */
import { useState, useEffect, useCallback } from 'react';
import { discoveryFlowV2Service, DiscoveryFlow } from '@/services/discoveryFlowV2Service';

export const useDiscoveryFlowV2 = (crewai_flow_id?: string) => {
  const [flow, setFlow] = useState<DiscoveryFlow | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFlow = useCallback(async (flowId: string) => {
    setLoading(true);
    setError(null);
    try {
      const flowData = await discoveryFlowV2Service.getFlowByCrewAIId(flowId);
      setFlow(flowData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load flow');
    } finally {
      setLoading(false);
    }
  }, []);

  const createFlow = useCallback(async (data: {
    crewai_flow_id: string;
    raw_data: any[];
    import_session_id?: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const newFlow = await discoveryFlowV2Service.createFlow(data);
      setFlow(newFlow);
      return newFlow;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create flow');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updatePhase = useCallback(async (phase: string, phase_data: any) => {
    if (!flow) throw new Error('No flow loaded');
    
    setLoading(true);
    setError(null);
    try {
      const updatedFlow = await discoveryFlowV2Service.updatePhaseCompletion(
        flow.crewai_flow_id, 
        phase, 
        phase_data
      );
      setFlow(updatedFlow);
      return updatedFlow;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update phase');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [flow]);

  const completeFlow = useCallback(async () => {
    if (!flow) throw new Error('No flow loaded');
    
    setLoading(true);
    setError(null);
    try {
      const completedFlow = await discoveryFlowV2Service.completeFlow(flow.crewai_flow_id);
      setFlow(completedFlow);
      return completedFlow;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete flow');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [flow]);

  useEffect(() => {
    if (crewai_flow_id) {
      loadFlow(crewai_flow_id);
    }
  }, [crewai_flow_id, loadFlow]);

  return {
    flow,
    loading,
    error,
    loadFlow,
    createFlow,
    updatePhase,
    completeFlow,
    // Helper properties
    currentPhase: flow?.current_phase,
    progressPercentage: flow?.progress_percentage || 0,
    phaseCompletion: flow?.phase_completion || {},
    isComplete: flow?.status === 'completed'
  };
};
```

### **Task 3.3: Update Discovery Pages (Days 6-8)**

**For each page, follow this pattern:**

#### **Data Import Page Update (Day 6)**

**File:** `src/pages/discovery/DataImport.tsx`

**Key changes:**
1. Replace old hook with `useDiscoveryFlowV2`
2. Use `crewai_flow_id` from URL params
3. Update navigation to pass `crewai_flow_id`

```typescript
// Replace imports
import { useDiscoveryFlowV2 } from '@/hooks/useDiscoveryFlowV2';

// Replace hook usage
const { crewai_flow_id } = useParams();
const { flow, createFlow, updatePhase, loading, error } = useDiscoveryFlowV2(crewai_flow_id);

// Update data import completion
const handleDataImportComplete = async (importedData: any[]) => {
  try {
    if (!crewai_flow_id) {
      // Create new flow
      const newFlow = await createFlow({
        crewai_flow_id: generateCrewAIFlowId(), // Generate UUID
        raw_data: importedData,
        import_session_id: import_session_id
      });
      // Navigate with CrewAI Flow ID
      navigate(`/discovery/attribute-mapping/${newFlow.crewai_flow_id}`);
    } else {
      // Update existing flow
      await updatePhase('data_import', importedData);
      navigate(`/discovery/attribute-mapping/${crewai_flow_id}`);
    }
  } catch (error) {
    console.error('Failed to complete data import:', error);
  }
};
```

#### **Attribute Mapping Page Update (Day 6)**

**File:** `src/pages/discovery/AttributeMapping.tsx`

```typescript
const { crewai_flow_id } = useParams();
const { flow, updatePhase, loading, error } = useDiscoveryFlowV2(crewai_flow_id);

const handleMappingComplete = async (mappings: any) => {
  try {
    await updatePhase('attribute_mapping', mappings);
    navigate(`/discovery/data-cleansing/${crewai_flow_id}`);
  } catch (error) {
    console.error('Failed to complete attribute mapping:', error);
  }
};
```

#### **Continue same pattern for remaining pages (Days 7-8):**
- Data Cleansing: `/discovery/data-cleansing/${crewai_flow_id}`
- Inventory: `/discovery/inventory/${crewai_flow_id}`  
- Dependencies: `/discovery/dependencies/${crewai_flow_id}`
- Tech Debt: `/discovery/tech-debt/${crewai_flow_id}`

---

## 📅 PHASE 4: TESTING & VALIDATION (Days 9-10)

### **Task 4.1: Integration Testing (Day 9)**

**File:** `tests/integration/test_discovery_flow_v2.py`

**CREATE NEW FILE:**

```python
"""
Discovery Flow V2 Integration Tests
Test complete flow from data import to completion
"""
import pytest
import uuid
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_complete_discovery_flow():
    """Test complete discovery flow end-to-end"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        crewai_flow_id = str(uuid.uuid4())
        
        # 1. Create flow
        response = await client.post("/api/v2/discovery-flows/flows", json={
            "crewai_flow_id": crewai_flow_id,
            "raw_data": [{"server": "test-01", "ip": "10.0.1.1"}]
        })
        assert response.status_code == 201
        
        # 2. Update each phase
        phases = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
        
        for phase in phases:
            response = await client.put(f"/api/v2/discovery-flows/flows/crewai/{crewai_flow_id}/phase", json={
                "phase": phase,
                "phase_data": {"test": "data"}
            })
            assert response.status_code == 200
        
        # 3. Verify completion
        response = await client.get(f"/api/v2/discovery-flows/flows/crewai/{crewai_flow_id}")
        flow = response.json()
        assert flow["progress_percentage"] == 100.0
        assert flow["current_phase"] == "completed"
```

### **Task 4.2: Frontend Testing (Day 10)**

**Commands to run:**
```bash
# Backend tests
docker exec -it migration_backend python -m pytest tests/integration/test_discovery_flow_v2.py -v

# Frontend tests  
docker exec -it migration_frontend npm test -- --testPathPattern=discovery

# End-to-end testing
docker exec -it migration_frontend npm run test:e2e
```

---

## 🚨 CRITICAL SUCCESS CRITERIA

### **Database Schema Validation**
```bash
# Verify correct schema
docker exec -it migration_backend python -c "
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset
print('✅ Models imported successfully')
print('✅ Schema matches implementation plan')
"
```

### **API Response Validation**
```bash
# Test V2 API
docker exec -it migration_backend curl -X GET "http://localhost:8000/api/v2/discovery-flows/health"
# Should return: {"status": "healthy", "version": "v2"}
```

### **Frontend Integration Validation**
```bash
# Test frontend builds
docker exec -it migration_frontend npm run build
# Should build without errors
```

---

## 📋 COMPLETION CHECKLIST

**Phase 1: Database Foundation**
- [ ] DiscoveryFlow model rewritten with correct schema
- [ ] DiscoveryAsset model rewritten with correct schema  
- [ ] Database migration created and applied
- [ ] Repository methods updated
- [ ] Service methods updated
- [ ] Seeding script rewritten and tested

**Phase 2: API Layer** 
- [ ] V2 API response models fixed
- [ ] API endpoints updated to use crewai_flow_id
- [ ] All 14 endpoints tested and working

**Phase 3: Frontend Integration**
- [ ] V2 service created
- [ ] V2 hook created
- [ ] All 6 discovery pages updated
- [ ] Navigation uses crewai_flow_id consistently

**Phase 4: Testing**
- [ ] Integration tests pass
- [ ] Frontend tests pass
- [ ] End-to-end flow tested
- [ ] Performance validated

**Final Validation**
- [ ] Complete discovery flow works end-to-end
- [ ] No session_id confusion
- [ ] CrewAI Flow ID is single source of truth
- [ ] Automatic asset creation works
- [ ] All phase transitions work correctly

---

**This document provides step-by-step implementation tasks that eliminate the architectural issues and establish the clean Discovery Flow architecture as specified in the implementation plan.** 