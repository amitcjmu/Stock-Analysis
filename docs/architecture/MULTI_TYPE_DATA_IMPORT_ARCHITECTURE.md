# Multi-Type Data Import Architecture for Collection Flow

## Executive Summary

This architecture enables the Collection Flow to handle four distinct data import types (CMDB Export, Application Discovery, Infrastructure Assessment, Sensitive Data Assets) through a unified, scalable processing pipeline. The design leverages existing Master Flow Orchestrator (MFO) patterns, introduces specialized validation agents per import type, and implements intelligent data enrichment strategies that update different asset attributes based on the data source type. The architecture maintains the seven-layer enterprise pattern, multi-tenant isolation, and integrates seamlessly with existing CrewAI agent infrastructure while exposing key capabilities through Model Context Protocol (MCP) servers.

**Key Outcomes:**
- Single unified endpoint with type parameter (avoids endpoint sprawl)
- Specialized agent-based validation per data type (4-6 agents)
- Intelligent attribute enrichment based on import type
- MCP-compatible design for external tool integration
- Zero-downtime migration from current CMDB-only implementation

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Upload UI Layer)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │   CMDB   │  │   App    │  │  Infra   │  │ Sensitive│                   │
│  │  Export  │  │Discovery │  │Assessment│  │   Data   │                   │
│  │ (4 val)  │  │ (5 val)  │  │ (5 val)  │  │  (6 val) │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
│       │             │              │             │                          │
└───────┼─────────────┼──────────────┼─────────────┼──────────────────────────┘
        │             │              │             │
        └─────────────┴──────────────┴─────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI Endpoints)                            │
│  POST /api/v1/collection/data-import/analyze                                │
│  POST /api/v1/collection/data-import/execute                                │
│  GET  /api/v1/collection/data-import/status/{task_id}                      │
│                                                                             │
│  Request Body: { import_type, file, collection_flow_id }                   │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               SERVICE LAYER (Business Logic Orchestration)                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │            DataImportOrchestrationService                             │ │
│  │  - Route to type-specific processor based on import_type             │ │
│  │  - Coordinate validation agent pools                                 │ │
│  │  - Manage enrichment pipeline                                        │ │
│  └───────────────────┬───────────────────────────────────────────────────┘ │
│                      │                                                      │
│       ┌──────────────┼──────────────┬────────────────┬───────────────┐    │
│       ▼              ▼              ▼                ▼               ▼    │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  ┌─────────────────┐         │
│  │  CMDB   │  │   App    │  │   Infra    │  │   Sensitive     │         │
│  │Processor│  │Processor │  │ Processor  │  │  DataProcessor  │         │
│  └────┬────┘  └─────┬────┘  └──────┬─────┘  └────────┬────────┘         │
│       │             │               │                 │                   │
└───────┼─────────────┼───────────────┼─────────────────┼───────────────────┘
        │             │               │                 │
        ▼             ▼               ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              AGENT LAYER (CrewAI Validation & Enrichment)                   │
│                                                                             │
│  ┌──────────────────────┐  ┌────────────────────────┐                     │
│  │  CMDB Validation     │  │  App Discovery Val     │                     │
│  │  - FormatValidator   │  │  - DependencyAnalyzer  │                     │
│  │  - DuplicateDetector │  │  - AppToServerMapper   │                     │
│  │  - DataQualityAgent  │  │  - IntegrationDetector │                     │
│  │  - SchemaValidator   │  │  - APIDiscoveryAgent   │                     │
│  └──────────────────────┘  │  - DataFlowAnalyzer    │                     │
│                            └────────────────────────┘                     │
│  ┌──────────────────────┐  ┌────────────────────────┐                     │
│  │  Infra Assessment Val│  │  Sensitive Data Val    │                     │
│  │  - PerformanceAnalyzer│ │  - DataClassifier      │                     │
│  │  - TopologyMapper    │  │  - PIIDetector         │                     │
│  │  - CapacityAnalyzer  │  │  - ComplianceValidator │                     │
│  │  - NetworkValidator  │  │  - EncryptionChecker   │                     │
│  │  - EOLDetector       │  │  - AccessControlAgent  │                     │
│  └──────────────────────┘  │  - DataLineageTracker  │                     │
│                            └────────────────────────┘                     │
│                                                                             │
│  Agents use TenantScopedAgentPool (persistent, memory-enabled via          │
│  TenantMemoryManager per ADR-024)                                          │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│           REPOSITORY LAYER (Data Access & Enrichment Logic)                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │              EnrichmentStrategyRegistry                               │ │
│  │                                                                       │ │
│  │  cmdb_export → BaseAssetAttributes (name, type, location)            │ │
│  │  application_discovery → Dependencies, IntegrationPoints             │ │
│  │  infrastructure_assessment → Performance, NetworkTopology            │ │
│  │  sensitive_data → DataClassification, ComplianceFlags               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  MODEL LAYER (Database Schema)                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  Asset (Core Table - Extended per Import Type)              │           │
│  │  - id (UUID PK)                                             │           │
│  │  - asset_name, asset_type (CMDB base)                       │           │
│  │  - dependencies JSONB (App Discovery enrichment)            │           │
│  │  - integration_points JSONB (App Discovery enrichment)      │           │
│  │  - performance_metrics JSONB (Infra enrichment)             │           │
│  │  - network_topology JSONB (Infra enrichment)                │           │
│  │  - data_classification TEXT (Sensitive Data enrichment)     │           │
│  │  - compliance_scopes JSONB (Sensitive Data enrichment)      │           │
│  │  - enrichment_metadata JSONB (tracks all enrichments)       │           │
│  │  - client_account_id, engagement_id (Multi-tenant)          │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  DataImportTask (Background Processing Tracking)            │           │
│  │  - id (UUID PK)                                             │           │
│  │  - import_type (cmdb|app_discovery|infra|sensitive)         │           │
│  │  - collection_flow_id (FK to collection_flows)              │           │
│  │  - status (pending|processing|completed|failed)             │           │
│  │  - validation_results JSONB (agent validation outputs)      │           │
│  │  - enrichment_summary JSONB (what was enriched)             │           │
│  │  - error_details JSONB (if failed)                          │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  AssetEnrichment (Audit Trail for Enrichments)              │           │
│  │  - id (UUID PK)                                             │           │
│  │  - asset_id (FK to assets)                                  │           │
│  │  - enrichment_source (import_type)                          │           │
│  │  - enriched_attributes JSONB (before/after)                 │           │
│  │  - enrichment_timestamp                                     │           │
│  └─────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                   MCP INTEGRATION LAYER (External Tools)                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  MCP Server: data-import-validator                                    │ │
│  │  - Tool: validate_cmdb_file(file_path) → validation_report           │ │
│  │  - Tool: detect_data_type(file_path) → detected_type                 │ │
│  │  - Tool: suggest_mappings(columns) → field_mapping_suggestions       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  MCP Server: enrichment-engine                                        │ │
│  │  - Resource: asset_enrichment_schema → JSON schema for enrichments   │ │
│  │  - Tool: apply_enrichment(asset_id, data) → enrichment_result        │ │
│  │  - Tool: rollback_enrichment(enrichment_id) → rollback_status        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Context7 MCP Integration (Documentation Augmentation)               │ │
│  │  - Resolve library IDs for validation frameworks                     │ │
│  │  - Fetch latest documentation for data format standards              │ │
│  │  - Augment agent context with industry best practices                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. API Layer Components

#### DataImportController (`/backend/app/api/v1/endpoints/collection/data_import.py`)

**Responsibilities:**
- Unified endpoint for all import types (no endpoint sprawl)
- Request validation and tenant context extraction
- File upload handling with security checks
- Background task orchestration via Redis queue

**Key Endpoints:**

```python
@router.post("/data-import/analyze")
async def analyze_data_import(
    file: UploadFile,
    import_type: Literal["cmdb_export", "application_discovery", "infrastructure_assessment", "sensitive_data"],
    collection_flow_id: UUID,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
) -> DataImportAnalysisResponse:
    """
    Analyze uploaded file and suggest field mappings.

    - Detect file format (CSV, XLSX, JSON, XML)
    - Route to type-specific validator agents
    - Return validation results + suggested mappings
    - Create DataImportTask for tracking
    """

@router.post("/data-import/execute")
async def execute_data_import(
    task_id: UUID,
    confirmed_mappings: Dict[str, str],
    enrichment_options: Dict[str, Any],
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
) -> DataImportExecutionResponse:
    """
    Execute validated import with confirmed mappings.

    - Dispatch to Redis background queue
    - Create master flow state in MFO
    - Return task ID for status polling
    """

@router.get("/data-import/status/{task_id}")
async def get_import_status(
    task_id: UUID,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
) -> DataImportStatusResponse:
    """
    Poll import task status (HTTP polling, no WebSockets per ADR-010).

    - Returns: progress, validation results, enrichment summary
    - Includes agent insights from validation phase
    """
```

