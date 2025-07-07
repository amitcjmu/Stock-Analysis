# Discovery Flow Remediation Implementation Task Tracker

## Overview
This tracker is designed for parallel execution by multiple AI coding agents. Tasks are organized by phase with clear dependencies, allowing agents to work simultaneously on independent tasks.

## Execution Guidelines for AI Agents

1. **Task Selection**: Choose tasks marked as "Ready" with no blocking dependencies
2. **Parallel Work**: Multiple agents can work on different tasks simultaneously
3. **Dependency Check**: Always verify dependencies are completed before starting a task
4. **Status Updates**: Mark task as "In Progress" when starting, "Completed" when done
5. **Code Location**: Follow the file paths and patterns specified in each task
6. **Testing**: Each task includes test requirements that must be completed

## Task Status Legend
- 🟢 **Ready**: Task can be started immediately
- 🔵 **In Progress**: Task is being worked on
- ✅ **Completed**: Task is finished and tested
- 🔴 **Blocked**: Waiting on dependencies
- 🟡 **Review**: Needs review before marking complete

---

## Phase 1: Continuous Refinement Foundation (Weeks 1-2)

### Week 1: Database Schema Tasks

#### Task 1.1: Create Assets Table
- **Status**: 🟢 Ready
- **Priority**: Critical
- **Dependencies**: None
- **Estimated Hours**: 8
- **Location**: `backend/alembic/versions/`
- **Description**: Create persistent assets table separate from flow state

**Implementation Requirements**:
```sql
-- Create new migration file: xxx_create_assets_table.py
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,
    discovery_flow_id UUID REFERENCES discovery_flows(id),
    asset_type VARCHAR(50) NOT NULL,
    asset_subtype VARCHAR(50),
    asset_state VARCHAR(50) NOT NULL DEFAULT 'discovered',
    name VARCHAR(255) NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}',
    readiness_score FLOAT DEFAULT 0.0,
    confidence_score FLOAT DEFAULT 0.0,
    source_systems JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT assets_client_account_id_fkey FOREIGN KEY (client_account_id) 
        REFERENCES client_accounts(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_assets_client_engagement ON assets(client_account_id, engagement_id);
CREATE INDEX idx_assets_flow_id ON assets(discovery_flow_id);
CREATE INDEX idx_assets_type_state ON assets(asset_type, asset_state);
CREATE INDEX idx_assets_name ON assets(name);
```

**Test Requirements**:
- Multi-tenant isolation test
- Performance test with 10K+ assets
- Constraint validation tests

---

#### Task 1.2: Create Data Sources Table
- **Status**: 🟢 Ready
- **Priority**: Critical
- **Dependencies**: None (can run parallel to 1.1)
- **Estimated Hours**: 6
- **Location**: `backend/alembic/versions/`
- **Description**: Track data sources with reliability scoring

**Implementation Requirements**:
```sql
-- Create new migration file: xxx_create_data_sources_table.py
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_account_id INTEGER NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    reliability_score FLOAT DEFAULT 0.5,
    is_authoritative_for JSONB DEFAULT '[]',
    connection_config JSONB DEFAULT '{}',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_frequency_hours INTEGER,
    total_imports INTEGER DEFAULT 0,
    successful_imports INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT data_sources_client_account_id_fkey FOREIGN KEY (client_account_id) 
        REFERENCES client_accounts(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_data_sources_client ON data_sources(client_account_id);
CREATE INDEX idx_data_sources_type ON data_sources(source_type);
CREATE UNIQUE INDEX idx_data_sources_name_client ON data_sources(client_account_id, source_name);
```

**Test Requirements**:
- Unique constraint tests
- Reliability score calculation tests
- Source type validation

---

#### Task 1.3: Create Raw Data Records Table
- **Status**: 🟢 Ready
- **Priority**: High
- **Dependencies**: None (can run parallel)
- **Estimated Hours**: 6
- **Location**: `backend/alembic/versions/`
- **Description**: Store raw import data for audit and rollback

**Implementation Requirements**:
```sql
-- Create new migration file: xxx_create_raw_data_records_table.py
CREATE TABLE raw_data_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_account_id INTEGER NOT NULL,
    discovery_flow_id UUID NOT NULL,
    data_source_id UUID REFERENCES data_sources(id),
    import_id UUID NOT NULL,
    record_type VARCHAR(50) NOT NULL,
    raw_data JSONB NOT NULL,
    processed_data JSONB,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_errors JSONB DEFAULT '[]',
    hash_signature VARCHAR(64),
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT raw_data_client_account_id_fkey FOREIGN KEY (client_account_id) 
        REFERENCES client_accounts(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_raw_data_client_flow ON raw_data_records(client_account_id, discovery_flow_id);
CREATE INDEX idx_raw_data_import ON raw_data_records(import_id);
CREATE INDEX idx_raw_data_status ON raw_data_records(processing_status);
CREATE INDEX idx_raw_data_hash ON raw_data_records(hash_signature);

-- Partitioning by month for performance
-- Add partitioning setup based on imported_at
```

