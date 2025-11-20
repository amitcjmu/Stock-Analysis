# Multi-Type Data Import Architecture - Revised Design (GPT-5 Feedback)

**Date**: 2025-01-11
**Status**: Design Review - Addressing GPT-5 Feedback
**Authors**: Claude Code (Sonnet 4.5), Architecture Review by GPT-5

---

## Executive Summary

This document revises the initial multi-type data import design based on critical feedback from GPT-5's architecture review. The key insight: **we already have the schema we need** - `data_imports`, `raw_import_records`, and `import_processing_steps` tables can handle all four import types without new tables.

### Key Changes from Initial Design

| Initial Proposal | GPT-5 Feedback | Revised Approach |
|-----------------|----------------|------------------|
| New `data_import_batches` table | ❌ Duplicates existing `data_imports` | ✅ Extend `data_imports` with `import_category` enum |
| New `data_import_flows` table | ❌ Duplicates MFO child flow pattern | ✅ Create `DataImportChildFlowService` |
| 12 new JSONB columns on Asset | ❌ Conflicts with existing models | ✅ Use `AssetDependency`, `PerformanceFieldsMixin`, `asset_custom_attributes` |
| Generic processor factory | ❌ No clear service boundary | ✅ Processors in `service_handlers/` with child flow service |
| New background execution | ❌ Reinventing existing pattern | ✅ Use existing `background_execution_service` |

---

## 1. Existing Schema Analysis

### 1.1 Current Data Import Tables (Already Exist!)

**Table: `migration.data_imports`** (backend/app/models/data_import/core.py:30-189)
```python
class DataImport(Base):
    # ✅ Already has everything we need
    id                    # UUID primary key
    client_account_id     # Multi-tenant isolation
    engagement_id         # Multi-tenant isolation
    master_flow_id        # Links to MFO (ADR-006)

    import_name           # User-defined name
    import_type           # ✅ 'cmdb', 'asset_inventory' - ADD new types here!
    description           # Detailed description

    # File metadata
    filename              # Original file name
    file_size             # File size in bytes
    mime_type             # MIME type (csv, xlsx, json, xml)
    source_system         # e.g., 'ServiceNow', 'Movere', 'Azure Migrate'

    # Job status (perfect for progress tracking)
    status                # 'pending', 'processing', 'completed', 'failed'
    progress_percentage   # 0.0-100.0
    total_records         # Total rows detected
    processed_records     # Rows successfully processed
    failed_records        # Rows that failed

    imported_by           # User ID
    error_message         # Error summary
    error_details         # JSONB error details

    # Timestamps
    started_at            # When processing began
    completed_at          # When processing finished
    created_at            # Record creation
    updated_at            # Last update
```

**Table: `migration.raw_import_records`** (backend/app/models/data_import/core.py:191-304)
```python
class RawImportRecord(Base):
    # ✅ Stores raw CSV/Excel/JSON data before transformation
    id                    # UUID primary key
    data_import_id        # ✅ FK to data_imports (NOT master_flow_id!)
    client_account_id     # Denormalized for efficient queries
    engagement_id         # Denormalized
    master_flow_id        # Denormalized (links to MFO)

    row_number            # Original row number from file
    raw_data              # JSONB - original, unaltered row data
    cleansed_data         # JSONB - after type casting

    validation_errors     # JSONB - array of validation errors
    processing_notes      # Text notes/warnings

    is_processed          # Boolean - successfully transformed?
    is_valid              # Boolean - passed validation?
    asset_id              # FK to assets (if asset created)

    created_at            # Record creation
    processed_at          # When processed
```

**Table: `migration.import_processing_steps`** (backend/app/models/data_import/core.py:306-389)
```python
class ImportProcessingStep(Base):
    # ✅ Tracks execution steps - PERFECT for agent instrumentation!
    id                    # UUID primary key
    data_import_id        # FK to data_imports

    step_name             # 'validation', 'field_mapping', 'enrichment'
    step_order            # Sequential order (1, 2, 3...)
    status                # 'pending', 'running', 'completed', 'failed'

    description           # What this step does
    input_data            # JSONB - input snapshot
    output_data           # JSONB - output snapshot
    error_details         # JSONB - detailed errors

    records_processed     # Count of records processed
    duration_seconds      # Step duration

    started_at            # Step start time
    completed_at          # Step completion time
```

### 1.2 Existing Asset Enrichment Models (No New JSONB Columns Needed!)

**Table: `migration.asset_dependencies`** (backend/app/models/asset/relationships.py:27-123)
```python
class AssetDependency(Base):
    # ✅ Already exists! Handles app-to-server mappings, network dependencies
    id                    # UUID primary key
    client_account_id     # Multi-tenant isolation
    engagement_id         # Multi-tenant isolation

    asset_id              # The asset that has the dependency
    depends_on_asset_id   # The asset being depended upon
    dependency_type       # 'database', 'application', 'storage', 'network'
    criticality           # 'low', 'medium', 'high'
    description           # Dependency description
    confidence_score      # 0.0-1.0 (1.0=manual, <1.0=auto-detected)

    # ✅ Network Discovery Fields (Issue #833) - Already exist!
    port                  # Network port
    protocol_name         # 'TCP', 'UDP', 'HTTP', etc.
    conn_count            # Number of connections
    bytes_total           # Total bytes transferred
    first_seen            # First detection timestamp
    last_seen             # Last detection timestamp
```