**Security Considerations:**
- File size limits (50MB for standard, 100MB for elevated, 200MB for high/max)
- MIME type validation (CSV, XLSX, JSON, XML only)
- Virus scanning integration (ClamAV via MCP server)
- Rate limiting per tenant (10 uploads/minute)

---

### 2. Service Layer Components

#### DataImportOrchestrationService (`/backend/app/services/collection/data_import_orchestrator.py`)

**Responsibilities:**
- Route requests to type-specific processors
- Coordinate agent pool initialization per import type
- Manage validation pipeline
- Handle enrichment strategy selection
- Integration with MFO for state management

**Key Methods:**

```python
class DataImportOrchestrationService:
    """
    Orchestrates multi-type data import with agent-based validation.

    Per CLAUDE.md requirements:
    - Uses TenantScopedAgentPool (no per-call Crew instantiation)
    - Integrates with MFO via master flow registration
    - Ensures multi-tenant isolation (client_account_id + engagement_id)
    - Uses TenantMemoryManager for agent learning (ADR-024)
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.agent_pool = TenantScopedAgentPool(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        self.memory_manager = TenantMemoryManager(
            crewai_service=None,  # Initialized lazily
            database_session=db
        )

    async def analyze_import(
        self,
        file_data: bytes,
        import_type: str,
        collection_flow_id: UUID
    ) -> DataImportAnalysis:
        """
        Step 1: Analyze file and suggest mappings.

        Flow:
        1. Detect file format and parse data
        2. Route to type-specific processor
        3. Initialize validation agent pool
        4. Run format validation
        5. Generate field mapping suggestions (via LLM)
        6. Store analysis in Redis cache

        Returns:
        - Detected columns and suggested mappings
        - Validation warnings (agent insights)
        - Recommended enrichment targets
        """

        # Detect format and parse
        file_format = self._detect_format(file_data)
        parsed_data = await self._parse_file(file_data, file_format)

        # Route to processor
        processor = self._get_processor(import_type)

        # Initialize agent pool for this import type
        agents = await self._initialize_agents(import_type)

        # Run validation
        validation_results = await processor.validate(
            data=parsed_data,
            agents=agents
        )

        # Generate mapping suggestions using LLM
        mappings = await self._generate_mappings(
            columns=parsed_data.columns,
            import_type=import_type,
            sample_data=parsed_data.head(5)
        )

        # Cache for execution phase
        cache_key = f"import_analysis:{self.context.engagement_id}:{collection_flow_id}"
        await self.redis.set(cache_key, json.dumps({
            "parsed_data": parsed_data.to_dict(),
            "validation_results": validation_results,
            "mappings": mappings
        }), ex=3600)

        return DataImportAnalysis(
            file_format=file_format,
            detected_columns=parsed_data.columns.tolist(),
            suggested_mappings=mappings,
            validation_warnings=validation_results.warnings,
            enrichment_targets=processor.get_enrichment_targets()
        )

    async def execute_import(
        self,
        task_id: UUID,
        confirmed_mappings: Dict[str, str],
        enrichment_options: Dict[str, Any]
    ) -> DataImportTask:
        """
        Step 2: Execute import with confirmed mappings.

        Flow:
        1. Retrieve cached analysis from Redis
        2. Register master flow with MFO
        3. Dispatch to background queue
        4. Background worker:
           a. Transform data using confirmed mappings
           b. Run duplicate detection
           c. Execute enrichment pipeline
           d. Update asset records atomically
           e. Store enrichment audit trail

        Returns:
        - DataImportTask for status polling
        """

        # Register with MFO (ADR-006)
        master_flow_id = await self.mfo.register_flow(
            flow_type="collection",
            child_flow_id=self.collection_flow_id,
            flow_configuration={
                "import_type": self.import_type,
                "enrichment_targets": enrichment_options
            }
        )

        # Create task record
        task = DataImportTask(
            id=task_id,
            import_type=self.import_type,
            collection_flow_id=self.collection_flow_id,
            master_flow_id=master_flow_id,
            status="pending",
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id
        )
        self.db.add(task)
        await self.db.commit()

        # Dispatch to background queue
        await self.redis.enqueue(
            queue="data_import",
            task={
                "task_id": str(task_id),
                "confirmed_mappings": confirmed_mappings,
                "enrichment_options": enrichment_options
            }
        )

        return task

    def _get_processor(self, import_type: str) -> DataImportProcessor:
        """Factory pattern for type-specific processors."""
        processors = {
            "cmdb_export": CMDBExportProcessor,
            "application_discovery": ApplicationDiscoveryProcessor,
            "infrastructure_assessment": InfrastructureAssessmentProcessor,
            "sensitive_data": SensitiveDataProcessor
        }
        return processors[import_type](self.db, self.context)

    async def _initialize_agents(self, import_type: str) -> List[Agent]:
        """
        Initialize validation agents for import type.

        Per ADR-015 and ADR-024:
        - Uses TenantScopedAgentPool (persistent agents)
        - Agents have memory=False (TenantMemoryManager used instead)
        - Warm up agents with import type context
        """
        agent_configs = {
            "cmdb_export": [
                "format_validator",
                "duplicate_detector",
                "data_quality_agent",
                "schema_validator"
            ],
            "application_discovery": [
                "dependency_analyzer",
                "app_to_server_mapper",
                "integration_detector",
                "api_discovery_agent",
                "data_flow_analyzer"
            ],
            "infrastructure_assessment": [
                "performance_analyzer",
                "topology_mapper",
                "capacity_analyzer",
                "network_validator",
                "eol_detector"
            ],
            "sensitive_data": [
                "data_classifier",
                "pii_detector",
                "compliance_validator",
                "encryption_checker",
                "access_control_agent",
                "data_lineage_tracker"
            ]
        }

        agents = []
        for agent_type in agent_configs[import_type]:
            agent = await self.agent_pool.get_or_create_agent(
                agent_type=agent_type,
                memory_enabled=False  # Per ADR-024
            )
            # Warm up with import context
            await agent.set_context({
                "import_type": import_type,
                "engagement_id": self.context.engagement_id
            })
            agents.append(agent)

        return agents
```

---

#### Type-Specific Processors

##### CMDBExportProcessor (`/backend/app/services/collection/processors/cmdb_export.py`)

```python
class CMDBExportProcessor(DataImportProcessor):
    """
    Handles standard CMDB exports (existing functionality).

    Validation Agents (4):
    - FormatValidator: CSV/XLSX structure validation
    - DuplicateDetector: Duplicate asset detection
    - DataQualityAgent: Data quality scoring
    - SchemaValidator: Required field validation

    Enrichment Targets:
    - Asset.asset_name, Asset.asset_type (base attributes)
    - Asset.location, Asset.business_unit
    - Asset.environment (dev/test/prod)
    """

    def get_enrichment_targets(self) -> List[str]:
        return [
            "asset_name",
            "asset_type",
            "location",
            "business_unit",
            "environment",
            "cost_center"
        ]

    async def enrich_asset(
        self,
        asset: Asset,
        row_data: Dict[str, Any],
        mappings: Dict[str, str]
    ) -> AssetEnrichment:
        """
        Enrich asset with CMDB base attributes.

        Strategy:
        - Update base columns only (no JSONB enrichment)
        - Validate required fields present
        - Apply data quality normalization
        """
        before_snapshot = asset.to_dict()

        # Apply mappings
        for source_field, target_field in mappings.items():
            if target_field in self.get_enrichment_targets():
                setattr(asset, target_field, row_data.get(source_field))

        # Normalize data quality
        if hasattr(asset, 'asset_type'):
            asset.asset_type = self._normalize_asset_type(asset.asset_type)

        after_snapshot = asset.to_dict()

        # Create audit trail
        return AssetEnrichment(
            asset_id=asset.id,
            enrichment_source="cmdb_export",
            enriched_attributes={
                "before": before_snapshot,
                "after": after_snapshot,
                "changed_fields": [
                    field for field in self.get_enrichment_targets()
                    if before_snapshot.get(field) != after_snapshot.get(field)
                ]
            },
            enrichment_timestamp=datetime.utcnow()
        )
```

##### ApplicationDiscoveryProcessor (`/backend/app/services/collection/processors/app_discovery.py`)