**Test Requirements**:
- Large data handling (1MB+ JSON)
- Hash collision tests
- Partitioning performance tests

---

#### Task 1.4: Create Asset Versions Table
- **Status**: 🔴 Blocked
- **Priority**: High
- **Dependencies**: Task 1.1 (assets table)
- **Estimated Hours**: 8
- **Location**: `backend/alembic/versions/`
- **Description**: Track asset version history

**Implementation Requirements**:
```sql
-- Create new migration file: xxx_create_asset_versions_table.py
CREATE TABLE asset_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    changed_fields JSONB DEFAULT '[]',
    previous_values JSONB DEFAULT '{}',
    new_values JSONB DEFAULT '{}',
    change_source_id UUID REFERENCES data_sources(id),
    change_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    UNIQUE(asset_id, version_number)
);

-- Indexes
CREATE INDEX idx_asset_versions_asset ON asset_versions(asset_id);
CREATE INDEX idx_asset_versions_created ON asset_versions(created_at);
```

---

#### Task 1.5: Create Asset Attributes Table
- **Status**: 🔴 Blocked
- **Priority**: Medium
- **Dependencies**: Tasks 1.1, 1.2
- **Estimated Hours**: 4
- **Location**: `backend/alembic/versions/`
- **Description**: Track source attribution per attribute

**Implementation Requirements**:
```sql
-- Create new migration file: xxx_create_asset_attributes_table.py
CREATE TABLE asset_attributes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    attribute_name VARCHAR(255) NOT NULL,
    attribute_value JSONB,
    source_id UUID REFERENCES data_sources(id),
    confidence_score FLOAT DEFAULT 0.5,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    update_count INTEGER DEFAULT 1,
    UNIQUE(asset_id, attribute_name)
);

-- Indexes
CREATE INDEX idx_asset_attributes_asset ON asset_attributes(asset_id);
CREATE INDEX idx_asset_attributes_source ON asset_attributes(source_id);
```

---

### Week 2: Flow Modification Tasks

#### Task 2.1: Update UnifiedDiscoveryFlow for Asset Detection
- **Status**: 🔴 Blocked
- **Priority**: Critical
- **Dependencies**: Tasks 1.1, 1.4
- **Estimated Hours**: 8
- **Location**: `backend/app/services/crewai_flows/unified_discovery_flow.py`
- **Description**: Modify flow to check and load existing assets

**Implementation Requirements**:
```python
# Add to UnifiedDiscoveryFlow class

@start()
async def initialize_discovery(self):
    """Enhanced initialization with existing asset detection"""
    # Check for existing assets
    asset_repository = AssetRepository(self.db, self.context.client_account_id)
    existing_assets = await asset_repository.find_by_engagement(
        self.context.engagement_id
    )
    
    if existing_assets:
        self.state.mode = "refinement"
        self.state.existing_assets = [asset.to_dict() for asset in existing_assets]
        self.state.merge_strategy = self.config.get("merge_strategy", "confidence_based")
        logger.info(f"Found {len(existing_assets)} existing assets - entering refinement mode")
    else:
        self.state.mode = "initial"
        logger.info("No existing assets found - entering initial discovery mode")
    
    # Store mode in flow metadata
    await self.flow_repository.update_metadata(self.flow_id, {
        "discovery_mode": self.state.mode,
        "existing_asset_count": len(existing_assets) if existing_assets else 0
    })
```

**Test Requirements**:
- Test both initial and refinement modes
- Verify existing asset loading
- Test mode persistence

---

#### Task 2.2: Implement Merge Strategies
- **Status**: 🔴 Blocked
- **Priority**: Critical
- **Dependencies**: Task 2.1
- **Estimated Hours**: 10
- **Location**: `backend/app/services/discovery/merge_strategies.py` (new file)
- **Description**: Create multiple merge strategy implementations