**Mixin: `PerformanceFieldsMixin`** (backend/app/models/asset/performance_fields.py:6-43)
```python
class PerformanceFieldsMixin:
    # ✅ Already on Asset model! Handles infrastructure performance data
    cpu_utilization_percent      # Average CPU %
    memory_utilization_percent   # Average memory %
    disk_iops                    # Disk IOPS
    network_throughput_mbps      # Network throughput

    completeness_score           # Data completeness
    quality_score                # Overall quality
    confidence_score             # Confidence level

    current_monthly_cost         # Current cost
    estimated_cloud_cost         # Estimated cloud cost
```

**Table: `migration.asset_custom_attributes`** (Exists - For Sensitive Data)
```python
# ✅ Use this for PII/compliance data instead of new JSONB columns
# Stores key-value pairs with data classification metadata
```

---

## 2. Revised Architecture Design

### 2.1 Schema Extensions (Minimal Changes)

**Migration: `094_add_import_category_enum.py`** (NEW)
```python
"""Add import_category enum to data_imports table"""

def upgrade():
    # Add import_category column (extends existing import_type)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'data_imports'
                AND column_name = 'import_category'
            ) THEN
                ALTER TABLE migration.data_imports
                ADD COLUMN import_category VARCHAR(50);

                -- Populate from existing import_type for backward compatibility
                UPDATE migration.data_imports
                SET import_category = CASE
                    WHEN import_type IN ('cmdb', 'asset_inventory') THEN 'cmdb_export'
                    ELSE import_type
                END;

                COMMENT ON COLUMN migration.data_imports.import_category IS
                'Import category: cmdb_export, app_discovery, infrastructure, sensitive_data';
            END IF;
        END $$;
    """)

    # Add processing_config JSONB (type-specific configurations)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'data_imports'
                AND column_name = 'processing_config'
            ) THEN
                ALTER TABLE migration.data_imports
                ADD COLUMN processing_config JSONB DEFAULT '{}'::jsonb;

                COMMENT ON COLUMN migration.data_imports.processing_config IS
                'Type-specific processing configurations (agents, enrichment targets, etc.)';
            END IF;
        END $$;
    """)

def downgrade():
    op.execute("""
        ALTER TABLE migration.data_imports
        DROP COLUMN IF EXISTS import_category,
        DROP COLUMN IF EXISTS processing_config;
    """)
```

**No Other Database Changes Needed!** ✅

---

## 3. Service Layer Architecture

### 3.1 Child Flow Service (NEW - Replaces Direct DiscoveryFlowService Usage)

**File: `backend/app/services/data_import/child_flow_service.py`** (NEW)
```python
"""
Data Import Child Flow Service

Handles master + child flow creation for data imports following MFO pattern.
Replaces direct DiscoveryFlowService instantiation per GPT-5 feedback.
"""

from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.models.data_import import DataImport, ImportProcessingStep
from app.models.discovery_flow import DiscoveryFlow

logger = get_logger(__name__)


class DataImportChildFlowService:
    """
    Manages data import flows using MFO two-table pattern.

    Master Flow (crewai_flow_state_extensions):
      - High-level lifecycle: 'running', 'paused', 'completed'
      - Cross-flow coordination

    Child Flow (discovery_flows):
      - Operational decisions: phases, validations, UI state
      - Import-specific metadata (data_import_id, selected applications)

    Per ADR-006, ADR-012.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.mfo = MasterFlowOrchestrator(db, context)

    async def create_import_flow(
        self,
        data_import_id: UUID,
        import_category: str,
        processing_config: Dict[str, Any],
    ) -> Dict[str, UUID]:
        """
        Create master + child flow for data import (atomic transaction).

        Args:
            data_import_id: UUID of data_imports record
            import_category: 'cmdb_export', 'app_discovery', etc.
            processing_config: Type-specific config (agents, enrichment targets)

        Returns:
            {
                'master_flow_id': UUID,
                'child_flow_id': UUID (discovery_flow.id)
            }

        Raises:
            FlowError: If flow creation fails
        """
        async with self.db.begin():
            # Step 1: Create master flow via MFO
            master_flow = await self.mfo.create_master_flow(
                flow_type="data_import",
                flow_name=f"Data Import - {import_category}",
                initial_phase="upload",
                metadata={
                    "data_import_id": str(data_import_id),
                    "import_category": import_category,
                    "processing_config": processing_config,
                }
            )

            # Step 2: Create child flow (discovery_flows) - operational state
            child_flow = DiscoveryFlow(
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                master_flow_id=master_flow.flow_id,
                data_import_id=data_import_id,  # ✅ Link to data import

                # Initial state
                current_phase="upload",
                phase_status="completed",  # Upload already done

                # Import-specific metadata
                flow_context={
                    "import_category": import_category,
                    "processing_config": processing_config,
                    "agents_required": processing_config.get("agent_count", 4),
                }
            )
            self.db.add(child_flow)
            await self.db.flush()

            # Step 3: Update data_imports.master_flow_id
            data_import = await self.db.get(DataImport, data_import_id)
            data_import.master_flow_id = master_flow.flow_id

            logger.info(
                f"✅ Created master flow {master_flow.flow_id} + "
                f"child flow {child_flow.id} for import {data_import_id}"
            )

            return {
                "master_flow_id": master_flow.flow_id,
                "child_flow_id": child_flow.id,
            }

    async def advance_to_validation(
        self,
        master_flow_id: UUID,
    ) -> None:
        """
        Advance flow to validation phase.

        Updates master flow phase and child flow operational state.
        """
        async with self.db.begin():
            # Update master flow phase
            await self.mfo.update_phase(
                master_flow_id=master_flow_id,
                new_phase="validation",
            )

            # Update child flow operational state
            child_flow = await self._get_child_flow_by_master_id(master_flow_id)
            child_flow.current_phase = "validation"
            child_flow.phase_status = "in_progress"

            logger.info(f"✅ Advanced flow {master_flow_id} to validation phase")

    async def advance_to_enrichment(
        self,
        master_flow_id: UUID,
        validation_results: Dict[str, Any],
    ) -> None:
        """
        Advance flow to enrichment phase.

        Args:
            master_flow_id: Master flow UUID
            validation_results: Results from validation agents (JSONB)
        """
        async with self.db.begin():
            await self.mfo.update_phase(
                master_flow_id=master_flow_id,
                new_phase="enrichment",
            )

            child_flow = await self._get_child_flow_by_master_id(master_flow_id)
            child_flow.current_phase = "enrichment"
            child_flow.phase_status = "in_progress"
            child_flow.flow_context["validation_results"] = validation_results

            logger.info(f"✅ Advanced flow {master_flow_id} to enrichment phase")

    async def mark_completed(
        self,
        master_flow_id: UUID,
        enrichment_summary: Dict[str, Any],
    ) -> None:
        """
        Mark flow as completed.

        Updates master flow status to 'completed' and child flow with results.
        """
        async with self.db.begin():
            await self.mfo.complete_flow(master_flow_id)

            child_flow = await self._get_child_flow_by_master_id(master_flow_id)
            child_flow.current_phase = "complete"
            child_flow.phase_status = "completed"
            child_flow.flow_context["enrichment_summary"] = enrichment_summary

            # Update data_imports.status
            data_import_id = UUID(child_flow.flow_context.get("data_import_id"))
            data_import = await self.db.get(DataImport, data_import_id)
            data_import.status = "completed"
            data_import.completed_at = datetime.utcnow()

            logger.info(f"✅ Marked flow {master_flow_id} as completed")

    async def _get_child_flow_by_master_id(self, master_flow_id: UUID) -> DiscoveryFlow:
        """Get child flow by master flow ID."""
        from sqlalchemy import select

        stmt = select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == master_flow_id,
            DiscoveryFlow.client_account_id == self.context.client_account_id,
            DiscoveryFlow.engagement_id == self.context.engagement_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
```