```python
class ApplicationDiscoveryProcessor(DataImportProcessor):
    """
    Handles application discovery data (dependencies, integrations).

    Validation Agents (5):
    - DependencyAnalyzer: Analyzes application dependencies
    - AppToServerMapper: Maps applications to servers
    - IntegrationDetector: Detects API/service integrations
    - APIDiscoveryAgent: Discovers API endpoints
    - DataFlowAnalyzer: Analyzes data flow patterns

    Enrichment Targets:
    - Asset.dependencies JSONB (app-level dependencies)
    - Asset.integration_points JSONB (external integrations)
    - Asset.api_endpoints JSONB (discovered APIs)
    - Asset.data_flows JSONB (data flow diagrams)
    """

    def get_enrichment_targets(self) -> List[str]:
        return [
            "dependencies",
            "integration_points",
            "api_endpoints",
            "data_flows",
            "service_dependencies"
        ]

    async def enrich_asset(
        self,
        asset: Asset,
        row_data: Dict[str, Any],
        mappings: Dict[str, str]
    ) -> AssetEnrichment:
        """
        Enrich asset with application discovery data.

        Strategy:
        - Update JSONB fields (dependencies, integration_points)
        - Merge with existing data (additive enrichment)
        - Run agent analysis on complex relationships
        """
        before_snapshot = {
            "dependencies": asset.dependencies or {},
            "integration_points": asset.integration_points or {}
        }

        # Parse dependency data
        if "dependencies" in mappings:
            dependency_analyzer = await self.agent_pool.get_agent("dependency_analyzer")
            dependencies = await dependency_analyzer.analyze_dependencies(
                raw_data=row_data.get(mappings["dependencies"])
            )
            asset.dependencies = self._merge_jsonb(asset.dependencies, dependencies)

        # Parse integration points
        if "integration_points" in mappings:
            integration_detector = await self.agent_pool.get_agent("integration_detector")
            integrations = await integration_detector.detect_integrations(
                raw_data=row_data.get(mappings["integration_points"])
            )
            asset.integration_points = self._merge_jsonb(asset.integration_points, integrations)

        # Discover API endpoints if available
        if "api_endpoints" in mappings:
            api_agent = await self.agent_pool.get_agent("api_discovery_agent")
            endpoints = await api_agent.discover_endpoints(
                raw_data=row_data.get(mappings["api_endpoints"])
            )
            asset.api_endpoints = endpoints

        after_snapshot = {
            "dependencies": asset.dependencies,
            "integration_points": asset.integration_points
        }

        return AssetEnrichment(
            asset_id=asset.id,
            enrichment_source="application_discovery",
            enriched_attributes={
                "before": before_snapshot,
                "after": after_snapshot,
                "analysis_results": {
                    "dependency_count": len(asset.dependencies or {}),
                    "integration_count": len(asset.integration_points or {})
                }
            },
            enrichment_timestamp=datetime.utcnow()
        )

    def _merge_jsonb(self, existing: Dict, new: Dict) -> Dict:
        """
        Merge JSONB data (additive enrichment).

        Strategy:
        - Keep existing keys
        - Add new keys
        - Overwrite with new values if confidence > 0.8
        """
        merged = existing.copy() if existing else {}
        for key, value in new.items():
            if key not in merged or value.get("confidence", 0) > 0.8:
                merged[key] = value
        return merged
```

##### InfrastructureAssessmentProcessor (`/backend/app/services/collection/processors/infrastructure.py`)

```python
class InfrastructureAssessmentProcessor(DataImportProcessor):
    """
    Handles infrastructure assessment data (performance, topology).

    Validation Agents (5):
    - PerformanceAnalyzer: CPU/memory/disk metrics
    - TopologyMapper: Network topology mapping
    - CapacityAnalyzer: Capacity planning analysis
    - NetworkValidator: Network configuration validation
    - EOLDetector: End-of-life technology detection

    Enrichment Targets:
    - Asset.performance_metrics JSONB (CPU, memory, I/O)
    - Asset.network_topology JSONB (network layout)
    - Asset.capacity_analysis JSONB (capacity planning)
    - Asset.eol_technology BOOLEAN (EOL flag)
    """

    def get_enrichment_targets(self) -> List[str]:
        return [
            "performance_metrics",
            "network_topology",
            "capacity_analysis",
            "eol_technology",
            "network_configuration"
        ]

    async def enrich_asset(
        self,
        asset: Asset,
        row_data: Dict[str, Any],
        mappings: Dict[str, str]
    ) -> AssetEnrichment:
        """
        Enrich asset with infrastructure data.

        Strategy:
        - Parse performance metrics (time-series data)
        - Generate network topology visualizations
        - Flag EOL technologies
        """
        before_snapshot = {
            "performance_metrics": asset.performance_metrics or {},
            "network_topology": asset.network_topology or {}
        }

        # Analyze performance metrics
        if "performance_metrics" in mappings:
            perf_analyzer = await self.agent_pool.get_agent("performance_analyzer")
            metrics = await perf_analyzer.analyze_metrics(
                raw_data=row_data.get(mappings["performance_metrics"])
            )
            asset.performance_metrics = metrics

        # Map network topology
        if "network_topology" in mappings:
            topology_mapper = await self.agent_pool.get_agent("topology_mapper")
            topology = await topology_mapper.map_topology(
                raw_data=row_data.get(mappings["network_topology"])
            )
            asset.network_topology = topology

        # Detect EOL technologies
        eol_detector = await self.agent_pool.get_agent("eol_detector")
        is_eol = await eol_detector.check_eol(
            os_name=asset.operating_system,
            os_version=asset.os_version
        )
        asset.eol_technology = is_eol

        after_snapshot = {
            "performance_metrics": asset.performance_metrics,
            "network_topology": asset.network_topology
        }

        return AssetEnrichment(
            asset_id=asset.id,
            enrichment_source="infrastructure_assessment",
            enriched_attributes={
                "before": before_snapshot,
                "after": after_snapshot,
                "analysis_results": {
                    "eol_detected": is_eol,
                    "performance_score": metrics.get("score", 0)
                }
            },
            enrichment_timestamp=datetime.utcnow()
        )
```

##### SensitiveDataProcessor (`/backend/app/services/collection/processors/sensitive_data.py`)

```python
class SensitiveDataProcessor(DataImportProcessor):
    """
    Handles sensitive data assets (PII, compliance, encryption).

    Validation Agents (6):
    - DataClassifier: Classifies data sensitivity
    - PIIDetector: Detects personally identifiable information
    - ComplianceValidator: Validates compliance requirements
    - EncryptionChecker: Verifies encryption status
    - AccessControlAgent: Analyzes access controls
    - DataLineageTracker: Tracks data lineage

    Enrichment Targets:
    - Asset.data_classification TEXT (public/internal/confidential/restricted)
    - Asset.compliance_scopes JSONB (GDPR, HIPAA, PCI-DSS)
    - Asset.encryption_status JSONB (at-rest, in-transit)
    - Asset.access_controls JSONB (RBAC, ACL)
    - Asset.data_lineage JSONB (data flow)
    """

    def get_enrichment_targets(self) -> List[str]:
        return [
            "data_classification",
            "compliance_scopes",
            "encryption_status",
            "access_controls",
            "data_lineage"
        ]

    async def enrich_asset(
        self,
        asset: Asset,
        row_data: Dict[str, Any],
        mappings: Dict[str, str]
    ) -> AssetEnrichment:
        """
        Enrich asset with sensitive data attributes.

        Strategy:
        - Classify data sensitivity (agent-based)
        - Validate compliance requirements
        - Verify encryption and access controls
        - Maximum security validation (6 agents)
        """
        before_snapshot = {
            "data_classification": asset.data_classification,
            "compliance_scopes": asset.compliance_scopes or {}
        }

        # Classify data sensitivity
        data_classifier = await self.agent_pool.get_agent("data_classifier")
        classification = await data_classifier.classify(
            asset_data=row_data,
            existing_classification=asset.data_classification
        )
        asset.data_classification = classification

        # Detect PII
        pii_detector = await self.agent_pool.get_agent("pii_detector")
        pii_findings = await pii_detector.detect_pii(
            raw_data=row_data
        )

        # Validate compliance
        compliance_validator = await self.agent_pool.get_agent("compliance_validator")
        compliance_scopes = await compliance_validator.validate_compliance(
            data_classification=classification,
            pii_findings=pii_findings,
            industry=self.context.client_account.industry
        )
        asset.compliance_scopes = compliance_scopes

        # Check encryption
        encryption_checker = await self.agent_pool.get_agent("encryption_checker")
        encryption_status = await encryption_checker.check_encryption(
            raw_data=row_data.get(mappings.get("encryption_status", {}))
        )
        asset.encryption_status = encryption_status

        # Analyze access controls
        access_agent = await self.agent_pool.get_agent("access_control_agent")
        access_controls = await access_agent.analyze_access(
            raw_data=row_data.get(mappings.get("access_controls", {}))
        )
        asset.access_controls = access_controls

        after_snapshot = {
            "data_classification": asset.data_classification,
            "compliance_scopes": asset.compliance_scopes
        }

        return AssetEnrichment(
            asset_id=asset.id,
            enrichment_source="sensitive_data",
            enriched_attributes={
                "before": before_snapshot,
                "after": after_snapshot,
                "security_analysis": {
                    "pii_detected": len(pii_findings) > 0,
                    "compliance_requirements": list(compliance_scopes.keys()),
                    "encryption_verified": encryption_status.get("verified", False)
                }
            },
            enrichment_timestamp=datetime.utcnow()
        )
```