**Implementation Requirements**:
```python
# Create new file: backend/app/services/discovery/merge_strategies.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class MergeStrategy(ABC):
    """Base class for asset merge strategies"""
    
    @abstractmethod
    async def merge_assets(
        self, 
        existing_asset: Dict[str, Any], 
        new_data: Dict[str, Any],
        source_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge new data into existing asset"""
        pass

class ConfidenceBasedMergeStrategy(MergeStrategy):
    """Merge based on confidence scores"""
    
    async def merge_assets(self, existing_asset, new_data, source_info):
        merged = existing_asset.copy()
        
        for key, new_value in new_data.items():
            if key not in merged:
                merged[key] = new_value
                continue
                
            # Get confidence scores
            existing_confidence = self._get_attribute_confidence(existing_asset, key)
            new_confidence = source_info.get("reliability_score", 0.5)
            
            if new_confidence > existing_confidence:
                merged[key] = new_value
                
        return merged

class NewestWinsMergeStrategy(MergeStrategy):
    """Always use the newest data"""
    
    async def merge_assets(self, existing_asset, new_data, source_info):
        return {**existing_asset, **new_data}

class AuthoritativeMergeStrategy(MergeStrategy):
    """Use authoritative sources for specific attributes"""
    
    def __init__(self, authoritative_mappings: Dict[str, str]):
        self.authoritative_mappings = authoritative_mappings
    
    async def merge_assets(self, existing_asset, new_data, source_info):
        merged = existing_asset.copy()
        source_type = source_info.get("source_type")
        
        for key, value in new_data.items():
            # Check if this source is authoritative for this attribute
            if self.authoritative_mappings.get(key) == source_type:
                merged[key] = value
            elif key not in merged:
                merged[key] = value
                
        return merged

class MergeStrategyFactory:
    """Factory for creating merge strategies"""
    
    @staticmethod
    def create_strategy(strategy_type: str, **kwargs) -> MergeStrategy:
        strategies = {
            "confidence_based": ConfidenceBasedMergeStrategy,
            "newest_wins": NewestWinsMergeStrategy,
            "authoritative": AuthoritativeMergeStrategy
        }
        
        strategy_class = strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown merge strategy: {strategy_type}")
            
        return strategy_class(**kwargs)
```

**Test Requirements**:
- Unit tests for each strategy
- Integration tests with real assets
- Performance tests with large datasets

---

#### Task 2.3: Create Conflict Detection Logic
- **Status**: 🔴 Blocked
- **Priority**: High
- **Dependencies**: Task 2.2
- **Estimated Hours**: 8
- **Location**: `backend/app/services/discovery/conflict_detection.py` (new file)
- **Description**: Implement intelligent conflict detection

**Implementation Requirements**:
```python
# Create new file: backend/app/services/discovery/conflict_detection.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ConflictType(Enum):
    VALUE_MISMATCH = "value_mismatch"
    TYPE_MISMATCH = "type_mismatch"
    MISSING_IN_NEW = "missing_in_new"
    MISSING_IN_EXISTING = "missing_in_existing"
    SUSPICIOUS_CHANGE = "suspicious_change"

@dataclass
class DataConflict:
    asset_id: str
    attribute_name: str
    conflict_type: ConflictType
    existing_value: Any
    new_value: Any
    existing_source: Optional[str]
    new_source: Optional[str]
    severity: str  # low, medium, high, critical
    description: str
    resolution_hint: Optional[str] = None

class ConflictDetector:
    """Detects conflicts between existing and new asset data"""
    
    def __init__(self, anomaly_threshold: float = 0.3):
        self.anomaly_threshold = anomaly_threshold
        self.critical_attributes = [
            "ip_address", "hostname", "database_name", 
            "application_id", "criticality"
        ]
    
    async def detect_conflicts(
        self, 
        existing_asset: Dict[str, Any], 
        new_data: Dict[str, Any],
        source_info: Dict[str, Any]
    ) -> List[DataConflict]:
        """Detect all conflicts between existing and new data"""
        conflicts = []
        
        # Check for value mismatches
        for key in set(existing_asset.keys()) & set(new_data.keys()):
            if existing_asset[key] != new_data[key]:
                conflict = self._analyze_value_conflict(
                    existing_asset, new_data, key, source_info
                )
                if conflict:
                    conflicts.append(conflict)
        
        # Check for missing attributes
        conflicts.extend(self._check_missing_attributes(existing_asset, new_data))
        
        # Check for suspicious changes
        conflicts.extend(await self._detect_anomalies(existing_asset, new_data))
        
        return conflicts
    
    def _analyze_value_conflict(
        self, existing, new_data, attribute, source_info
    ) -> Optional[DataConflict]:
        """Analyze a single value conflict"""
        existing_value = existing.get(attribute)
        new_value = new_data.get(attribute)
        
        # Skip if values are equivalent
        if self._values_equivalent(existing_value, new_value):
            return None
            
        severity = "critical" if attribute in self.critical_attributes else "medium"
        
        return DataConflict(
            asset_id=existing.get("id"),
            attribute_name=attribute,
            conflict_type=ConflictType.VALUE_MISMATCH,
            existing_value=existing_value,
            new_value=new_value,
            existing_source=existing.get("_source"),
            new_source=source_info.get("source_name"),
            severity=severity,
            description=f"Value mismatch for {attribute}",
            resolution_hint=self._get_resolution_hint(attribute, existing_value, new_value)
        )
    
    async def _detect_anomalies(
        self, existing: Dict, new_data: Dict
    ) -> List[DataConflict]:
        """Detect suspicious or anomalous changes"""
        anomalies = []
        
        # Example: Detect suspicious IP address changes
        if "ip_address" in existing and "ip_address" in new_data:
            if self._is_suspicious_ip_change(existing["ip_address"], new_data["ip_address"]):
                anomalies.append(DataConflict(
                    asset_id=existing.get("id"),
                    attribute_name="ip_address",
                    conflict_type=ConflictType.SUSPICIOUS_CHANGE,
                    existing_value=existing["ip_address"],
                    new_value=new_data["ip_address"],
                    existing_source=existing.get("_source"),
                    new_source=new_data.get("_source"),
                    severity="high",
                    description="IP address changed to different subnet",
                    resolution_hint="Verify if server was migrated or if this is an error"
                ))
        
        return anomalies
```