### 3.2 Processor Factory (Revised - In `service_handlers/`)

**File: `backend/app/services/data_import/service_handlers/__init__.py`** (NEW)
```python
"""
Data Import Processor Factory

Creates type-specific processors following modular handler pattern.
Housed under service_handlers/ per GPT-5 feedback.
"""

from typing import Dict, Type
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

logger = get_logger(__name__)


class BaseDataImportProcessor(ABC):
    """Base class for type-specific import processors."""

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        agent_pool: TenantScopedAgentPool,
    ):
        self.db = db
        self.context = context
        self.agent_pool = agent_pool

    @abstractmethod
    async def validate_data(
        self,
        data_import_id: UUID,
    ) -> Dict[str, Any]:
        """
        Run validation agents for this import type.

        Returns:
            {
                'is_valid': bool,
                'agent_results': List[AgentValidationResult],
                'error_count': int,
                'warning_count': int,
            }
        """
        pass

    @abstractmethod
    async def enrich_assets(
        self,
        data_import_id: UUID,
        validation_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run enrichment agents to populate asset attributes.

        Returns:
            {
                'assets_created': int,
                'assets_updated': int,
                'enrichment_details': Dict[str, Any],
            }
        """
        pass


class DataImportProcessorFactory:
    """Creates type-specific processors."""

    _processors: Dict[str, Type[BaseDataImportProcessor]] = {}

    @classmethod
    def register_processor(
        cls,
        import_category: str,
        processor_class: Type[BaseDataImportProcessor],
    ):
        """Register a processor for an import category."""
        cls._processors[import_category] = processor_class
        logger.info(f"✅ Registered processor for '{import_category}'")

    @classmethod
    def create_processor(
        cls,
        import_category: str,
        db: AsyncSession,
        context: RequestContext,
        agent_pool: TenantScopedAgentPool,
    ) -> BaseDataImportProcessor:
        """Create a processor instance for the given import category."""
        processor_class = cls._processors.get(import_category)
        if not processor_class:
            raise ValueError(f"No processor registered for category: {import_category}")

        return processor_class(db, context, agent_pool)


# Import and register processors (auto-registration pattern)
from .cmdb_export_processor import CMDBExportProcessor
from .app_discovery_processor import ApplicationDiscoveryProcessor
from .infrastructure_processor import InfrastructureAssessmentProcessor
from .sensitive_data_processor import SensitiveDataProcessor

DataImportProcessorFactory.register_processor("cmdb_export", CMDBExportProcessor)
DataImportProcessorFactory.register_processor("app_discovery", ApplicationDiscoveryProcessor)
DataImportProcessorFactory.register_processor("infrastructure", InfrastructureAssessmentProcessor)
DataImportProcessorFactory.register_processor("sensitive_data", SensitiveDataProcessor)
```

### 3.3 Example Processor: Application Discovery