---

### 3. Repository Layer

#### EnrichmentStrategyRegistry (`/backend/app/repositories/enrichment_strategy_registry.py`)

```python
class EnrichmentStrategyRegistry:
    """
    Registry of enrichment strategies per import type.

    Responsibilities:
    - Map import types to target asset attributes
    - Define enrichment priorities
    - Handle conflict resolution (multiple sources enriching same field)
    """

    STRATEGIES = {
        "cmdb_export": {
            "priority": 1,  # Base data - highest priority
            "targets": [
                "asset_name",
                "asset_type",
                "location",
                "business_unit",
                "environment"
            ],
            "conflict_resolution": "overwrite"  # Always overwrite base attributes
        },
        "application_discovery": {
            "priority": 2,  # Application-level enrichment
            "targets": [
                "dependencies",
                "integration_points",
                "api_endpoints",
                "data_flows"
            ],
            "conflict_resolution": "merge"  # Merge JSONB data
        },
        "infrastructure_assessment": {
            "priority": 3,  # Infrastructure-level enrichment
            "targets": [
                "performance_metrics",
                "network_topology",
                "capacity_analysis",
                "eol_technology"
            ],
            "conflict_resolution": "latest"  # Use latest assessment
        },
        "sensitive_data": {
            "priority": 4,  # Security-level enrichment (highest scrutiny)
            "targets": [
                "data_classification",
                "compliance_scopes",
                "encryption_status",
                "access_controls"
            ],
            "conflict_resolution": "most_restrictive"  # Use most restrictive classification
        }
    }

    @classmethod
    def get_strategy(cls, import_type: str) -> Dict[str, Any]:
        """Get enrichment strategy for import type."""
        return cls.STRATEGIES.get(import_type, {})

    @classmethod
    def resolve_conflict(
        cls,
        target_field: str,
        existing_value: Any,
        new_value: Any,
        import_type: str
    ) -> Any:
        """
        Resolve conflicts when multiple imports target same field.

        Strategies:
        - overwrite: New value always wins (CMDB base data)
        - merge: Merge JSONB data (App Discovery, Infra)
        - latest: Use latest value (time-series data)
        - most_restrictive: Use most restrictive value (security)
        """
        strategy = cls.get_strategy(import_type)
        resolution = strategy.get("conflict_resolution", "latest")

        if resolution == "overwrite":
            return new_value
        elif resolution == "merge":
            return cls._merge_jsonb(existing_value, new_value)
        elif resolution == "latest":
            return new_value
        elif resolution == "most_restrictive":
            return cls._most_restrictive(existing_value, new_value)

        return new_value

    @staticmethod
    def _merge_jsonb(existing: Dict, new: Dict) -> Dict:
        """Merge JSONB data (additive enrichment)."""
        merged = existing.copy() if existing else {}
        merged.update(new)
        return merged

    @staticmethod
    def _most_restrictive(existing: str, new: str) -> str:
        """Return most restrictive data classification."""
        hierarchy = ["public", "internal", "confidential", "restricted"]
        existing_level = hierarchy.index(existing) if existing in hierarchy else 0
        new_level = hierarchy.index(new) if new in hierarchy else 0
        return hierarchy[max(existing_level, new_level)]
```

---

### 4. Database Schema Changes

#### Migration: `133_add_multi_type_import_support.py`

```python
"""
Add support for multi-type data imports.

Revision ID: 133
Revises: 132
Create Date: 2025-01-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    """
    Add columns for multi-type enrichment.

    Per CLAUDE.md:
    - All tables in 'migration' schema
    - Use CHECK constraints (not ENUMs)
    - Idempotent migrations
    """

    # Add new columns to assets table
    op.execute("""
        ALTER TABLE migration.assets
        ADD COLUMN IF NOT EXISTS dependencies JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS integration_points JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS api_endpoints JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS data_flows JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS performance_metrics JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS network_topology JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS capacity_analysis JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS eol_technology BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS data_classification VARCHAR(50),
        ADD COLUMN IF NOT EXISTS compliance_scopes JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS encryption_status JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS access_controls JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS data_lineage JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS enrichment_metadata JSONB DEFAULT '{}';
    """)

    # Add CHECK constraint for data_classification
    op.execute("""
        ALTER TABLE migration.assets
        ADD CONSTRAINT chk_data_classification
        CHECK (data_classification IN ('public', 'internal', 'confidential', 'restricted'));
    """)

    # Create data_import_tasks table
    op.execute("""
        CREATE TABLE IF NOT EXISTS migration.data_import_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            import_type VARCHAR(50) NOT NULL,
            collection_flow_id UUID NOT NULL REFERENCES migration.collection_flows(id) ON DELETE CASCADE,
            master_flow_id UUID REFERENCES migration.crewai_flow_state_extensions(id),
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            validation_results JSONB DEFAULT '{}',
            enrichment_summary JSONB DEFAULT '{}',
            error_details JSONB,
            client_account_id UUID NOT NULL,
            engagement_id UUID NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,

            CONSTRAINT chk_import_type CHECK (import_type IN (
                'cmdb_export',
                'application_discovery',
                'infrastructure_assessment',
                'sensitive_data'
            )),
            CONSTRAINT chk_status CHECK (status IN (
                'pending', 'processing', 'completed', 'failed'
            ))
        );
    """)

    # Create asset_enrichments table (audit trail)
    op.execute("""
        CREATE TABLE IF NOT EXISTS migration.asset_enrichments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
            enrichment_source VARCHAR(50) NOT NULL,
            enriched_attributes JSONB NOT NULL,
            enrichment_timestamp TIMESTAMP DEFAULT NOW(),
            client_account_id UUID NOT NULL,
            engagement_id UUID NOT NULL,

            CONSTRAINT chk_enrichment_source CHECK (enrichment_source IN (
                'cmdb_export',
                'application_discovery',
                'infrastructure_assessment',
                'sensitive_data'
            ))
        );
    """)

    # Add indexes for performance
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_data_import_tasks_flow
        ON migration.data_import_tasks(collection_flow_id);

        CREATE INDEX IF NOT EXISTS idx_data_import_tasks_tenant
        ON migration.data_import_tasks(client_account_id, engagement_id);

        CREATE INDEX IF NOT EXISTS idx_asset_enrichments_asset
        ON migration.asset_enrichments(asset_id);

        CREATE INDEX IF NOT EXISTS idx_asset_enrichments_source
        ON migration.asset_enrichments(enrichment_source);

        -- GIN indexes for JSONB columns (performance for JSON queries)
        CREATE INDEX IF NOT EXISTS idx_assets_dependencies_gin
        ON migration.assets USING GIN(dependencies);

        CREATE INDEX IF NOT EXISTS idx_assets_compliance_gin
        ON migration.assets USING GIN(compliance_scopes);
    """)

def downgrade():
    """Rollback multi-type import support."""
    op.execute("""
        DROP TABLE IF EXISTS migration.asset_enrichments CASCADE;
        DROP TABLE IF EXISTS migration.data_import_tasks CASCADE;

        ALTER TABLE migration.assets
        DROP COLUMN IF EXISTS dependencies,
        DROP COLUMN IF EXISTS integration_points,
        DROP COLUMN IF EXISTS api_endpoints,
        DROP COLUMN IF EXISTS data_flows,
        DROP COLUMN IF EXISTS performance_metrics,
        DROP COLUMN IF EXISTS network_topology,
        DROP COLUMN IF EXISTS capacity_analysis,
        DROP COLUMN IF EXISTS eol_technology,
        DROP COLUMN IF EXISTS data_classification,
        DROP COLUMN IF EXISTS compliance_scopes,
        DROP COLUMN IF EXISTS encryption_status,
        DROP COLUMN IF EXISTS access_controls,
        DROP COLUMN IF EXISTS data_lineage,
        DROP COLUMN IF EXISTS enrichment_metadata;
    """)
```

---

### 5. Agent Orchestration Strategy

#### Agent Pool Configuration (`/backend/app/services/persistent_agents/data_import_agent_pool.py`)