**Test Requirements**:
- Test all conflict types
- Test anomaly detection
- Test with real-world data patterns

---

#### Task 2.4: Implement Source Lineage Tracking
- **Status**: 🔴 Blocked
- **Priority**: Medium
- **Dependencies**: Task 1.5
- **Estimated Hours**: 6
- **Location**: `backend/app/services/discovery/data_lineage.py` (new file)
- **Description**: Track complete data provenance

**Implementation Requirements**:
```python
# Create new file: backend/app/services/discovery/data_lineage.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class LineageRecord:
    """Record of data lineage for an attribute"""
    attribute_name: str
    value: Any
    source_id: str
    source_name: str
    source_type: str
    import_id: str
    timestamp: datetime
    confidence_score: float
    transformation_applied: Optional[str] = None
    validation_status: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class DataLineageTracker:
    """Tracks data lineage for assets and attributes"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.lineage_cache: Dict[str, List[LineageRecord]] = {}
    
    async def track_attribute_update(
        self,
        asset_id: str,
        attribute_name: str,
        new_value: Any,
        source_info: Dict[str, Any],
        import_context: Dict[str, Any]
    ) -> LineageRecord:
        """Track an attribute update with full lineage"""
        
        lineage_record = LineageRecord(
            attribute_name=attribute_name,
            value=new_value,
            source_id=source_info["id"],
            source_name=source_info["name"],
            source_type=source_info["type"],
            import_id=import_context["import_id"],
            timestamp=datetime.utcnow(),
            confidence_score=source_info.get("reliability_score", 0.5),
            transformation_applied=import_context.get("transformation"),
            validation_status=import_context.get("validation_status"),
            metadata={
                "raw_value": import_context.get("raw_value"),
                "processing_time_ms": import_context.get("processing_time_ms"),
                "validator_used": import_context.get("validator")
            }
        )
        
        # Store in database
        await self._persist_lineage_record(asset_id, lineage_record)
        
        # Update cache
        cache_key = f"{asset_id}:{attribute_name}"
        if cache_key not in self.lineage_cache:
            self.lineage_cache[cache_key] = []
        self.lineage_cache[cache_key].append(lineage_record)
        
        return lineage_record
    
    async def get_attribute_history(
        self, 
        asset_id: str, 
        attribute_name: str
    ) -> List[LineageRecord]:
        """Get complete history of an attribute"""
        # Implementation to fetch from database
        pass
    
    async def get_source_contribution(
        self, 
        asset_id: str
    ) -> Dict[str, Dict[str, int]]:
        """Get contribution of each source to the asset"""
        # Returns: {source_id: {attribute_count: X, last_update: Y}}
        pass
```

**Test Requirements**:
- Test lineage tracking accuracy
- Test performance with high-volume updates
- Test cache consistency

---

#### Task 2.5: Enable Parallel Raw Data Storage
- **Status**: 🔴 Blocked
- **Priority**: Medium
- **Dependencies**: Task 1.3
- **Estimated Hours**: 4
- **Location**: `backend/app/services/crewai_flows/unified_discovery_flow.py`
- **Description**: Store raw data alongside processed assets