**File: `backend/app/services/data_import/service_handlers/app_discovery_processor.py`** (NEW)
```python
"""
Application Discovery Processor

Handles application portfolio and dependency scan imports.
Enriches: AssetDependency table (app-to-server mappings, integrations).
"""

from uuid import UUID
from typing import Dict, Any, List
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.data_import import DataImport, RawImportRecord, ImportProcessingStep
from app.models.asset import Asset
from app.models.asset.relationships import AssetDependency
from app.services.multi_model_service import multi_model_service, TaskComplexity

from .base_processor import BaseDataImportProcessor

logger = get_logger(__name__)


class ApplicationDiscoveryProcessor(BaseDataImportProcessor):
    """
    Processes application discovery data imports.

    Expected Data Structure:
    {
        "source_app": "CustomerPortal",
        "target_app": "InventoryDB",
        "dependency_type": "database",
        "port": 5432,
        "protocol": "TCP",
        "criticality": "high"
    }

    Enriches:
    - AssetDependency table (app-to-server mappings)
    - Asset.integration_points (JSONB - external API dependencies)
    """

    async def validate_data(
        self,
        data_import_id: UUID,
    ) -> Dict[str, Any]:
        """
        Run 5 validation agents for application discovery data.

        Agents:
        1. Schema Validation Agent (shared)
        2. Dependency Validation Agent (circular dependencies, orphaned apps)
        3. Port/Protocol Validation Agent (valid port ranges, protocol names)
        4. Criticality Validation Agent (valid criticality levels)
        5. Duplicate Detection Agent (duplicate app-to-app relationships)
        """
        # Create processing step for tracking
        step = ImportProcessingStep(
            data_import_id=data_import_id,
            step_name="validation",
            step_order=1,
            status="running",
            description="Running 5 validation agents",
        )
        self.db.add(step)
        await self.db.flush()

        # Fetch raw records
        stmt = select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import_id,
            RawImportRecord.client_account_id == self.context.client_account_id,
        )
        result = await self.db.execute(stmt)
        raw_records = result.scalars().all()

        # Agent 1: Schema Validation (via shared agent)
        schema_agent = await self.agent_pool.get_agent("data_validation")
        schema_results = await schema_agent.execute(
            task="Validate application discovery schema",
            context={
                "expected_fields": ["source_app", "target_app", "dependency_type"],
                "raw_records": [r.raw_data for r in raw_records],
            }
        )

        # Agent 2: Dependency Validation (circular dependencies)
        dependency_agent = await self.agent_pool.get_agent("dependency_analysis")
        dependency_results = await dependency_agent.execute(
            task="Check for circular dependencies and orphaned applications",
            context={
                "dependencies": [r.raw_data for r in raw_records],
            }
        )

        # Agent 3: Port/Protocol Validation
        # Use multi_model_service for LLM tracking (MANDATORY per CLAUDE.md)
        port_validation_prompt = f"""
        Validate port and protocol configurations in application dependencies.

        Rules:
        - Valid port range: 1-65535
        - Valid protocols: TCP, UDP, HTTP, HTTPS, gRPC, AMQP
        - Common port-protocol pairs (e.g., 5432=PostgreSQL/TCP)

        Dependencies: {[r.raw_data for r in raw_records[:10]]}

        Return JSON:
        {{
            "is_valid": bool,
            "invalid_ports": [{{row_number, port, reason}}],
            "protocol_mismatches": [{{row_number, port, protocol, expected_protocol}}]
        }}
        """

        port_validation_response = await multi_model_service.generate_response(
            prompt=port_validation_prompt,
            task_type="validation",
            complexity=TaskComplexity.SIMPLE,  # Simple validation
            client_account_id=str(self.context.client_account_id),
            engagement_id=str(self.context.engagement_id),
        )
        port_results = json.loads(port_validation_response)

        # Agent 4: Criticality Validation
        # (Similar pattern using agent or LLM)

        # Agent 5: Duplicate Detection
        # (Similar pattern)

        # Aggregate results
        agent_results = [
            {
                "agent_name": "Schema Validation",
                "status": "completed" if schema_results["is_valid"] else "failed",
                "error_count": len(schema_results.get("errors", [])),
                "warning_count": 0,
            },
            {
                "agent_name": "Dependency Analysis",
                "status": "completed" if dependency_results["is_valid"] else "failed",
                "error_count": len(dependency_results.get("circular_deps", [])),
                "warning_count": len(dependency_results.get("orphaned_apps", [])),
            },
            {
                "agent_name": "Port/Protocol Validation",
                "status": "completed" if port_results["is_valid"] else "failed",
                "error_count": len(port_results.get("invalid_ports", [])),
                "warning_count": len(port_results.get("protocol_mismatches", [])),
            },
            # ... Agent 4, 5 results
        ]

        # Update processing step
        step.status = "completed"
        step.completed_at = datetime.utcnow()
        step.output_data = {
            "agent_results": agent_results,
        }

        total_errors = sum(r["error_count"] for r in agent_results)
        total_warnings = sum(r["warning_count"] for r in agent_results)

        return {
            "is_valid": total_errors == 0,
            "agent_results": agent_results,
            "error_count": total_errors,
            "warning_count": total_warnings,
        }

    async def enrich_assets(
        self,
        data_import_id: UUID,
        validation_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich AssetDependency table with application dependencies.

        Creates/updates:
        - AssetDependency records (source_app → target_app)
        - Asset.integration_points JSONB (external APIs)
        """
        # Create processing step
        step = ImportProcessingStep(
            data_import_id=data_import_id,
            step_name="enrichment",
            step_order=2,
            status="running",
            description="Creating asset dependencies from application discovery data",
        )
        self.db.add(step)
        await self.db.flush()

        # Fetch raw records
        stmt = select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import_id,
            RawImportRecord.is_valid == True,  # Only valid records
        )
        result = await self.db.execute(stmt)
        raw_records = result.scalars().all()

        dependencies_created = 0
        dependencies_updated = 0

        for record in raw_records:
            data = record.raw_data

            # Find or create source asset
            source_asset = await self._find_or_create_asset(
                asset_name=data["source_app"],
                asset_type="application",
            )

            # Find or create target asset
            target_asset = await self._find_or_create_asset(
                asset_name=data["target_app"],
                asset_type="application",
            )

            # Check if dependency already exists
            existing_dep_stmt = select(AssetDependency).where(
                AssetDependency.asset_id == source_asset.id,
                AssetDependency.depends_on_asset_id == target_asset.id,
                AssetDependency.client_account_id == self.context.client_account_id,
            )
            existing_dep_result = await self.db.execute(existing_dep_stmt)
            existing_dep = existing_dep_result.scalar_one_or_none()

            if existing_dep:
                # Update existing dependency
                existing_dep.dependency_type = data.get("dependency_type", "application")
                existing_dep.criticality = data.get("criticality", "medium")
                existing_dep.port = data.get("port")
                existing_dep.protocol_name = data.get("protocol")
                existing_dep.confidence_score = 0.85  # Auto-detected from import
                dependencies_updated += 1
            else:
                # Create new dependency
                new_dep = AssetDependency(
                    client_account_id=self.context.client_account_id,
                    engagement_id=self.context.engagement_id,
                    asset_id=source_asset.id,
                    depends_on_asset_id=target_asset.id,
                    dependency_type=data.get("dependency_type", "application"),
                    criticality=data.get("criticality", "medium"),
                    port=data.get("port"),
                    protocol_name=data.get("protocol"),
                    confidence_score=0.85,
                    description=f"Discovered from {data_import.filename}",
                )
                self.db.add(new_dep)
                dependencies_created += 1

            # Mark record as processed
            record.is_processed = True
            record.processed_at = datetime.utcnow()
            record.asset_id = source_asset.id

        # Update processing step
        step.status = "completed"
        step.completed_at = datetime.utcnow()
        step.records_processed = len(raw_records)
        step.output_data = {
            "dependencies_created": dependencies_created,
            "dependencies_updated": dependencies_updated,
        }

        logger.info(
            f"✅ Enriched {dependencies_created} new dependencies, "
            f"updated {dependencies_updated} existing dependencies"
        )

        return {
            "assets_created": 0,  # No new assets, only dependencies
            "assets_updated": dependencies_created + dependencies_updated,
            "enrichment_details": {
                "dependencies_created": dependencies_created,
                "dependencies_updated": dependencies_updated,
            },
        }

    async def _find_or_create_asset(
        self,
        asset_name: str,
        asset_type: str,
    ) -> Asset:
        """Find existing asset or create placeholder."""
        stmt = select(Asset).where(
            Asset.name == asset_name,
            Asset.asset_type == asset_type,
            Asset.client_account_id == self.context.client_account_id,
            Asset.engagement_id == self.context.engagement_id,
        )
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()

        if not asset:
            asset = Asset(
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                name=asset_name,
                asset_type=asset_type,
                discovery_source="application_discovery_import",
            )
            self.db.add(asset)
            await self.db.flush()

        return asset
```

