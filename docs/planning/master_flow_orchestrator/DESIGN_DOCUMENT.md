# Master Flow Orchestrator Design Document

## Executive Summary

The Master Flow Orchestrator is a unified service that replaces all individual flow managers in the AI Force Migration Platform. It provides a single, consistent interface for managing all flow types (Discovery, Assessment, Planning, Execution, Modernize, FinOps, Observability, Decommission) while eliminating redundancy and ensuring consistent behavior across the platform.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Principles](#design-principles)
3. [Component Design](#component-design)
4. [Data Models](#data-models)
5. [API Design](#api-design)
6. [Flow Type Registry](#flow-type-registry)
7. [State Management](#state-management)
8. [Error Handling](#error-handling)
9. [Security & Multi-tenancy](#security--multi-tenancy)
10. [Performance Considerations](#performance-considerations)
11. [Migration Strategy](#migration-strategy)

## Architecture Overview

### Current State (Problem)
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Discovery   │ │ Assessment  │ │ Planning    │
│ Flow Mgr    │ │ Flow Mgr    │ │ Flow Mgr    │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┴───────────────┘
                       │
              ┌────────▼────────┐
              │ Master Flow     │
              │ Extensions      │
              │ (Just tracking) │
              └─────────────────┘
```

### Target State (Solution)
```
┌─────────────────────────────────────────────────┐
│          Master Flow Orchestrator               │
│                                                 │
│  ┌───────────────────────────────────-────┐     │
│  │         Flow Type Registry             │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │     │
│  │  │Disc. │ │Assess│ │Plan  │ │Exec. │   │     │
│  │  └──────┘ └──────┘ └──────┘ └──────┘   │     │
│  └─────────────────────────────────────-──┘     │
│                                                 │
│  Single API | Single State | Single Truth       │
└─────────────────────────────────────────────────┘
```

## Design Principles

### 1. Single Source of Truth
- Master flow table (`crewai_flow_state_extensions`) is THE authority
- No duplicate state tracking in child tables
- All flow status, progress, and metadata in one place

### 2. Configuration Over Code
- Flow types defined through configuration
- Phases, validators, and handlers registered, not hard-coded
- Easy to add new flow types without code changes

### 3. Consistent Behavior
- All flows follow same lifecycle: create → execute → pause/resume → complete/delete
- Unified error handling and recovery
- Standard progress tracking and reporting

### 4. Extensibility
- Plugin architecture for custom handlers
- Validator registry for phase-specific validation
- Hook system for flow-specific logic

### 5. Multi-tenant by Design
- Every operation scoped by client/engagement
- Proper data isolation at all levels
- Audit trail for all operations

## Component Design

### Core Components

```python
# 1. Master Flow Orchestrator (Main Service)
class MasterFlowOrchestrator:
    """Central orchestration service for all flow types"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.master_repo = CrewAIFlowStateExtensionsRepository(db)
        self.flow_registry = FlowTypeRegistry()
        self.state_manager = FlowStateManager(db)
        self.validator_registry = ValidatorRegistry()
        self.handler_registry = HandlerRegistry()
        
    # Core flow operations
    async def create_flow(...) -> MasterFlow
    async def execute_phase(...) -> PhaseResult
    async def pause_flow(...) -> None
    async def resume_flow(...) -> PhaseResult
    async def delete_flow(...) -> None
    async def get_flow_status(...) -> FlowStatus
    
    # Bulk operations
    async def get_active_flows(...) -> List[MasterFlow]
    async def get_flow_analytics(...) -> FlowAnalytics

# 2. Flow Type Registry
class FlowTypeRegistry:
    """Registry for all flow type configurations"""
    
    def register(self, config: FlowTypeConfig) -> None
    def get_config(self, flow_type: str) -> FlowTypeConfig
    def list_flow_types(self) -> List[str]

# 3. Flow State Manager
class FlowStateManager:
    """Manages flow state persistence and recovery"""
    
    async def save_state(self, flow_id: str, state: Any) -> None
    async def load_state(self, flow_id: str) -> Any
    async def update_phase_state(self, flow_id: str, phase: str, data: Dict) -> None

# 4. Validator Registry
class ValidatorRegistry:
    """Registry for phase-specific validators"""
    
    def register_validator(self, flow_type: str, phase: str, validator: Callable) -> None
    def validate(self, flow_type: str, phase: str, data: Any) -> ValidationResult

# 5. Handler Registry  
class HandlerRegistry:
    """Registry for custom phase handlers"""
    
    def register_handler(self, flow_type: str, phase: str, handler: Callable) -> None
    async def execute_handler(self, flow_type: str, phase: str, context: HandlerContext) -> Any
```

### Configuration Objects

```python
@dataclass
class FlowTypeConfig:
    """Configuration for a flow type"""
    name: str                              # e.g., "discovery"
    display_name: str                      # e.g., "Discovery Flow"
    description: str                       # Human-readable description
    phases: List[PhaseConfig]              # Ordered list of phases
    crew_class: Type[Flow]                 # CrewAI Flow implementation
    output_schema: Type[BaseModel]         # Pydantic model for outputs
    capabilities: FlowCapabilities         # What this flow can do
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PhaseConfig:
    """Configuration for a flow phase"""
    name: str                              # e.g., "data_import"
    display_name: str                      # e.g., "Data Import"
    description: str                       # What this phase does
    required_inputs: List[str]             # Required input fields
    optional_inputs: List[str]             # Optional input fields
    validators: List[str]                  # Validator names to apply
    handlers: List[str]                    # Handler names to execute
    can_pause: bool = True                 # Whether phase can be paused
    can_skip: bool = False                 # Whether phase can be skipped
    retry_config: RetryConfig = None       # Retry configuration

@dataclass
class FlowCapabilities:
    """Capabilities of a flow type"""
    supports_pause_resume: bool = True
    supports_rollback: bool = False
    supports_branching: bool = False
    supports_iterations: bool = True
    max_iterations: int = 10
    supports_scheduling: bool = False
```

## Data Models

### Master Flow Model (Enhanced)

```python
class CrewAIFlowStateExtensions(Base):
    """Master flow record - single source of truth"""
    __tablename__ = "crewai_flow_state_extensions"
    
    # Identity
    flow_id = Column(UUID, primary_key=True)
    flow_type = Column(String(50), nullable=False)
    flow_version = Column(String(20), default="1.0.0")
    
    # Multi-tenant context
    client_account_id = Column(UUID, nullable=False)
    engagement_id = Column(UUID, nullable=False)
    user_id = Column(String(255), nullable=False)
    
    # Flow metadata
    flow_name = Column(String(255))
    flow_description = Column(Text)
    flow_tags = Column(JSONB, default=list)
    
    # Status and progress
    flow_status = Column(String(50), default="initialized")
    current_phase = Column(String(50))
    phases_completed = Column(JSONB, default=list)
    progress_percentage = Column(Float, default=0.0)
    
    # Execution data
    flow_configuration = Column(JSONB, nullable=False)
    flow_state = Column(JSONB, nullable=False)  # Full CrewAI state
    phase_results = Column(JSONB, default=dict)
    validation_results = Column(JSONB, default=dict)
    
    # Performance and monitoring
    performance_metrics = Column(JSONB, default=dict)
    phase_execution_times = Column(JSONB, default=dict)
    resource_usage = Column(JSONB, default=dict)
    error_log = Column(JSONB, default=list)
    
    # Agent collaboration
    agent_collaboration_log = Column(JSONB, default=list)
    agent_insights = Column(JSONB, default=list)
    learning_patterns = Column(JSONB, default=list)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    updated_by = Column(String(255))
    deletion_metadata = Column(JSONB)  # For soft deletes
    
    # Relationships and dependencies
    parent_flow_id = Column(UUID)  # For sub-flows
    dependent_flow_ids = Column(JSONB, default=list)
    iteration_number = Column(Integer, default=1)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_flow_type_status', 'flow_type', 'flow_status'),
        Index('idx_client_engagement', 'client_account_id', 'engagement_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_current_phase', 'current_phase'),
    )
```

### Flow Execution Models

```python
class FlowExecutionRequest(BaseModel):
    """Request to execute a flow phase"""
    phase_name: Optional[str] = None  # If None, execute next phase
    inputs: Dict[str, Any] = {}
    options: ExecutionOptions = ExecutionOptions()

class ExecutionOptions(BaseModel):
    """Options for phase execution"""
    timeout_seconds: int = 300
    retry_on_failure: bool = True
    max_retries: int = 3
    save_checkpoints: bool = True
    validate_inputs: bool = True
    validate_outputs: bool = True

class PhaseResult(BaseModel):
    """Result of phase execution"""
    flow_id: str
    phase_name: str
    status: Literal["success", "failed", "paused", "skipped"]
    outputs: Dict[str, Any]
    validation_results: Optional[ValidationResult]
    execution_time_ms: int
    agent_insights: List[Dict[str, Any]]
    next_phase: Optional[str]
    errors: List[ErrorDetail] = []
```

## API Design

### RESTful Endpoints

```yaml
# Flow Management
POST   /api/v1/flows                    # Create any flow type
GET    /api/v1/flows                    # List flows (with filters)
GET    /api/v1/flows/{flow_id}          # Get flow details
DELETE /api/v1/flows/{flow_id}          # Delete flow (soft)

# Flow Execution
POST   /api/v1/flows/{flow_id}/execute  # Execute next/specific phase
POST   /api/v1/flows/{flow_id}/pause    # Pause flow
POST   /api/v1/flows/{flow_id}/resume   # Resume flow
POST   /api/v1/flows/{flow_id}/rollback # Rollback to phase

# Flow Status and Analytics
GET    /api/v1/flows/{flow_id}/status   # Get current status
GET    /api/v1/flows/{flow_id}/history  # Get execution history
GET    /api/v1/flows/analytics          # Get analytics across flows

# Flow Type Management
GET    /api/v1/flow-types               # List available flow types
GET    /api/v1/flow-types/{type}        # Get flow type details
```

### Request/Response Examples

```python
# Create Flow Request
POST /api/v1/flows
{
    "flow_type": "discovery",
    "flow_name": "Production Environment Discovery",
    "initial_data": {
        "environment": "production",
        "import_file_id": "file_123"
    },
    "options": {
        "auto_execute": true,
        "notification_emails": ["team@company.com"]
    }
}

# Create Flow Response
{
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "flow_type": "discovery",
    "status": "initialized",
    "current_phase": "data_import",
    "next_action": {
        "type": "execute_phase",
        "phase": "data_import",
        "required_inputs": []
    },
    "created_at": "2024-01-15T10:00:00Z"
}

# Execute Phase Request
POST /api/v1/flows/{flow_id}/execute
{
    "phase_name": "field_mapping",  # Optional, defaults to next phase
    "inputs": {
        "mappings": {
            "source_field_1": "target_field_1"
        },
        "approval": true
    }
}

# Get Status Response
{
    "flow_id": "550e8400-e29b-41d4-a716-446655440000",
    "flow_type": "discovery",
    "flow_name": "Production Environment Discovery",
    "status": "processing",
    "current_phase": "data_cleansing",
    "progress": {
        "percentage": 45.5,
        "phases_completed": ["data_import", "field_mapping"],
        "phases_remaining": ["data_cleansing", "asset_inventory", "dependency_analysis", "tech_debt_assessment"],
        "estimated_completion": "2024-01-15T11:30:00Z"
    },
    "performance": {
        "total_execution_time_ms": 125000,
        "phase_times": {
            "data_import": 45000,
            "field_mapping": 80000
        }
    },
    "next_action": {
        "type": "wait",
        "message": "Processing data cleansing phase",
        "estimated_duration_seconds": 180
    }
}
```

## Flow Type Registry

### Built-in Flow Types

```python
# Discovery Flow Configuration
DISCOVERY_FLOW_CONFIG = FlowTypeConfig(
    name="discovery",
    display_name="Discovery Flow",
    description="Discover and catalog IT assets and their dependencies",
    phases=[
        PhaseConfig(
            name="data_import",
            display_name="Data Import",
            description="Import data from various sources",
            required_inputs=["import_file_id"],
            validators=["file_exists", "file_format_valid"],
            handlers=["store_raw_data"]
        ),
        PhaseConfig(
            name="field_mapping",
            display_name="Field Mapping",
            description="Map source fields to target schema",
            required_inputs=["mappings"],
            validators=["mappings_complete"],
            handlers=["apply_mappings"],
            can_pause=True
        ),
        # ... other phases
    ],
    crew_class=UnifiedDiscoveryFlow,
    output_schema=DiscoveryFlowOutput,
    capabilities=FlowCapabilities(
        supports_iterations=True,
        max_iterations=5
    )
)

# Assessment Flow Configuration  
ASSESSMENT_FLOW_CONFIG = FlowTypeConfig(
    name="assessment",
    display_name="Assessment Flow",
    description="Assess applications for cloud migration readiness",
    phases=[
        PhaseConfig(
            name="migration_readiness",
            display_name="Migration Readiness Assessment",
            description="Evaluate technical readiness for migration",
            required_inputs=["application_ids"],
            validators=["applications_exist"],
            handlers=["fetch_application_data"]
        ),
        # ... other phases
    ],
    crew_class=UnifiedAssessmentFlow,
    output_schema=AssessmentFlowOutput,
    capabilities=FlowCapabilities()
)

# Registry initialization
flow_registry = FlowTypeRegistry()
flow_registry.register(DISCOVERY_FLOW_CONFIG)
flow_registry.register(ASSESSMENT_FLOW_CONFIG)
flow_registry.register(PLANNING_FLOW_CONFIG)
# ... register other flow types
```

### Adding New Flow Types

```python
# Example: Adding a new Security Scan flow type
SECURITY_SCAN_CONFIG = FlowTypeConfig(
    name="security_scan",
    display_name="Security Scan Flow",
    description="Scan applications for security vulnerabilities",
    phases=[
        PhaseConfig(
            name="vulnerability_scan",
            display_name="Vulnerability Scanning",
            description="Scan for known vulnerabilities",
            required_inputs=["target_systems"],
            validators=["valid_targets"],
            handlers=["initiate_scan"]
        ),
        PhaseConfig(
            name="risk_assessment",
            display_name="Risk Assessment",
            description="Assess security risks",
            validators=["scan_complete"],
            handlers=["analyze_risks"]
        )
    ],
    crew_class=SecurityScanFlow,
    output_schema=SecurityScanOutput,
    capabilities=FlowCapabilities(
        supports_scheduling=True
    )
)

# Register the new flow type
flow_registry.register(SECURITY_SCAN_CONFIG)
```

## State Management

### State Persistence Strategy

```python
class FlowStateManager:
    """Manages flow state with PostgreSQL persistence"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption_key = settings.STATE_ENCRYPTION_KEY
        
    async def save_state(self, flow_id: str, state: Any) -> None:
        """Save CrewAI flow state to database"""
        # 1. Serialize state (handle complex objects)
        serialized = self._serialize_state(state)
        
        # 2. Encrypt sensitive data
        encrypted = self._encrypt_sensitive_fields(serialized)
        
        # 3. Compress large states
        if len(json.dumps(encrypted)) > 10000:  # 10KB threshold
            compressed = self._compress_state(encrypted)
        else:
            compressed = encrypted
            
        # 4. Update master flow record
        await self._update_flow_state(flow_id, compressed)
        
    async def load_state(self, flow_id: str) -> Any:
        """Load and restore CrewAI flow state"""
        # 1. Fetch from database
        compressed = await self._fetch_flow_state(flow_id)
        
        # 2. Decompress if needed
        encrypted = self._decompress_state(compressed)
        
        # 3. Decrypt sensitive fields
        serialized = self._decrypt_sensitive_fields(encrypted)
        
        # 4. Deserialize to objects
        state = self._deserialize_state(serialized)
        
        return state
        
    def _serialize_state(self, state: Any) -> Dict:
        """Convert CrewAI state to JSON-serializable format"""
        # Handle special types (datetime, UUID, custom objects)
        return json.loads(
            json.dumps(state, cls=FlowStateEncoder)
        )
        
    def _encrypt_sensitive_fields(self, state: Dict) -> Dict:
        """Encrypt fields marked as sensitive"""
        sensitive_paths = [
            "credentials",
            "api_keys",
            "connection_strings"
        ]
        # Implement field-level encryption
        return state
```

### State Recovery and Checkpointing

```python
class StateRecoveryManager:
    """Handles state recovery and checkpointing"""
    
    async def create_checkpoint(
        self, 
        flow_id: str, 
        phase: str, 
        state: Any
    ) -> str:
        """Create a checkpoint for rollback"""
        checkpoint_id = str(uuid.uuid4())
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "flow_id": flow_id,
            "phase": phase,
            "state": state,
            "created_at": datetime.utcnow()
        }
        # Store checkpoint
        await self._store_checkpoint(checkpoint)
        return checkpoint_id
        
    async def recover_from_checkpoint(
        self, 
        checkpoint_id: str
    ) -> Any:
        """Recover state from checkpoint"""
        checkpoint = await self._load_checkpoint(checkpoint_id)
        return checkpoint["state"]
        
    async def auto_recover(self, flow_id: str) -> RecoveryResult:
        """Automatically recover from last good state"""
        # 1. Find last successful checkpoint
        last_checkpoint = await self._find_last_checkpoint(flow_id)
        
        # 2. Validate checkpoint integrity
        if not self._validate_checkpoint(last_checkpoint):
            return RecoveryResult(success=False, reason="Invalid checkpoint")
            
        # 3. Restore state
        state = await self.recover_from_checkpoint(
            last_checkpoint["checkpoint_id"]
        )
        
        return RecoveryResult(
            success=True,
            recovered_phase=last_checkpoint["phase"],
            state=state
        )
```

## Error Handling

### Error Handling Strategy

```python
class FlowErrorHandler:
    """Centralized error handling for flows"""
    
    def __init__(self):
        self.error_strategies = {
            ValidationError: self._handle_validation_error,
            TimeoutError: self._handle_timeout_error,
            CrewAIError: self._handle_crewai_error,
            DatabaseError: self._handle_database_error
        }
        
    async def handle_error(
        self, 
        error: Exception, 
        context: ErrorContext
    ) -> ErrorResolution:
        """Handle errors with appropriate strategy"""
        error_type = type(error)
        
        # 1. Log error with context
        await self._log_error(error, context)
        
        # 2. Apply error strategy
        strategy = self.error_strategies.get(
            error_type, 
            self._handle_generic_error
        )
        resolution = await strategy(error, context)
        
        # 3. Update flow status if needed
        if resolution.update_flow_status:
            await self._update_flow_error_state(
                context.flow_id,
                error,
                resolution
            )
            
        # 4. Notify if critical
        if resolution.severity == "critical":
            await self._send_error_notification(error, context)
            
        return resolution
        
    async def _handle_validation_error(
        self, 
        error: ValidationError, 
        context: ErrorContext
    ) -> ErrorResolution:
        """Handle validation errors"""
        return ErrorResolution(
            action="pause_for_input",
            message=f"Validation failed: {error.message}",
            user_action_required=True,
            can_retry=True,
            update_flow_status=True,
            new_status="waiting_for_input"
        )
```

### Retry Logic

```python
class RetryManager:
    """Manages retry logic for failed operations"""
    
    def __init__(self):
        self.default_config = RetryConfig(
            max_attempts=3,
            initial_delay_seconds=1,
            backoff_multiplier=2,
            max_delay_seconds=60
        )
        
    async def execute_with_retry(
        self,
        operation: Callable,
        config: RetryConfig = None
    ) -> Any:
        """Execute operation with exponential backoff retry"""
        config = config or self.default_config
        attempts = 0
        delay = config.initial_delay_seconds
        
        while attempts < config.max_attempts:
            try:
                return await operation()
            except Exception as e:
                attempts += 1
                
                if attempts >= config.max_attempts:
                    raise RetryExhaustedError(
                        f"Operation failed after {attempts} attempts",
                        original_error=e
                    )
                    
                # Log retry attempt
                logger.warning(
                    f"Attempt {attempts} failed, retrying in {delay}s: {e}"
                )
                
                # Wait with backoff
                await asyncio.sleep(delay)
                delay = min(
                    delay * config.backoff_multiplier,
                    config.max_delay_seconds
                )
```

## Security & Multi-tenancy

### Multi-tenant Isolation

```python
class MultiTenantFlowManager:
    """Ensures proper multi-tenant isolation"""
    
    def __init__(self, context: RequestContext):
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
        
    def apply_tenant_filter(self, query: Query) -> Query:
        """Apply tenant filters to any query"""
        return query.filter(
            CrewAIFlowStateExtensions.client_account_id == self.client_account_id,
            CrewAIFlowStateExtensions.engagement_id == self.engagement_id
        )
        
    async def validate_flow_access(self, flow_id: str) -> bool:
        """Validate user has access to flow"""
        flow = await self.get_flow(flow_id)
        return (
            flow.client_account_id == self.client_account_id and
            flow.engagement_id == self.engagement_id
        )
        
    def sanitize_flow_data(self, flow_data: Dict) -> Dict:
        """Remove sensitive data based on user permissions"""
        if not self.user_has_permission("view_sensitive_data"):
            # Remove sensitive fields
            sensitive_fields = [
                "api_keys", 
                "credentials", 
                "connection_strings"
            ]
            for field in sensitive_fields:
                flow_data.pop(field, None)
        return flow_data
```

### Security Controls

```python
class FlowSecurityManager:
    """Manages security controls for flows"""
    
    async def authorize_action(
        self,
        user_id: str,
        action: str,
        resource: str
    ) -> bool:
        """Authorize user action on resource"""
        # Check RBAC permissions
        user_roles = await self.get_user_roles(user_id)
        required_permission = f"{resource}:{action}"
        
        for role in user_roles:
            if required_permission in role.permissions:
                return True
                
        return False
        
    def encrypt_sensitive_data(self, data: Dict) -> Dict:
        """Encrypt sensitive fields in flow data"""
        encrypted = data.copy()
        
        for field, value in data.items():
            if self.is_sensitive_field(field):
                encrypted[field] = self.encrypt_value(value)
                
        return encrypted
        
    def audit_flow_action(
        self,
        user_id: str,
        action: str,
        flow_id: str,
        details: Dict
    ) -> None:
        """Audit trail for all flow actions"""
        audit_entry = {
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "action": action,
            "flow_id": flow_id,
            "details": details,
            "ip_address": self.get_client_ip(),
            "user_agent": self.get_user_agent()
        }
        # Store audit entry
        self.store_audit_entry(audit_entry)
```

## Performance Considerations

### Optimization Strategies

```python
class FlowPerformanceOptimizer:
    """Optimizes flow execution performance"""
    
    def __init__(self):
        self.cache_manager = FlowCacheManager()
        self.metrics_collector = MetricsCollector()
        
    async def optimize_phase_execution(
        self,
        flow_id: str,
        phase: str
    ) -> OptimizationResult:
        """Apply optimizations for phase execution"""
        
        # 1. Check cache for previous results
        cached_result = await self.cache_manager.get_phase_result(
            flow_id, phase
        )
        if cached_result and self.is_cache_valid(cached_result):
            return OptimizationResult(
                used_cache=True,
                result=cached_result
            )
            
        # 2. Pre-load required data
        await self.preload_phase_data(flow_id, phase)
        
        # 3. Optimize CrewAI agent configuration
        agent_config = self.optimize_agent_config(phase)
        
        # 4. Set resource limits
        resource_limits = self.calculate_resource_limits(phase)
        
        return OptimizationResult(
            used_cache=False,
            agent_config=agent_config,
            resource_limits=resource_limits
        )
```

### Performance Monitoring

```python
class FlowPerformanceMonitor:
    """Monitors flow execution performance"""
    
    async def track_phase_performance(
        self,
        flow_id: str,
        phase: str,
        execution_time_ms: int,
        resource_usage: Dict
    ) -> None:
        """Track performance metrics"""
        metrics = {
            "flow_id": flow_id,
            "phase": phase,
            "execution_time_ms": execution_time_ms,
            "cpu_usage_percent": resource_usage.get("cpu"),
            "memory_usage_mb": resource_usage.get("memory"),
            "timestamp": datetime.utcnow()
        }
        
        # Store metrics
        await self.store_metrics(metrics)
        
        # Check for performance degradation
        if execution_time_ms > self.get_phase_threshold(phase):
            await self.alert_performance_issue(
                flow_id, phase, execution_time_ms
            )
            
    async def generate_performance_report(
        self,
        flow_type: str,
        time_range: TimeRange
    ) -> PerformanceReport:
        """Generate performance report for flow type"""
        metrics = await self.query_metrics(flow_type, time_range)
        
        return PerformanceReport(
            average_execution_time=self.calculate_average(metrics),
            p95_execution_time=self.calculate_percentile(metrics, 95),
            success_rate=self.calculate_success_rate(metrics),
            resource_usage_trends=self.analyze_resource_trends(metrics)
        )
```

## Migration Strategy

### Phase 1: Parallel Implementation (No Breaking Changes)

```python
# 1. Implement MasterFlowOrchestrator alongside existing
orchestrator = MasterFlowOrchestrator(db)

# 2. Create adapter layer for backward compatibility
class FlowManagerAdapter:
    """Adapts old flow manager calls to orchestrator"""
    
    def __init__(self, orchestrator: MasterFlowOrchestrator):
        self.orchestrator = orchestrator
        
    async def create_discovery_flow(self, **kwargs):
        """Adapter method for legacy code"""
        return await self.orchestrator.create_flow(
            flow_type="discovery",
            **kwargs
        )

# 3. Update dependency injection
def get_flow_manager(db: Session, flow_type: str):
    """Returns adapter during migration"""
    orchestrator = MasterFlowOrchestrator(db)
    return FlowManagerAdapter(orchestrator)
```

### Phase 2: Database Migration

```sql
-- Add new fields to master table
ALTER TABLE crewai_flow_state_extensions
ADD COLUMN flow_version VARCHAR(20) DEFAULT '1.0.0',
ADD COLUMN current_phase VARCHAR(50),
ADD COLUMN phases_completed JSONB DEFAULT '[]'::jsonb,
ADD COLUMN phase_results JSONB DEFAULT '{}'::jsonb,
ADD COLUMN validation_results JSONB DEFAULT '{}'::jsonb,
ADD COLUMN resource_usage JSONB DEFAULT '{}'::jsonb,
ADD COLUMN error_log JSONB DEFAULT '[]'::jsonb;

-- Create indexes for performance
CREATE INDEX idx_flow_type_status ON crewai_flow_state_extensions(flow_type, flow_status);
CREATE INDEX idx_current_phase ON crewai_flow_state_extensions(current_phase);

-- Migrate data from child tables to master
UPDATE crewai_flow_state_extensions cse
SET 
    current_phase = df.current_phase,
    phases_completed = ARRAY[
        CASE WHEN df.data_import_completed THEN 'data_import' END,
        CASE WHEN df.field_mapping_completed THEN 'field_mapping' END
        -- ... other phases
    ]
FROM discovery_flows df
WHERE cse.flow_id = df.flow_id;
```

### Phase 3: API Migration

```python
# Old endpoints (mark as deprecated)
@router.post("/api/v1/discovery/flows", deprecated=True)
async def create_discovery_flow_legacy():
    """Legacy endpoint - redirects to new API"""
    return RedirectResponse("/api/v1/flows?type=discovery")

# New unified endpoints
@router.post("/api/v1/flows")
async def create_flow(request: CreateFlowRequest):
    """New unified flow creation"""
    return await orchestrator.create_flow(**request.dict())
```

### Phase 4: Frontend Migration

```typescript
// Old hook (deprecated)
export function useDiscoveryFlow(flowId: string) {
    console.warn('useDiscoveryFlow is deprecated, use useFlow instead');
    return useFlow(flowId, 'discovery');
}

// New unified hook
export function useFlow(flowId: string, flowType?: string) {
    return useQuery({
        queryKey: ['flow', flowId],
        queryFn: () => apiClient.get(`/api/v1/flows/${flowId}`)
    });
}
```

### Phase 5: Cleanup

```python
# Remove old code after verification
# 1. Delete individual flow managers
# 2. Remove redundant repositories  
# 3. Drop unnecessary database columns
# 4. Remove deprecated API endpoints
# 5. Clean up frontend components
```

## Testing Strategy

### Unit Testing

```python
class TestMasterFlowOrchestrator:
    """Unit tests for orchestrator"""
    
    async def test_create_flow(self):
        """Test flow creation for all types"""
        for flow_type in ["discovery", "assessment", "planning"]:
            flow = await orchestrator.create_flow(
                flow_type=flow_type,
                context=mock_context,
                initial_data={}
            )
            assert flow.flow_type == flow_type
            assert flow.flow_status == "initialized"
            
    async def test_phase_execution(self):
        """Test phase execution with mocked CrewAI"""
        with mock.patch('CrewAI.execute') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            result = await orchestrator.execute_phase(
                flow_id="test-flow",
                phase_name="data_import"
            )
            assert result.status == "success"
```

### Integration Testing

```python
class TestFlowIntegration:
    """Integration tests with real database"""
    
    async def test_full_discovery_flow(self, db_session):
        """Test complete discovery flow lifecycle"""
        # Create flow
        flow = await orchestrator.create_flow(
            flow_type="discovery",
            context=test_context,
            initial_data={"file_id": "test.csv"}
        )
        
        # Execute phases
        phases = ["data_import", "field_mapping", "data_cleansing"]
        for phase in phases:
            result = await orchestrator.execute_phase(
                flow_id=flow.flow_id
            )
            assert result.status == "success"
            
        # Verify final state
        status = await orchestrator.get_flow_status(flow.flow_id)
        assert status["progress_percentage"] > 50
```

### Performance Testing

```python
class TestFlowPerformance:
    """Performance benchmarks"""
    
    async def test_concurrent_flow_execution(self):
        """Test concurrent flow handling"""
        flow_ids = []
        
        # Create 100 flows
        for i in range(100):
            flow = await orchestrator.create_flow(
                flow_type="discovery",
                context=test_context,
                initial_data={}
            )
            flow_ids.append(flow.flow_id)
            
        # Execute phases concurrently
        tasks = [
            orchestrator.execute_phase(flow_id)
            for flow_id in flow_ids
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Assert performance requirements
        assert end_time - start_time < 60  # Under 1 minute
        assert all(r.status == "success" for r in results)
```

## Monitoring and Observability

### Metrics Collection

```python
class FlowMetricsCollector:
    """Collects metrics for monitoring"""
    
    def __init__(self):
        self.prometheus_registry = CollectorRegistry()
        
        # Define metrics
        self.flow_counter = Counter(
            'flow_total',
            'Total flows created',
            ['flow_type', 'status'],
            registry=self.prometheus_registry
        )
        
        self.phase_duration = Histogram(
            'phase_duration_seconds',
            'Phase execution duration',
            ['flow_type', 'phase'],
            registry=self.prometheus_registry
        )
        
        self.active_flows = Gauge(
            'active_flows',
            'Currently active flows',
            ['flow_type'],
            registry=self.prometheus_registry
        )
        
    def record_flow_created(self, flow_type: str):
        """Record flow creation"""
        self.flow_counter.labels(
            flow_type=flow_type,
            status='created'
        ).inc()
        
    def record_phase_duration(
        self,
        flow_type: str,
        phase: str,
        duration_seconds: float
    ):
        """Record phase execution time"""
        self.phase_duration.labels(
            flow_type=flow_type,
            phase=phase
        ).observe(duration_seconds)
```

### Logging Strategy

```python
class FlowLogger:
    """Structured logging for flows"""
    
    def __init__(self):
        self.logger = structlog.get_logger()
        
    def log_flow_event(
        self,
        event_type: str,
        flow_id: str,
        **kwargs
    ):
        """Log structured flow event"""
        self.logger.bind(
            flow_id=flow_id,
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat()
        ).info(
            f"Flow event: {event_type}",
            **kwargs
        )
        
    def log_phase_execution(
        self,
        flow_id: str,
        phase: str,
        duration_ms: int,
        status: str
    ):
        """Log phase execution details"""
        self.logger.bind(
            flow_id=flow_id,
            phase=phase,
            duration_ms=duration_ms,
            status=status
        ).info(
            f"Phase {phase} completed with status {status}"
        )
```

## Conclusion

The Master Flow Orchestrator design provides a unified, extensible, and maintainable solution for managing all flow types in the AI Force Migration Platform. By consolidating redundant code and establishing clear patterns, it will significantly reduce complexity while improving consistency and reliability across the platform.

Key benefits:
- Single source of truth for all flows
- Consistent behavior across flow types  
- Easy to add new flow types
- Reduced code duplication
- Better monitoring and observability
- Improved error handling and recovery

The design prioritizes extensibility and maintainability while ensuring backward compatibility during migration.