**Implementation Requirements**:
```python
# Add to data import phase in unified_discovery_flow.py

async def _store_raw_data_parallel(self, import_data: Dict[str, Any]):
    """Store raw data in parallel with processing"""
    raw_data_repository = RawDataRepository(self.db, self.context.client_account_id)
    
    # Create raw data records for each imported item
    raw_records = []
    for item in import_data.get("items", []):
        raw_record = RawDataRecord(
            client_account_id=self.context.client_account_id,
            discovery_flow_id=self.flow_id,
            data_source_id=import_data.get("source_id"),
            import_id=import_data.get("import_id"),
            record_type=item.get("type", "unknown"),
            raw_data=item,
            hash_signature=self._calculate_hash(item),
            metadata={
                "import_timestamp": datetime.utcnow().isoformat(),
                "processing_version": "1.0"
            }
        )
        raw_records.append(raw_record)
    
    # Bulk insert for performance
    await raw_data_repository.bulk_create(raw_records)
    
    logger.info(f"Stored {len(raw_records)} raw data records")
```

---

## Phase 2: Pattern Learning Persistence (Week 3)

### Week 3: Pattern Storage Tasks

#### Task 3.1: Create Mapping Patterns Table
- **Status**: 🔴 Blocked
- **Priority**: Critical
- **Dependencies**: Task 2.1 (flow modification)
- **Estimated Hours**: 4
- **Location**: `backend/alembic/versions/`
- **Description**: Schema for reusable mapping patterns

**Implementation Requirements**:
```sql
-- Create new migration file: xxx_create_mapping_patterns_table.py
CREATE TABLE mapping_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_account_id INTEGER,  -- NULL for global patterns
    pattern_key VARCHAR(255) NOT NULL,
    source_pattern VARCHAR(255) NOT NULL,
    target_field VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,  -- exact, regex, fuzzy, semantic
    confidence_score FLOAT DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    example_values JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_account_id, pattern_key)
);

-- Indexes
CREATE INDEX idx_patterns_client ON mapping_patterns(client_account_id);
CREATE INDEX idx_patterns_confidence ON mapping_patterns(confidence_score DESC);
CREATE INDEX idx_patterns_usage ON mapping_patterns(usage_count DESC);
CREATE INDEX idx_patterns_target ON mapping_patterns(target_field);
```

---

#### Task 3.2: Modify AttributeMappingAgent for Pattern Storage
- **Status**: 🔴 Blocked
- **Priority**: Critical
- **Dependencies**: Task 3.1
- **Estimated Hours**: 8
- **Location**: `backend/app/services/crews/agents/attribute_mapping_agent.py`
- **Description**: Add pattern persistence to mapping agent

**Implementation Requirements**:
```python
# Modify AttributeMappingAgent to store successful patterns

class EnhancedAttributeMappingAgent(AttributeMappingAgent):
    """Enhanced with pattern learning and persistence"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern_repository = MappingPatternRepository(self.db, self.client_account_id)
    
    async def map_attributes(self, source_data: Dict, target_schema: Dict) -> Dict:
        """Map with pattern learning"""
        # Try to use existing patterns first
        existing_mappings = await self._apply_learned_patterns(source_data, target_schema)
        
        # Perform normal mapping for unmapped fields
        new_mappings = await super().map_attributes(source_data, target_schema)
        
        # Learn from successful mappings
        await self._learn_from_mappings(new_mappings, source_data)
        
        return {**existing_mappings, **new_mappings}
    
    async def _apply_learned_patterns(self, source_data: Dict, target_schema: Dict) -> Dict:
        """Apply previously learned patterns"""
        patterns = await self.pattern_repository.get_active_patterns(
            target_fields=list(target_schema.keys())
        )
        
        mappings = {}
        for pattern in patterns:
            if self._pattern_matches(pattern, source_data):
                mappings[pattern.target_field] = {
                    "source_field": pattern.source_pattern,
                    "confidence": pattern.confidence_score,
                    "pattern_id": pattern.id
                }
        
        return mappings
    
    async def _learn_from_mappings(self, mappings: Dict, source_data: Dict):
        """Store successful mapping patterns"""
        for target_field, mapping_info in mappings.items():
            if mapping_info.get("confidence", 0) > 0.8:  # High confidence threshold
                await self.pattern_repository.create_or_update_pattern(
                    source_pattern=mapping_info["source_field"],
                    target_field=target_field,
                    pattern_type=self._detect_pattern_type(mapping_info),
                    example_value=source_data.get(mapping_info["source_field"]),
                    confidence_score=mapping_info["confidence"]
                )
```

---

#### Task 3.3: Create Template System
- **Status**: 🔴 Blocked
- **Priority**: High
- **Dependencies**: Task 3.2
- **Estimated Hours**: 6
- **Location**: `backend/app/services/discovery/mapping_templates.py` (new file)
- **Description**: Create reusable mapping templates