---

## 4. Background Execution (Use Existing Service!)

**NO NEW BACKGROUND SERVICE** - Use existing `BackgroundExecutionService`:

**File: `backend/app/services/data_import/orchestrator.py`** (Revised)
```python
"""
Data Import Orchestrator

Coordinates upload → validation → enrichment flow using existing services.
"""

from uuid import UUID
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from app.services.data_import.background_execution_service import BackgroundExecutionService
from app.services.data_import.child_flow_service import DataImportChildFlowService
from app.services.data_import.service_handlers import DataImportProcessorFactory

logger = get_logger(__name__)


class DataImportOrchestrator:
    """
    Orchestrates data import processing pipeline.

    Flow:
    1. Create master + child flow (DataImportChildFlowService)
    2. Queue background execution (BackgroundExecutionService) ✅
    3. Processor runs validation → enrichment
    4. Update flow status to completed
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.child_flow_service = DataImportChildFlowService(db, context)
        self.agent_pool = TenantScopedAgentPool.get_instance()
        # ✅ Use existing background execution service (GPT-5 feedback)
        self.background_service = BackgroundExecutionService(
            db, str(context.client_account_id)
        )

    async def start_import_processing(
        self,
        data_import_id: UUID,
        import_category: str,
        processing_config: Dict[str, Any],
    ) -> Dict[str, UUID]:
        """
        Start data import processing in background.

        Returns:
            {
                'master_flow_id': UUID,
                'child_flow_id': UUID,
            }
        """
        # Step 1: Create flows (atomic)
        flows = await self.child_flow_service.create_import_flow(
            data_import_id=data_import_id,
            import_category=import_category,
            processing_config=processing_config,
        )

        # Step 2: Queue background processing (after transaction commits)
        # ✅ Use existing background_execution_service (GPT-5 feedback)
        await self.background_service.start_background_import_execution(
            master_flow_id=flows["master_flow_id"],
            data_import_id=data_import_id,
            import_category=import_category,
            context=self.context,
        )

        logger.info(
            f"✅ Started import processing for {import_category} "
            f"(flow: {flows['master_flow_id']})"
        )

        return flows

    async def _execute_import_processing(
        self,
        master_flow_id: UUID,
        data_import_id: UUID,
        import_category: str,
    ) -> None:
        """
        Execute import processing (validation → enrichment).

        This runs in background task.
        """
        try:
            # Get processor for import category
            processor = DataImportProcessorFactory.create_processor(
                import_category=import_category,
                db=self.db,
                context=self.context,
                agent_pool=self.agent_pool,
            )

            # Phase 1: Validation
            await self.child_flow_service.advance_to_validation(master_flow_id)
            validation_results = await processor.validate_data(data_import_id)

            if not validation_results["is_valid"]:
                logger.error(f"❌ Validation failed for import {data_import_id}")
                await self.child_flow_service.mark_failed(
                    master_flow_id,
                    error="Validation failed",
                )
                return

            # Phase 2: Enrichment
            await self.child_flow_service.advance_to_enrichment(
                master_flow_id,
                validation_results,
            )
            enrichment_summary = await processor.enrich_assets(
                data_import_id,
                validation_results,
            )

            # Phase 3: Complete
            await self.child_flow_service.mark_completed(
                master_flow_id,
                enrichment_summary,
            )

            logger.info(f"✅ Import processing completed for {data_import_id}")

        except Exception as e:
            logger.error(f"❌ Import processing failed: {e}", exc_info=True)
            await self.child_flow_service.mark_failed(master_flow_id, str(e))
```