```python
class DataImportAgentPoolConfig:
    """
    Agent pool configuration for data import validation.

    Per ADR-015 and ADR-024:
    - Agents are persistent per tenant
    - memory=False (TenantMemoryManager used instead)
    - Agents warm up with import type context
    """

    AGENT_CONFIGS = {
        # CMDB Export Agents (4)
        "format_validator": {
            "role": "Data Format Validation Specialist",
            "goal": "Validate CSV/XLSX structure and detect formatting issues",
            "backstory": "Expert in data format validation with 10+ years in CMDB imports",
            "tools": ["file_format_analyzer", "schema_validator"],
            "memory": False  # Per ADR-024
        },
        "duplicate_detector": {
            "role": "Duplicate Detection Specialist",
            "goal": "Identify duplicate assets and suggest merge strategies",
            "backstory": "Expert in fuzzy matching and entity resolution",
            "tools": ["fuzzy_matcher", "entity_resolver"],
            "memory": False
        },
        "data_quality_agent": {
            "role": "Data Quality Analyst",
            "goal": "Score data quality and suggest improvements",
            "backstory": "Specialist in data profiling and quality metrics",
            "tools": ["data_profiler", "quality_scorer"],
            "memory": False
        },
        "schema_validator": {
            "role": "Schema Validation Expert",
            "goal": "Validate required fields and data types",
            "backstory": "Expert in database schema validation",
            "tools": ["schema_checker", "type_validator"],
            "memory": False
        },

        # Application Discovery Agents (5)
        "dependency_analyzer": {
            "role": "Application Dependency Analyst",
            "goal": "Analyze and map application dependencies",
            "backstory": "Expert in application architecture and dependency mapping",
            "tools": ["dependency_parser", "graph_analyzer"],
            "memory": False
        },
        "app_to_server_mapper": {
            "role": "Application-Server Mapping Specialist",
            "goal": "Map applications to their hosting servers",
            "backstory": "Expert in infrastructure topology mapping",
            "tools": ["topology_mapper", "asset_linker"],
            "memory": False
        },
        "integration_detector": {
            "role": "Integration Detection Specialist",
            "goal": "Detect API and service integrations",
            "backstory": "Expert in service-oriented architecture",
            "tools": ["api_scanner", "integration_analyzer"],
            "memory": False
        },
        "api_discovery_agent": {
            "role": "API Discovery Expert",
            "goal": "Discover and catalog API endpoints",
            "backstory": "Expert in API architecture and documentation",
            "tools": ["api_crawler", "endpoint_cataloger"],
            "memory": False
        },
        "data_flow_analyzer": {
            "role": "Data Flow Analysis Specialist",
            "goal": "Analyze data flow patterns between systems",
            "backstory": "Expert in data lineage and flow visualization",
            "tools": ["flow_analyzer", "lineage_tracker"],
            "memory": False
        },

        # Infrastructure Assessment Agents (5)
        "performance_analyzer": {
            "role": "Infrastructure Performance Analyst",
            "goal": "Analyze CPU, memory, and I/O metrics",
            "backstory": "Expert in infrastructure performance tuning",
            "tools": ["metrics_analyzer", "performance_profiler"],
            "memory": False
        },
        "topology_mapper": {
            "role": "Network Topology Specialist",
            "goal": "Map network topology and connections",
            "backstory": "Expert in network architecture visualization",
            "tools": ["topology_scanner", "network_mapper"],
            "memory": False
        },
        "capacity_analyzer": {
            "role": "Capacity Planning Expert",
            "goal": "Analyze capacity and forecast needs",
            "backstory": "Expert in capacity planning and forecasting",
            "tools": ["capacity_calculator", "forecast_analyzer"],
            "memory": False
        },
        "network_validator": {
            "role": "Network Configuration Validator",
            "goal": "Validate network configuration and security",
            "backstory": "Expert in network security and best practices",
            "tools": ["config_validator", "security_checker"],
            "memory": False
        },
        "eol_detector": {
            "role": "End-of-Life Technology Detector",
            "goal": "Detect EOL operating systems and software",
            "backstory": "Expert in technology lifecycle management",
            "tools": ["eol_database", "version_checker"],
            "memory": False
        },

        # Sensitive Data Agents (6)
        "data_classifier": {
            "role": "Data Classification Specialist",
            "goal": "Classify data sensitivity levels",
            "backstory": "Expert in data classification and governance",
            "tools": ["classifier", "sensitivity_analyzer"],
            "memory": False
        },
        "pii_detector": {
            "role": "PII Detection Expert",
            "goal": "Detect personally identifiable information",
            "backstory": "Expert in PII detection and privacy compliance",
            "tools": ["pii_scanner", "pattern_matcher"],
            "memory": False
        },
        "compliance_validator": {
            "role": "Compliance Validation Specialist",
            "goal": "Validate GDPR, HIPAA, PCI-DSS compliance",
            "backstory": "Expert in regulatory compliance",
            "tools": ["compliance_checker", "regulation_validator"],
            "memory": False
        },
        "encryption_checker": {
            "role": "Encryption Verification Expert",
            "goal": "Verify encryption at-rest and in-transit",
            "backstory": "Expert in cryptography and data security",
            "tools": ["encryption_verifier", "crypto_analyzer"],
            "memory": False
        },
        "access_control_agent": {
            "role": "Access Control Analyst",
            "goal": "Analyze RBAC and ACL configurations",
            "backstory": "Expert in identity and access management",
            "tools": ["rbac_analyzer", "acl_validator"],
            "memory": False
        },
        "data_lineage_tracker": {
            "role": "Data Lineage Specialist",
            "goal": "Track data lineage and flow",
            "backstory": "Expert in data governance and lineage tracking",
            "tools": ["lineage_tracker", "flow_visualizer"],
            "memory": False
        }
    }

    @classmethod
    async def initialize_pool(
        cls,
        import_type: str,
        client_account_id: UUID,
        engagement_id: UUID
    ) -> List[Agent]:
        """
        Initialize agent pool for import type.

        Per ADR-015: Uses TenantScopedAgentPool for persistence.
        """
        agent_pool = TenantScopedAgentPool(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )

        agent_type_mapping = {
            "cmdb_export": [
                "format_validator",
                "duplicate_detector",
                "data_quality_agent",
                "schema_validator"
            ],
            "application_discovery": [
                "dependency_analyzer",
                "app_to_server_mapper",
                "integration_detector",
                "api_discovery_agent",
                "data_flow_analyzer"
            ],
            "infrastructure_assessment": [
                "performance_analyzer",
                "topology_mapper",
                "capacity_analyzer",
                "network_validator",
                "eol_detector"
            ],
            "sensitive_data": [
                "data_classifier",
                "pii_detector",
                "compliance_validator",
                "encryption_checker",
                "access_control_agent",
                "data_lineage_tracker"
            ]
        }

        agents = []
        for agent_type in agent_type_mapping[import_type]:
            config = cls.AGENT_CONFIGS[agent_type]
            agent = await agent_pool.get_or_create_agent(
                agent_type=agent_type,
                role=config["role"],
                goal=config["goal"],
                backstory=config["backstory"],
                tools=config["tools"],
                memory=False  # Per ADR-024
            )
            agents.append(agent)

        return agents
```

---

### 6. MCP Integration Points

#### MCP Server: data-import-validator

**Location:** `/mcp-servers/data-import-validator/`

**Purpose:** Expose data import validation as MCP tools for external systems

**Tools:**

```typescript
// Tool 1: Validate CMDB File
{
  name: "validate_cmdb_file",
  description: "Validate CMDB export file format and structure",
  inputSchema: {
    type: "object",
    properties: {
      file_path: { type: "string", description: "Absolute path to file" },
      expected_format: { type: "string", enum: ["csv", "xlsx", "json", "xml"] }
    },
    required: ["file_path"]
  }
}

// Tool 2: Detect Data Type
{
  name: "detect_data_type",
  description: "Auto-detect import data type from file contents",
  inputSchema: {
    type: "object",
    properties: {
      file_path: { type: "string", description: "Absolute path to file" },
      sample_rows: { type: "number", default: 10 }
    },
    required: ["file_path"]
  }
}

// Tool 3: Suggest Field Mappings
{
  name: "suggest_mappings",
  description: "Generate intelligent field mapping suggestions",
  inputSchema: {
    type: "object",
    properties: {
      columns: { type: "array", items: { type: "string" } },
      import_type: { type: "string" },
      sample_data: { type: "array" }
    },
    required: ["columns", "import_type"]
  }
}
```

**Implementation:**

```python
# /mcp-servers/data-import-validator/server.py

from mcp.server import Server
from app.services.collection.data_import_orchestrator import DataImportOrchestrationService

server = Server("data-import-validator")

@server.tool("validate_cmdb_file")
async def validate_cmdb_file(file_path: str, expected_format: str = None):
    """Validate CMDB file format and structure."""
    orchestrator = DataImportOrchestrationService(db, context)

    with open(file_path, 'rb') as f:
        file_data = f.read()

    validation_results = await orchestrator.validate_file_format(
        file_data=file_data,
        expected_format=expected_format
    )

    return {
        "valid": validation_results.is_valid,
        "format": validation_results.detected_format,
        "warnings": validation_results.warnings,
        "errors": validation_results.errors
    }

@server.tool("detect_data_type")
async def detect_data_type(file_path: str, sample_rows: int = 10):
    """Auto-detect import data type from file contents."""
    orchestrator = DataImportOrchestrationService(db, context)

    with open(file_path, 'rb') as f:
        file_data = f.read()

    detected_type = await orchestrator.detect_import_type(
        file_data=file_data,
        sample_rows=sample_rows
    )

    return {
        "detected_type": detected_type.import_type,
        "confidence": detected_type.confidence,
        "reasoning": detected_type.reasoning
    }

@server.tool("suggest_mappings")
async def suggest_mappings(
    columns: List[str],
    import_type: str,
    sample_data: List[Dict] = None
):
    """Generate intelligent field mapping suggestions."""
    orchestrator = DataImportOrchestrationService(db, context)

    suggestions = await orchestrator.generate_mapping_suggestions(
        columns=columns,
        import_type=import_type,
        sample_data=sample_data
    )

    return {
        "mappings": [
            {
                "source_column": m.source_column,
                "target_field": m.target_field,
                "confidence": m.confidence,
                "alternatives": m.alternatives
            }
            for m in suggestions
        ]
    }
```