**Implementation Requirements**:
```python
# Create new file: backend/app/services/discovery/mapping_templates.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class MappingTemplate:
    """Reusable mapping template"""
    id: str
    name: str
    description: str
    source_type: str  # ServiceNow, Flexera, etc.
    target_type: str  # Standard asset type
    field_mappings: Dict[str, str]
    transformation_rules: Dict[str, str]
    validation_rules: Dict[str, str]
    confidence_threshold: float = 0.8
    version: str = "1.0"
    is_active: bool = True

class MappingTemplateManager:
    """Manages mapping templates"""
    
    def __init__(self, db_session, client_account_id: Optional[int] = None):
        self.db_session = db_session
        self.client_account_id = client_account_id
        self.template_cache: Dict[str, MappingTemplate] = {}
    
    async def create_template_from_mappings(
        self,
        successful_mappings: List[Dict],
        template_name: str,
        source_type: str,
        target_type: str
    ) -> MappingTemplate:
        """Create template from successful mappings"""
        
        # Aggregate field mappings
        field_mappings = {}
        transformation_rules = {}
        
        for mapping in successful_mappings:
            if mapping["confidence"] >= self.confidence_threshold:
                field_mappings[mapping["target_field"]] = mapping["source_field"]
                
                if "transformation" in mapping:
                    transformation_rules[mapping["target_field"]] = mapping["transformation"]
        
        template = MappingTemplate(
            id=self._generate_template_id(),
            name=template_name,
            description=f"Auto-generated template for {source_type} to {target_type}",
            source_type=source_type,
            target_type=target_type,
            field_mappings=field_mappings,
            transformation_rules=transformation_rules,
            validation_rules=self._infer_validation_rules(field_mappings)
        )
        
        await self._save_template(template)
        return template
    
    async def apply_template(
        self,
        template_id: str,
        source_data: Dict
    ) -> Dict[str, Any]:
        """Apply template to source data"""
        template = await self.get_template(template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        result = {}
        for target_field, source_field in template.field_mappings.items():
            if source_field in source_data:
                value = source_data[source_field]
                
                # Apply transformation if exists
                if target_field in template.transformation_rules:
                    value = self._apply_transformation(
                        value, 
                        template.transformation_rules[target_field]
                    )
                
                # Validate if rules exist
                if target_field in template.validation_rules:
                    if self._validate_value(value, template.validation_rules[target_field]):
                        result[target_field] = value
                else:
                    result[target_field] = value
        
        return result
```

---

#### Task 3.4: Implement Cross-Engagement Pattern Sharing
- **Status**: 🔴 Blocked
- **Priority**: Medium
- **Dependencies**: Task 3.3
- **Estimated Hours**: 8
- **Location**: `backend/app/services/discovery/pattern_sharing.py` (new file)
- **Description**: Enable pattern sharing with privacy controls

**Implementation Requirements**:
```python
# Create new file: backend/app/services/discovery/pattern_sharing.py

class PatternSharingService:
    """Manages cross-engagement pattern sharing with privacy controls"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.privacy_config = PrivacyConfiguration()
    
    async def share_patterns(
        self,
        client_account_id: int,
        patterns: List[MappingPattern],
        sharing_level: str = "anonymous"
    ) -> List[str]:
        """Share patterns with privacy controls"""
        
        shared_pattern_ids = []
        
        for pattern in patterns:
            # Check if pattern meets sharing criteria
            if not self._can_share_pattern(pattern, client_account_id):
                continue
            
            # Anonymize pattern based on sharing level
            anonymized_pattern = await self._anonymize_pattern(pattern, sharing_level)
            
            # Create global pattern
            global_pattern = await self._create_global_pattern(anonymized_pattern)
            shared_pattern_ids.append(global_pattern.id)
        
        return shared_pattern_ids
    
    async def find_relevant_patterns(
        self,
        source_type: str,
        target_fields: List[str],
        client_context: Dict
    ) -> List[MappingPattern]:
        """Find relevant patterns from global repository"""
        
        # Query global patterns
        global_patterns = await self._query_global_patterns(
            source_type=source_type,
            target_fields=target_fields
        )
        
        # Filter based on client context and privacy settings
        relevant_patterns = []
        for pattern in global_patterns:
            if self._pattern_applicable(pattern, client_context):
                relevant_patterns.append(pattern)
        
        # Sort by relevance and confidence
        return sorted(
            relevant_patterns, 
            key=lambda p: (p.confidence_score, p.usage_count), 
            reverse=True
        )
```