---

## 5. Agent Instrumentation (LLM Tracking)

Per GPT-5 feedback, document how processors use `multi_model_service` and log to `import_processing_steps`:

**Pattern Example** (from ApplicationDiscoveryProcessor above):
```python
# 1. Create processing step BEFORE agent execution
step = ImportProcessingStep(
    data_import_id=data_import_id,
    step_name="validation",
    step_order=1,
    status="running",
    description="Running 5 validation agents",
)
self.db.add(step)
await self.db.flush()

# 2. Use multi_model_service for LLM calls (MANDATORY)
response = await multi_model_service.generate_response(
    prompt=validation_prompt,
    task_type="validation",
    complexity=TaskComplexity.SIMPLE,  # or AGENTIC for complex tasks
    client_account_id=str(self.context.client_account_id),
    engagement_id=str(self.context.engagement_id),
)

# 3. Update processing step with results
step.status = "completed"
step.completed_at = datetime.utcnow()
step.output_data = {
    "agent_results": agent_results,
    "error_count": total_errors,
}

# 4. LLM usage automatically tracked to llm_usage_logs table (via multi_model_service)
# No additional tracking needed!
```

---

## 6. Frontend Wiring (Backward Compatible)

Per GPT-5 feedback, ensure frontend accepts both `master_flow_id` and `flow_id`:

**File: `src/lib/api/dataImportService.ts`** (Revised)
```typescript
import { apiClient } from './apiClient';

interface DataImportFlow {
  // ✅ Accept both master_flow_id and flow_id for backward compatibility
  master_flow_id?: string;
  flow_id?: string;  // Fallback during rollout

  data_import_id: string;
  import_category: 'cmdb_export' | 'app_discovery' | 'infrastructure' | 'sensitive_data';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  current_phase: 'upload' | 'validation' | 'enrichment' | 'complete';
  progress_percentage: number;

  validation_results?: AgentValidationResult[];
  enrichment_summary?: EnrichmentSummary;
}

export const dataImportService = {
  async uploadFile(
    file: File,
    import_category: DataImportFlow['import_category'],
    client_account_id: string,
    engagement_id: string,
  ): Promise<DataImportFlow> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_category', import_category);

    // ✅ Use shared API client with multi-tenant headers (GPT-5 feedback)
    const response = await apiClient<DataImportFlow>('/api/v1/data-import/upload', {
      method: 'POST',
      body: formData,  // ✅ Request body, NOT query params (CLAUDE.md)
      headers: {
        'X-Client-Account-ID': client_account_id,
        'X-Engagement-ID': engagement_id,
      },
    });

    return response;
  },

  async pollImportStatus(
    flow_id: string,  // Can be master_flow_id or flow_id
  ): Promise<DataImportFlow> {
    // ✅ Backward compatible during rollout
    const response = await apiClient<DataImportFlow>(
      `/api/v1/data-import/status/${flow_id}`,
      { method: 'GET' }
    );

    return response;
  },
};
```

---

## 7. MCP Integration (Feature-Flagged)

Per GPT-5 feedback, gate MCP servers behind feature flags:

**File: `backend/app/mcp/data_import_validator.py`** (NEW)
```python
"""
MCP Server: data-import-validator

Provides tools for external validation of data imports.
Feature-flagged per GPT-5 feedback.
"""

from app.core.feature_flags import is_feature_enabled

if is_feature_enabled("mcp_data_import_validator"):
    # Register MCP server tools
    @mcp_tool
    async def validate_cmdb_file(file_path: str, expected_schema: str) -> Dict[str, Any]:
        """Validate CMDB file against expected schema."""
        # Implementation aligned with CMDBExportProcessor validation logic
        pass

    @mcp_tool
    async def detect_data_type(file_path: str) -> Dict[str, str]:
        """Auto-detect import type from file content."""
        # Returns: { 'import_type': 'app_discovery', 'confidence': 0.92 }
        pass
else:
    logger.info("MCP data-import-validator server disabled (feature flag off)")
```

---

## 8. Sequence Diagrams (Validation Per GPT-5)

### 8.1 Master + Child Flow Creation