#### MCP Server: enrichment-engine

**Location:** `/mcp-servers/enrichment-engine/`

**Purpose:** Expose asset enrichment capabilities as MCP resources and tools

**Resources:**

```typescript
// Resource 1: Asset Enrichment Schema
{
  uri: "enrichment://schema/asset",
  name: "Asset Enrichment Schema",
  mimeType: "application/json",
  description: "JSON schema for asset enrichment data"
}

// Resource 2: Enrichment Audit Trail
{
  uri: "enrichment://audit/{asset_id}",
  name: "Enrichment Audit Trail",
  mimeType: "application/json",
  description: "Audit trail of all enrichments for an asset"
}
```

**Tools:**

```typescript
// Tool 1: Apply Enrichment
{
  name: "apply_enrichment",
  description: "Apply enrichment data to an asset",
  inputSchema: {
    type: "object",
    properties: {
      asset_id: { type: "string", format: "uuid" },
      enrichment_source: { type: "string", enum: ["cmdb_export", "application_discovery", "infrastructure_assessment", "sensitive_data"] },
      enrichment_data: { type: "object" }
    },
    required: ["asset_id", "enrichment_source", "enrichment_data"]
  }
}

// Tool 2: Rollback Enrichment
{
  name: "rollback_enrichment",
  description: "Rollback a specific enrichment by ID",
  inputSchema: {
    type: "object",
    properties: {
      enrichment_id: { type: "string", format: "uuid" }
    },
    required: ["enrichment_id"]
  }
}
```

#### Context7 MCP Integration

**Purpose:** Augment agent context with latest documentation for validation frameworks

**Usage in Agents:**

```python
from mcp.client import Client as MCPClient

class DataImportOrchestrationService:
    async def initialize_agents_with_context7(self, import_type: str):
        """
        Augment agent context with Context7 documentation.

        Example: Application Discovery agents get latest service mesh docs
        """
        context7_client = MCPClient("context7")

        if import_type == "application_discovery":
            # Resolve library ID for service mesh documentation
            library_id = await context7_client.call_tool(
                "resolve-library-id",
                libraryName="kubernetes/service-mesh"
            )

            # Fetch documentation
            docs = await context7_client.call_tool(
                "get-library-docs",
                context7CompatibleLibraryID=library_id,
                topic="service discovery patterns",
                tokens=5000
            )

            # Augment agent context
            for agent in self.agents:
                await agent.add_context(
                    "service_mesh_best_practices",
                    docs
                )
```

---

## API Endpoint Design

### Unified Endpoint Structure

**Base Path:** `/api/v1/collection/data-import`

**Endpoints:**

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| POST | `/analyze` | Analyze file and suggest mappings | `file`, `import_type`, `collection_flow_id` | `DataImportAnalysisResponse` |
| POST | `/execute` | Execute import with confirmed mappings | `task_id`, `confirmed_mappings`, `enrichment_options` | `DataImportExecutionResponse` |
| GET | `/status/{task_id}` | Poll import task status | - | `DataImportStatusResponse` |
| GET | `/history` | List import history for flow | Query: `collection_flow_id` | `List[DataImportTask]` |
| DELETE | `/task/{task_id}` | Cancel pending import task | - | `CancellationResponse` |

**Request/Response Schemas:**

```python
# Request Schemas
class DataImportAnalyzeRequest(BaseModel):
    file: UploadFile
    import_type: Literal["cmdb_export", "application_discovery", "infrastructure_assessment", "sensitive_data"]
    collection_flow_id: UUID

class DataImportExecuteRequest(BaseModel):
    task_id: UUID
    confirmed_mappings: Dict[str, str]  # {source_column: target_field}
    enrichment_options: Dict[str, Any]  # Type-specific options
    overwrite_existing: bool = False

# Response Schemas
class DataImportAnalysisResponse(BaseModel):
    task_id: UUID
    file_format: str  # "csv", "xlsx", "json", "xml"
    detected_columns: List[str]
    suggested_mappings: List[FieldMappingSuggestion]
    validation_warnings: List[ValidationWarning]
    enrichment_targets: List[str]  # Which asset attributes will be enriched
    estimated_rows: int

class FieldMappingSuggestion(BaseModel):
    source_column: str
    target_field: str
    confidence: float  # 0.0 - 1.0
    alternatives: List[str]  # Alternative target fields

class ValidationWarning(BaseModel):
    severity: Literal["info", "warning", "error"]
    message: str
    row_numbers: List[int]  # Affected rows
    agent_name: str  # Which agent generated this warning

class DataImportExecutionResponse(BaseModel):
    task_id: UUID
    status: str  # "pending", "processing"
    message: str
    estimated_duration_seconds: int

class DataImportStatusResponse(BaseModel):
    task_id: UUID
    status: str  # "pending", "processing", "completed", "failed"
    progress_percent: float
    current_stage: str  # "validation", "transformation", "enrichment", "persistence"
    rows_processed: int
    total_rows: int
    validation_results: Optional[Dict[str, Any]]
    enrichment_summary: Optional[Dict[str, Any]]
    error_details: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

---

## State Management

### Flow Status Integration (ADR-012)

**Master Flow Status** (`crewai_flow_state_extensions`):
- High-level lifecycle: `running`, `paused`, `completed`, `failed`
- Tracks overall import operation

**Child Flow Status** (`collection_flows`):
- Operational state: Current phase (`data_import`, `gap_analysis`, etc.)
- Import task details stored in `data_import_tasks` table

**Import Task Status** (`data_import_tasks`):
- Granular import status: `pending`, `processing`, `completed`, `failed`
- Tracks validation results and enrichment summary

**Status Transition Flow:**

```
User uploads file
  ↓
POST /analyze → Create DataImportTask (status: pending)
  ↓
Agent validation → Update task (status: processing, stage: validation)
  ↓
POST /execute → Dispatch to background queue
  ↓
Background worker:
  - Update task (stage: transformation)
  - Update task (stage: enrichment)
  - Update task (stage: persistence)
  ↓
Task completion:
  - Update task (status: completed)
  - Update master flow (status: running)
  - Update child flow (current_phase: gap_analysis)  # Proceed to next phase