---

#### Task 3.5: Build Pattern Confidence Evolution
- **Status**: 🔴 Blocked
- **Priority**: Medium
- **Dependencies**: Task 3.2
- **Estimated Hours**: 6
- **Location**: `backend/app/services/discovery/pattern_evolution.py` (new file)
- **Description**: Implement confidence scoring that improves with usage

**Implementation Requirements**:
```python
# Create new file: backend/app/services/discovery/pattern_evolution.py

class PatternEvolutionEngine:
    """Manages pattern confidence evolution based on usage"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.evolution_config = {
            "success_boost": 0.05,
            "failure_penalty": 0.10,
            "time_decay_factor": 0.01,
            "min_confidence": 0.1,
            "max_confidence": 0.99
        }
    
    async def record_pattern_usage(
        self,
        pattern_id: str,
        was_successful: bool,
        user_feedback: Optional[Dict] = None
    ):
        """Record pattern usage and update confidence"""
        
        pattern = await self.pattern_repository.get(pattern_id)
        
        if not pattern:
            return
        
        # Update usage counts
        pattern.usage_count += 1
        if was_successful:
            pattern.success_count += 1
        else:
            pattern.failure_count += 1
        
        # Calculate new confidence score
        old_confidence = pattern.confidence_score
        new_confidence = self._calculate_new_confidence(
            old_confidence,
            was_successful,
            pattern.usage_count,
            user_feedback
        )
        
        pattern.confidence_score = new_confidence
        pattern.last_used_at = datetime.utcnow()
        
        # Store evolution history
        await self._record_evolution_history(
            pattern_id,
            old_confidence,
            new_confidence,
            was_successful,
            user_feedback
        )
        
        await self.pattern_repository.update(pattern)
    
    def _calculate_new_confidence(
        self,
        current_confidence: float,
        was_successful: bool,
        usage_count: int,
        user_feedback: Optional[Dict]
    ) -> float:
        """Calculate new confidence score with bounded evolution"""
        
        # Base adjustment
        if was_successful:
            adjustment = self.evolution_config["success_boost"]
        else:
            adjustment = -self.evolution_config["failure_penalty"]
        
        # Reduce adjustment magnitude as usage increases (stabilization)
        adjustment *= (1 / (1 + 0.1 * usage_count))
        
        # Apply user feedback if provided
        if user_feedback:
            feedback_score = user_feedback.get("accuracy", 0.5)
            adjustment *= feedback_score
        
        # Calculate new confidence
        new_confidence = current_confidence + adjustment
        
        # Apply bounds
        new_confidence = max(
            self.evolution_config["min_confidence"],
            min(self.evolution_config["max_confidence"], new_confidence)
        )
        
        return new_confidence
```

---

## Phase 3: Multi-Source Reconciliation (Weeks 4-5)

### Week 4: Conflict Detection Tasks

#### Task 4.1: Create DataReconciliationCrew
- **Status**: 🔴 Blocked
- **Priority**: Critical
- **Dependencies**: Task 2.3 (conflict detection)
- **Estimated Hours**: 12
- **Location**: `backend/app/services/crews/data_reconciliation_crew.py` (new file)
- **Description**: New crew for multi-source reconciliation