```
User                  API Endpoint          DataImportOrchestrator    DataImportChildFlowService    MasterFlowOrchestrator    Database
  |                         |                         |                         |                         |                   |
  |--POST /upload---------->|                         |                         |                         |                   |
  |                         |                         |                         |                         |                   |
  |                         |--start_import_--------->|                         |                         |                   |
  |                         |   processing()          |                         |                         |                   |
  |                         |                         |                         |                         |                   |
  |                         |                         |--create_import_flow---->|                         |                   |
  |                         |                         |                         |                         |                   |
  |                         |                         |                         |--create_master_flow---->|                   |
  |                         |                         |                         |                         |                   |
  |                         |                         |                         |                         |--INSERT--------->|
  |                         |                         |                         |                         | crewai_flow_      |
  |                         |                         |                         |                         | state_extensions  |
  |                         |                         |                         |                         |                   |
  |                         |                         |                         |<--master_flow_id--------|                   |
  |                         |                         |                         |                         |                   |
  |                         |                         |                         |--INSERT discovery_flows----------------->|
  |                         |                         |                         |   (child flow with master_flow_id)        |
  |                         |                         |                         |                         |                   |
  |                         |                         |                         |--UPDATE data_imports.master_flow_id----->|
  |                         |                         |                         |                         |                   |
  |                         |                         |<--{master_flow_id,------|                         |                   |
  |                         |                         |    child_flow_id}       |                         |                   |
  |                         |                         |                         |                         |                   |
  |                         |                         |--queue_background------>|                         |                   |
  |                         |                         |   _execution()          |                         |                   |
  |                         |                         |                         |                         |                   |
  |<--{master_flow_id}------|                         |                         |                         |                   |
  |                         |                         |                         |                         |                   |
```

### 8.2 Application Discovery Processing

```
Background Task        ApplicationDiscoveryProcessor    TenantScopedAgentPool    multi_model_service    Database
       |                            |                            |                         |              |
       |--validate_data()---------->|                            |                         |              |
       |                            |                            |                         |              |
       |                            |--INSERT import_processing_steps (validation, running)------------>|
       |                            |                            |                         |              |
       |                            |--get_agent('dependency_--->|                         |              |
       |                            |   analysis')               |                         |              |
       |                            |                            |                         |              |
       |                            |<--agent instance-----------|                         |              |
       |                            |                            |                         |              |
       |                            |--agent.execute()---------->|                         |              |
       |                            |   (circular dependency     |                         |              |
       |                            |    detection)              |                         |              |
       |                            |                            |                         |              |
       |                            |<--validation results-------|                         |              |
       |                            |                            |                         |              |
       |                            |--generate_response()-------------------------------->|              |
       |                            |   (port/protocol validation)                         |              |
       |                            |                            |                         |              |
       |                            |                            |                         |--INSERT----->|
       |                            |                            |                         | llm_usage_   |
       |                            |                            |                         | logs         |
       |                            |                            |                         |              |
       |                            |<--port validation results----------------------------              |
       |                            |                            |                         |              |
       |                            |--UPDATE import_processing_steps (completed)---------------------->|
       |                            |                            |                         |              |
       |<--{is_valid, agent_--------|                            |                         |              |
       |    results}                |                            |                         |              |
       |                            |                            |                         |              |
       |--enrich_assets()---------->|                            |                         |              |
       |                            |                            |                         |              |
       |                            |--INSERT import_processing_steps (enrichment, running)------------>|
       |                            |                            |                         |              |
       |                            |--SELECT raw_import_records (WHERE data_import_id = ...)--------->|
       |                            |                            |                         |              |
       |                            |<--raw_records[]---------------------------------------------       |
       |                            |                            |                         |              |
       |                            |--find_or_create_asset()-----------------------------------       |
       |                            |   (source_app)             |                         |              |
       |                            |                            |                         |              |
       |                            |--INSERT/UPDATE asset_dependencies---------------------------------|
       |                            |   (source → target)        |                         |              |
       |                            |                            |                         |              |
       |                            |--UPDATE raw_import_records (is_processed=true)----------------->|
       |                            |                            |                         |              |
       |                            |--UPDATE import_processing_steps (completed)---------------------->|
       |                            |                            |                         |              |
       |<--{assets_created,---------|                            |                         |              |
       |    enrichment_details}     |                            |                         |              |
       |                            |                            |                         |              |
```

---

## 9. Next Steps (Per GPT-5 Feedback)

### Phase 1: ADR Update (Week 1)
- [ ] Draft ADR-036: Multi-Type Data Import Architecture
  - Document how non-CMDB imports extend existing `data_imports` two-table model
  - Explain child flow pattern (DataImportChildFlowService)
  - Justify processor placement in `service_handlers/`
  - Describe agent instrumentation with `multi_model_service`

### Phase 2: Prototype (Week 2-3)
- [ ] Implement `DataImportChildFlowService`
- [ ] Implement `ApplicationDiscoveryProcessor` (one non-CMDB type)
- [ ] Migration `094_add_import_category_enum.py`
- [ ] Validate atomic master + child flow creation
- [ ] Verify no legacy DiscoveryFlowService direct instantiation

### Phase 3: Additional Processors (Week 4-5)
- [ ] Implement `InfrastructureAssessmentProcessor`
- [ ] Implement `SensitiveDataProcessor`
- [ ] Update `CMDBExportProcessor` to use new pattern

### Phase 4: Frontend Integration (Week 6)
- [ ] Update upload tiles to use `import_category`
- [ ] Implement backward-compatible polling (accepts `master_flow_id` or `flow_id`)
- [ ] Type-specific results components