```

---

## Migration Path from Current Implementation

### Phase 1: Infrastructure Setup (Week 1)

**Deliverables:**
- [ ] Database migration `133_add_multi_type_import_support.py`
- [ ] `DataImportTask` and `AssetEnrichment` models
- [ ] `EnrichmentStrategyRegistry`
- [ ] Base `DataImportProcessor` interface
- [ ] Unit tests for database schema

**Success Criteria:**
- Migration runs successfully on dev/staging
- All new tables have proper indexes
- Multi-tenant scoping verified

### Phase 2: API Layer (Week 2)

**Deliverables:**
- [ ] `/api/v1/collection/data-import/analyze` endpoint
- [ ] `/api/v1/collection/data-import/execute` endpoint
- [ ] `/api/v1/collection/data-import/status/{task_id}` endpoint
- [ ] Request/response schema definitions
- [ ] OpenAPI documentation

**Success Criteria:**
- All endpoints return proper responses
- File upload validation works
- HTTP polling returns correct status
- Integration tests pass

### Phase 3: Service Layer (Week 3-4)

**Deliverables:**
- [ ] `DataImportOrchestrationService`
- [ ] Type-specific processors:
  - [ ] `CMDBExportProcessor` (existing functionality)
  - [ ] `ApplicationDiscoveryProcessor` (new)
  - [ ] `InfrastructureAssessmentProcessor` (new)
  - [ ] `SensitiveDataProcessor` (new)
- [ ] Background worker for import execution
- [ ] Redis queue integration

**Success Criteria:**
- CMDB import maintains existing functionality
- New processors validate and enrich correctly
- Background tasks execute successfully
- Error handling works properly

### Phase 4: Agent Integration (Week 5-6)

**Deliverables:**
- [ ] Agent pool configuration for all 20 agents
- [ ] Agent initialization per import type
- [ ] TenantMemoryManager integration for agent learning
- [ ] Agent validation pipeline
- [ ] Agent-based enrichment logic

**Success Criteria:**
- All agents initialize correctly
- Validation produces meaningful insights
- Enrichment logic correctly updates assets
- Agent learning patterns stored in TenantMemoryManager

### Phase 5: MCP Integration (Week 7)

**Deliverables:**
- [ ] `data-import-validator` MCP server
- [ ] `enrichment-engine` MCP server
- [ ] Context7 integration for agent context augmentation
- [ ] MCP server documentation

**Success Criteria:**
- MCP tools callable from external systems
- Context7 docs augment agent context
- MCP resources accessible

### Phase 6: Frontend Integration (Week 8)

**Deliverables:**
- [ ] Update `/discovery/cmdb-import` page
- [ ] Add import type selection UI
- [ ] Status polling implementation
- [ ] Enrichment summary visualization
- [ ] E2E Playwright tests

**Success Criteria:**
- UI correctly routes to backend endpoints
- Status updates display in real-time
- Users can view enrichment results
- All 4 upload tiles functional

### Phase 7: Testing & Validation (Week 9)

**Deliverables:**
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests (all import types)
- [ ] E2E tests (Playwright)
- [ ] Performance testing (1000+ row imports)
- [ ] Security testing (file validation, XSS, injection)

**Success Criteria:**
- All tests pass
- Performance meets SLAs (<60s for 1000 rows)
- Security vulnerabilities resolved

### Phase 8: Production Deployment (Week 10)

**Deliverables:**
- [ ] Staging deployment
- [ ] Production deployment
- [ ] Monitoring dashboards (Grafana)
- [ ] Runbook documentation
- [ ] User documentation

**Success Criteria:**
- Zero-downtime deployment
- Monitoring shows healthy metrics
- No production incidents
- Users successfully import all data types

---

## Implementation Roadmap

### Phase 1: Minimal Viable Architecture (Weeks 1-4)

**Goal:** Enable basic multi-type import with CMDB + one additional type (Application Discovery)

**Components:**
- Database schema with new JSONB columns
- Unified API endpoint (`/analyze`, `/execute`, `/status`)
- `CMDBExportProcessor` (existing) + `ApplicationDiscoveryProcessor` (new)
- 4 CMDB validation agents + 5 App Discovery agents
- Background worker for async processing

**Success Criteria:**
- CMDB import maintains existing functionality
- Application Discovery import enriches `dependencies` and `integration_points`
- Users can upload and track import status

### Phase 2: Full Multi-Type Support (Weeks 5-8)

**Goal:** Add remaining import types (Infrastructure Assessment, Sensitive Data)

**Components:**
- `InfrastructureAssessmentProcessor` with 5 validation agents
- `SensitiveDataProcessor` with 6 validation agents
- Enhanced enrichment logic for performance metrics, compliance
- Enrichment audit trail (`asset_enrichments` table)

**Success Criteria:**
- All 4 import types functional
- Enrichment correctly updates target attributes
- Audit trail tracks all enrichments

### Phase 3: MCP Integration & External Tools (Weeks 9-10)

**Goal:** Expose import capabilities as MCP tools for external systems

**Components:**
- `data-import-validator` MCP server
- `enrichment-engine` MCP server
- Context7 integration for agent documentation augmentation

**Success Criteria:**
- MCP tools callable from external systems
- Agents augmented with latest best practices

---

## Code Examples

### Example 1: Analyze Import File (API Call)

```typescript
// Frontend: Analyze uploaded file
async function analyzeImportFile(
  file: File,
  importType: string,
  collectionFlowId: string
) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('import_type', importType);
  formData.append('collection_flow_id', collectionFlowId);

  const response = await fetch('/api/v1/collection/data-import/analyze', {
    method: 'POST',
    headers: {
      'X-Client-Account-ID': clientAccountId,
      'X-Engagement-ID': engagementId
    },
    body: formData
  });

  const analysis: DataImportAnalysisResponse = await response.json();

  return {
    taskId: analysis.task_id,
    suggestedMappings: analysis.suggested_mappings,
    warnings: analysis.validation_warnings,
    enrichmentTargets: analysis.enrichment_targets
  };
}
```

### Example 2: Execute Import with Confirmed Mappings

```typescript
// Frontend: Execute import after user confirms mappings
async function executeImport(
  taskId: string,
  confirmedMappings: Record<string, string>,
  enrichmentOptions: Record<string, any>
) {
  const response = await fetch('/api/v1/collection/data-import/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Account-ID': clientAccountId,
      'X-Engagement-ID': engagementId
    },
    body: JSON.stringify({
      task_id: taskId,
      confirmed_mappings: confirmedMappings,
      enrichment_options: enrichmentOptions,
      overwrite_existing: false
    })
  });

  const execution: DataImportExecutionResponse = await response.json();

  // Start polling for status
  pollImportStatus(execution.task_id);

  return execution;
}
```

### Example 3: Poll Import Status (HTTP Polling)

```typescript
// Frontend: Poll import status (per ADR-010, no WebSockets)
function pollImportStatus(taskId: string) {
  const { data, error } = useQuery({
    queryKey: ['import-status', taskId],
    queryFn: () => fetchImportStatus(taskId),
    enabled: !!taskId,
    refetchInterval: (data) => {
      if (!data) return false;
      if (data.status === 'completed' || data.status === 'failed') return false;
      return data.status === 'processing' ? 5000 : 15000;  // 5s active, 15s waiting
    },
    staleTime: 0  // Always fresh for status
  });

  return { status: data, error };
}

async function fetchImportStatus(taskId: string): Promise<DataImportStatusResponse> {
  const response = await fetch(`/api/v1/collection/data-import/status/${taskId}`, {
    headers: {
      'X-Client-Account-ID': clientAccountId,
      'X-Engagement-ID': engagementId
    }
  });

  return response.json();
}
```

### Example 4: Background Worker Processing

```python
# Backend: Background worker for import execution
async def process_import_task(task_id: UUID):
    """
    Background worker that processes data import task.

    Per CLAUDE.md:
    - Uses async/await throughout
    - Atomic transactions for data integrity
    - Multi-tenant scoping on all queries
    - TenantMemoryManager for agent learning
    """
    async with AsyncSessionLocal() as db:
        # Fetch task
        task = await db.get(DataImportTask, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        try:
            # Update status
            task.status = "processing"
            task.started_at = datetime.utcnow()
            task.current_stage = "validation"
            await db.commit()

            # Initialize orchestrator
            context = RequestContext(
                client_account_id=task.client_account_id,
                engagement_id=task.engagement_id,
                user_id="system"
            )
            orchestrator = DataImportOrchestrationService(db, context)

            # Retrieve cached analysis from Redis
            cache_key = f"import_analysis:{task.engagement_id}:{task.collection_flow_id}"
            cached_data = await orchestrator.redis.get(cache_key)
            if not cached_data:
                raise ValueError("Cached analysis not found")

            analysis_data = json.loads(cached_data)
            parsed_data = pd.DataFrame(analysis_data["parsed_data"])

            # Get processor
            processor = orchestrator._get_processor(task.import_type)

            # Stage 1: Validation
            logger.info(f"Stage 1: Validation for task {task_id}")
            agents = await orchestrator._initialize_agents(task.import_type)
            validation_results = await processor.validate(
                data=parsed_data,
                agents=agents
            )
            task.validation_results = validation_results.to_dict()
            task.current_stage = "transformation"
            await db.commit()

            # Stage 2: Transformation
            logger.info(f"Stage 2: Transformation for task {task_id}")
            transformed_data = await processor.transform_data(
                data=parsed_data,
                mappings=task.confirmed_mappings
            )
            task.current_stage = "enrichment"
            await db.commit()

            # Stage 3: Enrichment (atomic transaction)
            logger.info(f"Stage 3: Enrichment for task {task_id}")
            enrichment_summary = {"assets_enriched": 0, "attributes_updated": []}

            async with db.begin():  # Atomic transaction
                for idx, row in transformed_data.iterrows():
                    # Find or create asset
                    asset = await processor.find_or_create_asset(
                        row=row,
                        db=db
                    )

                    # Enrich asset
                    enrichment = await processor.enrich_asset(
                        asset=asset,
                        row_data=row.to_dict(),
                        mappings=task.confirmed_mappings
                    )

                    # Save enrichment audit trail
                    db.add(enrichment)

                    enrichment_summary["assets_enriched"] += 1
                    enrichment_summary["attributes_updated"].extend(
                        enrichment.enriched_attributes.get("changed_fields", [])
                    )

                    # Update progress
                    task.rows_processed = idx + 1
                    task.progress_percent = (idx + 1) / len(transformed_data) * 100

                    # Store agent learnings (TenantMemoryManager)
                    if validation_results.has_learnings:
                        await orchestrator.memory_manager.store_learning(
                            client_account_id=task.client_account_id,
                            engagement_id=task.engagement_id,
                            scope=LearningScope.ENGAGEMENT,
                            pattern_type=f"{task.import_type}_validation",
                            pattern_data=validation_results.learnings
                        )

                await db.flush()  # Ensure all enrichments saved

            # Stage 4: Completion
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.enrichment_summary = enrichment_summary
            task.current_stage = "completed"
            await db.commit()

            logger.info(
                f"✅ Task {task_id} completed: "
                f"{enrichment_summary['assets_enriched']} assets enriched"
            )

        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}", exc_info=True)
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e)[:500],
                "stage": task.current_stage
            }
            await db.commit()