**Implementation Requirements**:
```python
# Create new file: backend/app/services/crews/data_reconciliation_crew.py

from crewai import Agent, Task, Crew
from typing import Dict, List, Any

class DataReconciliationCrew(BaseCrew):
    """Crew for multi-source data reconciliation"""
    
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context)
        self.conflict_detector = ConflictDetector()
        self.merge_strategy_factory = MergeStrategyFactory()
    
    def create_agents(self) -> List[Agent]:
        """Create specialized reconciliation agents"""
        
        # Conflict Detection Agent
        conflict_detection_agent = Agent(
            role="Data Conflict Detection Specialist",
            goal="Identify conflicts between multiple data sources",
            backstory="Expert in data quality and anomaly detection",
            tools=[
                self.tool_registry.get_tool("data_comparison_tool"),
                self.tool_registry.get_tool("anomaly_detection_tool")
            ],
            verbose=True
        )
        
        # Source Evaluation Agent
        source_evaluation_agent = Agent(
            role="Data Source Reliability Evaluator",
            goal="Evaluate and score data source reliability",
            backstory="Expert in data source assessment and quality metrics",
            tools=[
                self.tool_registry.get_tool("source_analysis_tool"),
                self.tool_registry.get_tool("quality_metrics_tool")
            ],
            verbose=True
        )
        
        # Resolution Strategy Agent
        resolution_strategy_agent = Agent(
            role="Conflict Resolution Strategist",
            goal="Determine optimal resolution strategy for conflicts",
            backstory="Expert in decision algorithms and data reconciliation",
            tools=[
                self.tool_registry.get_tool("strategy_selection_tool"),
                self.tool_registry.get_tool("resolution_engine_tool")
            ],
            verbose=True
        )
        
        # Anomaly Detection Agent
        anomaly_detection_agent = Agent(
            role="Data Anomaly Detection Expert",
            goal="Detect suspicious patterns and potential data quality issues",
            backstory="Specialist in pattern recognition and security",
            tools=[
                self.tool_registry.get_tool("pattern_analysis_tool"),
                self.tool_registry.get_tool("security_validation_tool")
            ],
            verbose=True
        )
        
        return [
            conflict_detection_agent,
            source_evaluation_agent,
            resolution_strategy_agent,
            anomaly_detection_agent
        ]
    
    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        """Create reconciliation tasks"""
        
        conflict_agent, source_agent, strategy_agent, anomaly_agent = agents
        
        # Task 1: Detect conflicts
        detect_conflicts_task = Task(
            description="""Analyze asset data from multiple sources and identify conflicts:
            1. Compare attribute values across sources
            2. Identify missing or additional attributes
            3. Flag type mismatches
            4. Calculate conflict severity
            5. Group related conflicts
            """,
            agent=conflict_agent,
            expected_output="List of detected conflicts with severity ratings"
        )
        
        # Task 2: Evaluate sources
        evaluate_sources_task = Task(
            description="""Evaluate reliability of each data source:
            1. Analyze historical accuracy
            2. Check data completeness
            3. Assess update frequency
            4. Determine authoritative attributes
            5. Calculate reliability scores
            """,
            agent=source_agent,
            expected_output="Source reliability assessment with scores"
        )
        
        # Task 3: Detect anomalies
        detect_anomalies_task = Task(
            description="""Identify suspicious patterns in data:
            1. Check for unusual value changes
            2. Detect potential data corruption
            3. Identify security concerns
            4. Flag statistical outliers
            5. Assess data integrity risks
            """,
            agent=anomaly_agent,
            expected_output="Anomaly detection report with risk assessment"
        )
        
        # Task 4: Develop resolution strategy
        develop_strategy_task = Task(
            description="""Create resolution strategy based on conflicts and source evaluation:
            1. Prioritize conflicts by business impact
            2. Select appropriate merge strategy
            3. Define resolution rules
            4. Create manual review queue
            5. Generate resolution recommendations
            """,
            agent=strategy_agent,
            expected_output="Comprehensive resolution strategy with action items",
            context=[detect_conflicts_task, evaluate_sources_task, detect_anomalies_task]
        )
        
        return [
            detect_conflicts_task,
            evaluate_sources_task,
            detect_anomalies_task,
            develop_strategy_task
        ]
```

---

### Additional Parallel Tasks Available

The following tasks can be worked on in parallel by different AI agents:

#### Parallel Group A (Database/Infrastructure):
- **Task 1.1**: Create Assets Table (Ready)
- **Task 1.2**: Create Data Sources Table (Ready)
- **Task 1.3**: Create Raw Data Records Table (Ready)

#### Parallel Group B (After Group A completes):
- **Task 1.4**: Create Asset Versions Table
- **Task 1.5**: Create Asset Attributes Table
- **Task 3.1**: Create Mapping Patterns Table

#### Parallel Group C (Tool Development - Can start immediately):
- Create new tools for Tool Registry:
  - `data_comparison_tool`
  - `anomaly_detection_tool`
  - `merge_algorithm_tool`
  - `pattern_analysis_tool`
  - `confidence_scoring_tool`

#### Parallel Group D (Repository Layer - After Group A):
- Create repository classes:
  - `AssetRepository`
  - `DataSourceRepository`
  - `RawDataRepository`
  - `MappingPatternRepository`

## Progress Tracking

### Completed Tasks: 0/40
### In Progress Tasks: 0/40
### Ready Tasks: 3/40
### Blocked Tasks: 37/40

## Notes for AI Agents

1. **Always check dependencies** before starting a task
2. **Update task status** when beginning and completing work
3. **Run tests** as specified in each task
4. **Follow existing patterns** in the codebase
5. **Document any blockers** encountered
6. **Create integration tests** for cross-component functionality

## Success Metrics

- **Pattern Reuse Rate**: Target 60%+
- **Conflict Resolution Accuracy**: Target 90%+
- **Asset Enhancement Rate**: Target 80%+
- **Performance**: Handle 10K+ assets efficiently
- **Test Coverage**: Maintain 80%+ coverage