### Phase 5: MCP Integration (Week 7)
- [ ] Implement `data-import-validator` MCP server (feature-flagged)
- [ ] Implement `enrichment-engine` MCP server (feature-flagged)
- [ ] Align schemas with backend processors

---

## 10. Key Differences from Initial Design

| Aspect | Initial Design | Revised Design (GPT-5) |
|--------|---------------|------------------------|
| **Tables** | New `data_import_batches`, `data_import_flows` | ✅ Extend existing `data_imports`, use `discovery_flows` |
| **Asset Enrichment** | 12 new JSONB columns on Asset | ✅ Use existing `AssetDependency`, `PerformanceFieldsMixin`, `asset_custom_attributes` |
| **Child Flow** | Generic child flow service | ✅ `DataImportChildFlowService` registered in flow config |
| **Processors** | Generic factory in services/ | ✅ `service_handlers/` following modular pattern |
| **Background Execution** | New mechanism | ✅ Use existing `BackgroundExecutionService` |
| **MCP Integration** | Always enabled | ✅ Feature-flagged, schema-aligned with processors |
| **LLM Tracking** | Documented but not instrumented | ✅ Explicit `multi_model_service` calls, logged to `import_processing_steps` |

---

## 11. Success Criteria (Unchanged)

1. ✅ Users can upload 4 different data types from single page
2. ✅ Each type shows appropriate security warnings + agent count
3. ✅ Real-time progress with per-agent validation status
4. ✅ Type-specific results (dependencies graph, performance metrics, compliance risks)
5. ✅ **NO NEW TABLES** - Extend existing `data_imports`, use existing enrichment models
6. ✅ **Child Flow Service** - `DataImportChildFlowService` registered in flow config
7. ✅ All flows registered with MFO (master + child pattern)
8. ✅ LLM usage automatically tracked to `llm_usage_logs` + `import_processing_steps`
9. ✅ **Use existing background_execution_service** - No new mechanisms
10. ✅ MCP servers feature-flagged and schema-aligned

---

## 12. Estimated Effort (Revised)

- **Backend**: ~3,000 LOC across 15 files (4-5 weeks) - **Reduced** from 5,000 LOC (reusing existing tables/services)
- **Frontend**: ~2,000 LOC across 10 files (3-4 weeks) - **Unchanged**
- **Testing**: 25+ tests (unit + integration + E2E) (2 weeks) - **Reduced** from 30+ tests
- **Total**: **8-10 weeks** with 2 developers - **Reduced** from 10-12 weeks

**Time Savings**: ~2 weeks by reusing existing schema and services

---

## Appendix A: Files to Create/Modify

### New Files (15)
1. `backend/alembic/versions/094_add_import_category_enum.py` (Migration)
2. `backend/app/services/data_import/child_flow_service.py` (Child flow service)
3. `backend/app/services/data_import/orchestrator.py` (Orchestrator)
4. `backend/app/services/data_import/service_handlers/__init__.py` (Factory)
5. `backend/app/services/data_import/service_handlers/base_processor.py` (Base class)
6. `backend/app/services/data_import/service_handlers/cmdb_export_processor.py`
7. `backend/app/services/data_import/service_handlers/app_discovery_processor.py`
8. `backend/app/services/data_import/service_handlers/infrastructure_processor.py`
9. `backend/app/services/data_import/service_handlers/sensitive_data_processor.py`
10. `backend/app/mcp/data_import_validator.py` (MCP server)
11. `backend/app/mcp/enrichment_engine.py` (MCP server)
12. `src/lib/api/dataImportService.ts` (Frontend API)
13-15. Frontend components (DataTypeCard, UploadProgressPanel, ResultsPreviewPanel)

### Modified Files (5)
1. `backend/app/services/data_import/import_service.py` (Remove direct DiscoveryFlowService usage)
2. `backend/app/services/data_import/background_execution_service/core.py` (Add import-specific method)
3. `src/pages/discovery/CMDBImport/CMDBImport.types.ts` (Add import_category types)
4. `src/pages/discovery/CMDBImport/utils/uploadCategories.ts` (Add new categories)
5. `src/pages/discovery/CMDBImport/components/CMDBUploadSection.tsx` (Use DataTypeCard)

**Total**: 20 files (vs 30 in initial design)

---

## Appendix B: Compliance Checklist

✅ **MFO Integration** (ADR-006): Two-table pattern with atomic master + child creation
✅ **Child Flow Service** (GPT-5): `DataImportChildFlowService` registered in flow config
✅ **Existing Schema Reuse** (GPT-5): Extend `data_imports`, use `AssetDependency`, `PerformanceFieldsMixin`
✅ **Processor Placement** (GPT-5): `service_handlers/` following modular pattern
✅ **Background Execution** (GPT-5): Use existing `BackgroundExecutionService`
✅ **LLM Tracking** (Oct 2025): `multi_model_service.generate_response()` + `import_processing_steps`
✅ **CrewAI Memory** (ADR-024): `memory=False`, use `TenantMemoryManager`
✅ **Multi-Tenant Isolation**: `client_account_id + engagement_id` on all queries
✅ **snake_case Fields**: All API contracts use snake_case
✅ **HTTP Polling**: 5s active / 15s waiting, no WebSockets
✅ **MCP Feature Flags** (GPT-5): Gate MCP servers, align schemas with processors
✅ **Frontend Backward Compatibility** (GPT-5): Accept both `master_flow_id` and `flow_id`

---

**END OF REVISED DESIGN DOCUMENT**