```

---

## Trade-offs and Decisions

### Decision 1: Unified Endpoint vs Separate Endpoints per Type

**Chosen:** Unified endpoint with `import_type` parameter

**Rationale:**
- ✅ **Avoids endpoint sprawl** (4 types → 1 endpoint, not 4)
- ✅ **Consistent API patterns** (easier for frontend integration)
- ✅ **Easier to add new types** (no new routes needed)
- ❌ **Slightly more complex routing logic** (handled by orchestrator)

**Alternative:** Separate endpoints (`/cmdb-import`, `/app-discovery-import`, etc.)
- ❌ Would create 12 endpoints (3 per type: analyze, execute, status)
- ❌ Harder to maintain consistency
- ❌ Duplicated code across endpoint implementations

### Decision 2: JSONB Enrichment vs Dedicated Tables

**Chosen:** JSONB columns for enrichment data

**Rationale:**
- ✅ **Flexible schema** (no migrations for new enrichment fields)
- ✅ **PostgreSQL GIN indexes** for fast JSONB queries
- ✅ **Easier to merge data** from multiple sources
- ✅ **Additive enrichment** (merge existing + new data)
- ❌ **Slightly slower queries** vs dedicated columns (mitigated by GIN indexes)

**Alternative:** Dedicated tables (`asset_dependencies`, `asset_performance_metrics`, etc.)
- ❌ Requires migrations for schema changes
- ❌ Complex joins for queries
- ✅ Faster queries (but marginal with GIN indexes)

### Decision 3: Agent-Based Validation vs Rule-Based Validation

**Chosen:** Agent-based validation (4-6 agents per type)

**Rationale:**
- ✅ **Intelligent validation** (context-aware insights)
- ✅ **Learns from patterns** (TenantMemoryManager)
- ✅ **Adapts to tenant data** (per-tenant agent pools)
- ✅ **Provides explanations** (agent reasoning)
- ❌ **Slower than rule-based** (agent inference time)
- ❌ **More complex to implement** (agent coordination)

**Alternative:** Simple rule-based validation (regex, required fields, etc.)
- ✅ Faster execution
- ❌ No intelligence or learning
- ❌ No contextual insights

### Decision 4: Synchronous vs Asynchronous Import Execution

**Chosen:** Asynchronous (background queue via Redis)

**Rationale:**
- ✅ **Non-blocking API** (returns immediately)
- ✅ **Handles large files** (1000+ rows)
- ✅ **Retry logic** (if worker fails)
- ✅ **Status polling** (HTTP polling per ADR-010)
- ❌ **More complex** (queue management, worker coordination)

**Alternative:** Synchronous execution (wait for completion)
- ❌ Blocks API thread
- ❌ Timeout issues for large files
- ✅ Simpler implementation

### Decision 5: Per-Import-Type Processors vs Generic Processor

**Chosen:** Type-specific processors (4 processors)

**Rationale:**
- ✅ **Clear separation of concerns** (each type has distinct logic)
- ✅ **Easier to maintain** (change one without affecting others)
- ✅ **Type-specific validation** (4-6 agents per type)
- ✅ **Type-specific enrichment** (different asset attributes)
- ❌ **More code** (4 processor classes)

**Alternative:** Generic processor with if/else branching
- ❌ Complex branching logic
- ❌ Harder to test
- ✅ Less code

---

## Quality Checks

### 1. Can this be simplified further without losing essential capabilities?

**Assessment:** ✅ Yes, but at cost of intelligence
- Could remove agent-based validation → lose intelligent insights
- Could use single processor → lose type-specific logic
- Could skip MCP integration → lose external tool capabilities

**Recommendation:** Current design is at optimal complexity/capability balance

### 2. Are MCP servers used effectively to extend rather than complicate?

**Assessment:** ✅ Yes
- `data-import-validator` MCP server exposes core functionality to external systems
- `enrichment-engine` MCP server enables programmatic enrichment
- Context7 integration augments agent context (doesn't complicate core logic)
- MCP servers are optional (core functionality works without them)

### 3. Will this architecture support the next 2-3 likely evolution scenarios?

**Assessment:** ✅ Yes

**Scenario 1:** Add 5th import type (e.g., "Cost Optimization Data")
- Add new processor class
- Define agent pool configuration (N agents)
- Add enrichment targets to `EnrichmentStrategyRegistry`
- No schema changes needed (JSONB columns flexible)

**Scenario 2:** External system wants to trigger imports programmatically
- MCP `data-import-validator` server already exposes tools
- External system calls `validate_cmdb_file`, `suggest_mappings`, `apply_enrichment`

**Scenario 3:** Bulk import from cloud provider APIs (AWS, Azure, GCP)
- Add new processor: `CloudProviderProcessor`
- Reuse existing enrichment pipeline
- Add cloud-specific validation agents

### 4. Is the implementation path clear and achievable?

**Assessment:** ✅ Yes
- 10-week phased roadmap
- Clear deliverables per week
- Success criteria defined
- Migration path from current implementation

### 5. Have we avoided common pitfalls?

**Assessment:** ✅ Yes

**Pitfall 1: Over-abstraction**
- Avoided: Type-specific processors are concrete implementations
- Avoided: JSONB enrichment avoids premature schema normalization

**Pitfall 2: Premature optimization**
- Avoided: Background queue for async processing (not premature - needed for large files)
- Avoided: GIN indexes for JSONB (standard PostgreSQL best practice)

**Pitfall 3: Vendor lock-in**
- Avoided: MCP servers are optional
- Avoided: Agent-based validation is pluggable (can switch agent providers)

---

## Summary

This architecture enables the Collection Flow to handle four distinct data import types through a unified, scalable pipeline. The design:

1. **Simplifies the frontend** - Single upload UI, 4 tiles route to same endpoint
2. **Scales with import types** - Adding new types requires minimal changes
3. **Leverages existing infrastructure** - MFO, TenantScopedAgentPool, TenantMemoryManager
4. **Provides intelligent validation** - 4-6 agents per type with context-aware insights
5. **Enriches strategically** - Different attributes per import type (JSONB flexibility)
6. **Integrates with MCP** - Exposes capabilities to external tools
7. **Maintains enterprise patterns** - 7-layer architecture, multi-tenant isolation, atomic transactions

**Next Steps:**
1. Review architecture with stakeholders
2. Begin Phase 1 implementation (database schema)
3. Iterate based on feedback

---

## Architectural Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Endpoint Strategy** | Unified endpoint with `import_type` parameter | Avoids endpoint sprawl, consistent API patterns |
| **Enrichment Storage** | JSONB columns on `assets` table | Flexible schema, GIN indexes for performance, additive enrichment |
| **Validation Strategy** | Agent-based (4-6 agents per type) | Intelligent, contextual validation with learning capabilities |
| **Execution Mode** | Asynchronous (Redis queue) | Non-blocking API, handles large files, retry logic |
| **Processor Design** | Type-specific processors (4 classes) | Clear separation of concerns, easier maintenance |
| **MCP Integration** | Optional external tools | Extends capabilities without complicating core logic |

---

## References

### Related ADRs
- **ADR-006**: Master Flow Orchestrator (MFO integration)
- **ADR-012**: Flow Status Management Separation (state handling)
- **ADR-015**: Persistent Multi-Tenant Agent Architecture (agent pools)
- **ADR-024**: TenantMemoryManager (agent learning)
- **ADR-035**: Per-Asset, Per-Section Questionnaire Generation (similar batching pattern)

### Existing Codebase
- `/backend/app/api/v1/endpoints/collection/bulk_import.py` - Current CMDB import endpoint
- `/backend/app/services/collection/unified_import_orchestrator.py` - Orchestrator pattern
- `/backend/app/services/persistent_agents/tenant_scoped_agent_pool.py` - Agent pool
- `/backend/app/services/crewai_flows/memory/tenant_memory_manager.py` - Agent memory

### Documentation
- `/docs/analysis/Notes/coding-agent-guide.md` - Implementation patterns
- `/docs/guidelines/API_REQUEST_PATTERNS.md` - API best practices
- `/CLAUDE.md` - Project coding standards

---

**Document Version:** 1.0
**Date:** 2025-01-16
**Author:** AI Architecture Specialist (Claude Code)
**Review Status:** Draft - Awaiting Stakeholder Review
