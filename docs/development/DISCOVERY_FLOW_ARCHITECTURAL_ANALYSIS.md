# 🔍 Multi-Flow Architectural Analysis & Database Schema Redesign

**Date:** January 27, 2025  
**Status:** Critical Architecture Review  
**Priority:** URGENT - System Breaking Issues  
**Scope:** Multi-Flow Platform Architecture (Discovery, Assess, Plan, Execute, Modernize)

## 📊 Executive Summary

The AI Force Migration Platform requires a **unified multi-flow architecture** supporting 5 distinct workflow types with proper data normalization, multi-tenant isolation, and complete rollback capabilities. The current implementation suffers from severe architectural fragmentation that prevents seamless flow progression and creates data sprawl across 47+ disconnected tables.

### **Multi-Flow Architecture Requirements**
Based on the navigation structure shown:
- **Discovery Flow**: Data Import → Attribute Mapping → Data Cleansing → Inventory → Dependencies → Tech Debt
- **Assess Flow**: Overview → Treatment → Wave Planning → Roadmap → Editor
- **Plan Flow**: Overview → Timeline → Resource → Target
- **Execute Flow**: Overview → Rehost → Replatform → Cutover → Reports  
- **Modernize Flow**: Refactor → Rearchitect → Rewrite workflows

### **Critical Issues Identified**
- ❌ **Data Sprawl**: 47+ tables with unclear relationships and duplicate data storage
- ❌ **Flow Isolation**: No unified framework supporting all 5 workflow types
- ❌ **Multi-Tenant Gaps**: Inconsistent client account scoping across tables
- ❌ **Rollback Impossibility**: No mechanism to cleanly rollback entire flows
- ❌ **Normalization Issues**: Large JSON blobs mixed with over-normalized structures
- ❌ **Cross-Flow Dependencies**: No clear handoff mechanisms between flows

## 🏗️ Current Database Schema Analysis

### **Schema Complexity Assessment**
The database schema reveals significant architectural problems:

#### **Over-Normalization Issues**
- **Import Processing Steps**: Separate table for workflow steps that should be part of main flow
- **Field Mappings**: Isolated from workflow context, causing disconnection
- **Asset Dependencies**: Separate table when could be part of asset model
- **Quality Issues**: Fragmented across multiple tracking tables

#### **Under-Normalization Issues**
- **Workflow States**: Massive JSON blobs storing all flow data without structure
- **Raw Import Records**: Large JSON data without proper field extraction
- **CrewAI Extensions**: Unstructured data storage without clear schema

#### **Multi-Tenancy Inconsistencies**
- **Missing Client Scoping**: Some tables lack proper client_account_id fields
- **Inconsistent Engagement Linking**: Not all tables properly link to engagements
- **Data Isolation Gaps**: Cross-tenant data leakage possible in current schema

## 🚨 Architectural Breaks by Flow Type

### **Discovery Flow Breaks**
```
❌ Data Import → WorkflowState (NO CONNECTION)
❌ Raw Import Records → Asset Creation (MANUAL ONLY)
❌ Field Mappings → Discovery Results (ISOLATED)
❌ Discovery → Assessment Handoff (MISSING)
```

### **Assessment Flow Breaks**
```
❌ Discovery Assets → Assessment Input (NO AUTOMATION)
❌ Treatment Planning → Wave Creation (DISCONNECTED)
❌ Assessment → Plan Handoff (MISSING)
```

### **Plan Flow Breaks**
```
❌ Assessment Results → Planning Input (MANUAL)
❌ Resource Planning → Timeline (FRAGMENTED)
❌ Plan → Execute Handoff (MISSING)
```

### **Execute Flow Breaks**
```
❌ Plan → Execution Tasks (NO AUTOMATION)
❌ Rehost/Replatform Progress → Reporting (ISOLATED)
❌ Execute → Modernize Handoff (MISSING)
```

### **Modernize Flow Breaks**
```
❌ Execute Results → Modernization Input (MANUAL)
❌ Refactor/Rearchitect → Progress Tracking (FRAGMENTED)
```

## 🏛️ Proposed Unified Database Architecture

### **Core Principle: Flow-Centric Design**
Design around flows as first-class entities with proper normalization and multi-tenancy.

#### **1. Master Flow Management**
```python
class MigrationFlow(Base):
    """Master flow entity supporting all flow types"""
    __tablename__ = "migration_flows"
    
    # Core identification
    id = Column(UUID, primary_key=True)
    flow_type = Column(Enum(FlowType))  # discovery, assess, plan, execute, modernize
    
    # Multi-tenant isolation
    client_account_id = Column(UUID, ForeignKey('client_accounts.id'), nullable=False, index=True)
    engagement_id = Column(UUID, ForeignKey('engagements.id'), nullable=False, index=True)
    
    # Flow metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(FlowStatus))  # draft, active, completed, failed, cancelled
    
    # Flow progression
    current_phase = Column(String(100), nullable=False)
    progress_percentage = Column(Float, default=0.0)
    phase_completion = Column(JSON, default={})
    
    # Flow relationships
    parent_flow_id = Column(UUID, ForeignKey('migration_flows.id'))  # For flow handoffs
    source_flow_type = Column(Enum(FlowType))  # Which flow this was created from
    
    # CrewAI integration
    crewai_flow_id = Column(UUID, index=True)  # CrewAI-generated flow ID
    
    # Rollback capability
    rollback_point = Column(JSON, default={})  # Snapshot for rollback
    can_rollback = Column(Boolean, default=True)
    rollback_reason = Column(Text)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID, ForeignKey('users.id'), nullable=False)
```

#### **2. Flow Phase Management**
```python
class FlowPhase(Base):
    """Individual phases within flows with proper tracking"""
    __tablename__ = "flow_phases"
    
    id = Column(UUID, primary_key=True)
    flow_id = Column(UUID, ForeignKey('migration_flows.id'), nullable=False)
    
    # Phase definition
    phase_name = Column(String(100), nullable=False)
    phase_order = Column(Integer, nullable=False)
    phase_type = Column(String(50))  # data_processing, analysis, planning, execution
    
    # Phase status
    status = Column(Enum(PhaseStatus))  # pending, active, completed, failed, skipped
    progress_percentage = Column(Float, default=0.0)
    
    # Phase data (normalized)
    input_data = Column(JSON)  # Structured input data
    output_data = Column(JSON)  # Structured output data
    phase_config = Column(JSON)  # Phase-specific configuration
    
    # Phase execution
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Error handling
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)
    
    # Rollback data
    rollback_snapshot = Column(JSON)  # Phase state before execution
```

#### **3. Flow Data Management**
```python
class FlowDataEntity(Base):
    """Normalized storage for flow-generated data"""
    __tablename__ = "flow_data_entities"
    
    id = Column(UUID, primary_key=True)
    flow_id = Column(UUID, ForeignKey('migration_flows.id'), nullable=False)
    phase_id = Column(UUID, ForeignKey('flow_phases.id'), nullable=True)
    
    # Multi-tenant isolation
    client_account_id = Column(UUID, ForeignKey('client_accounts.id'), nullable=False, index=True)
    engagement_id = Column(UUID, ForeignKey('engagements.id'), nullable=False, index=True)
    
    # Entity classification
    entity_type = Column(String(50), nullable=False)  # asset, dependency, mapping, analysis
    entity_subtype = Column(String(50))  # server, database, network, etc.
    
    # Structured data
    entity_data = Column(JSON, nullable=False)  # Structured entity data
    metadata = Column(JSON, default={})  # Additional metadata
    
    # Data lineage
    source_entity_id = Column(UUID, ForeignKey('flow_data_entities.id'))  # Data source tracking
    transformation_log = Column(JSON, default=[])  # How data was transformed
    
    # Quality tracking
    quality_score = Column(Float)
    validation_status = Column(String(20))
    validation_errors = Column(JSON, default=[])
    
    # Lifecycle
    is_active = Column(Boolean, default=True)
    archived_at = Column(DateTime(timezone=True))
    archived_reason = Column(Text)
```

#### **4. Flow Handoffs**
```python
class FlowHandoff(Base):
    """Manages data handoffs between flows"""
    __tablename__ = "flow_handoffs"
    
    id = Column(UUID, primary_key=True)
    
    # Source and target flows
    source_flow_id = Column(UUID, ForeignKey('migration_flows.id'), nullable=False)
    target_flow_id = Column(UUID, ForeignKey('migration_flows.id'), nullable=False)
    
    # Handoff metadata
    handoff_type = Column(String(50), nullable=False)  # discovery_to_assess, assess_to_plan, etc.
    handoff_status = Column(String(20), default='pending')  # pending, completed, failed
    
    # Data package
    handoff_data = Column(JSON, nullable=False)  # Structured handoff package
    data_summary = Column(JSON)  # Summary for validation
    
    # Validation
    validation_rules = Column(JSON)  # Rules for handoff validation
    validation_results = Column(JSON)  # Validation outcomes
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
```

#### **5. Unified Asset Management**
```python
class Asset(Base):
    """Unified asset model linked to flows"""
    __tablename__ = "assets"
    
    # Existing fields...
    
    # Flow integration
    source_flow_id = Column(UUID, ForeignKey('migration_flows.id'))  # Flow that created asset
    discovery_data_entity_id = Column(UUID, ForeignKey('flow_data_entities.id'))  # Link to discovery data
    
    # Flow progression tracking
    discovery_completed = Column(Boolean, default=False)
    assessment_completed = Column(Boolean, default=False)
    planning_completed = Column(Boolean, default=False)
    execution_completed = Column(Boolean, default=False)
    modernization_completed = Column(Boolean, default=False)
    
    # Cross-flow data
    flow_history = Column(JSON, default=[])  # Track which flows processed this asset
```

### **Database Normalization Strategy**

#### **Properly Normalized Entities**
- **Flow Phases**: Separate table for phase management with clear structure
- **Data Entities**: Normalized storage for all flow-generated data
- **Handoffs**: Dedicated table for inter-flow data transfer
- **Assets**: Enhanced with flow integration but maintain entity integrity

#### **Strategic Denormalization**
- **Flow Progress**: Keep phase completion in main flow table for performance
- **Entity Metadata**: Store frequently accessed metadata with entities
- **Handoff Summaries**: Cache summary data for quick validation

#### **JSON Usage Guidelines**
- **Configuration Data**: Use JSON for flexible configuration storage
- **Structured Results**: Use JSON for well-defined result structures
- **Avoid**: Large unstructured data dumps in JSON fields

### **Multi-Tenancy Architecture**

#### **Consistent Client Scoping**
```python
# Every table must have these fields
client_account_id = Column(UUID, ForeignKey('client_accounts.id'), nullable=False, index=True)
engagement_id = Column(UUID, ForeignKey('engagements.id'), nullable=False, index=True)
```

#### **Data Isolation Enforcement**
- **Repository Pattern**: All data access through context-aware repositories
- **Query Filtering**: Automatic client account filtering on all queries
- **Cross-Tenant Prevention**: Explicit checks to prevent data leakage

#### **Engagement-Level Isolation**
- **Flow Scoping**: All flows scoped to specific engagements
- **Data Segregation**: Complete data isolation between engagements
- **Resource Allocation**: Per-engagement resource tracking

### **Rollback Architecture**

#### **Flow-Level Rollback**
```python
class FlowRollback(Base):
    """Complete flow rollback management"""
    __tablename__ = "flow_rollbacks"
    
    id = Column(UUID, primary_key=True)
    flow_id = Column(UUID, ForeignKey('migration_flows.id'), nullable=False)
    
    # Rollback metadata
    rollback_type = Column(String(50))  # phase, flow, cascade
    rollback_reason = Column(Text, nullable=False)
    rollback_scope = Column(JSON)  # What will be rolled back
    
    # Snapshot data
    flow_snapshot = Column(JSON, nullable=False)  # Complete flow state
    data_snapshot = Column(JSON, nullable=False)  # All associated data
    asset_snapshot = Column(JSON)  # Asset states before flow
    
    # Rollback execution
    rollback_status = Column(String(20), default='pending')
    executed_at = Column(DateTime(timezone=True))
    execution_log = Column(JSON, default=[])
    
    # Recovery
    recovery_actions = Column(JSON)  # Actions taken during rollback
    data_integrity_check = Column(JSON)  # Post-rollback validation
```

#### **Cascade Rollback Support**
- **Dependent Flow Identification**: Track which flows depend on others
- **Cascade Impact Analysis**: Calculate rollback impact across flows
- **Selective Rollback**: Ability to rollback specific components
- **Data Integrity Validation**: Ensure data consistency post-rollback

## 🎯 Implementation Strategy

### **Phase 1: Core Flow Framework (Days 1-5)**
1. **Create Master Flow Tables**: MigrationFlow, FlowPhase, FlowDataEntity
2. **Implement Multi-Tenancy**: Consistent client scoping across all tables
3. **Build Repository Pattern**: Context-aware data access layer
4. **Create Migration Scripts**: Migrate existing data to new structure

### **Phase 2: Flow Integration (Days 6-10)**
1. **Discovery Flow Integration**: Connect existing discovery components
2. **Assessment Flow Setup**: Prepare assessment flow structure
3. **Handoff Mechanisms**: Implement inter-flow data transfer
4. **Rollback Framework**: Basic rollback capability

### **Phase 3: Advanced Features (Days 11-15)**
1. **Complete Rollback System**: Full cascade rollback capability
2. **Cross-Flow Analytics**: Flow performance and progression tracking
3. **Data Lineage**: Complete data transformation tracking
4. **Quality Assurance**: Automated data validation and quality scoring

### **Phase 4: Platform Extension (Days 16-20)**
1. **Plan Flow Implementation**: Full planning workflow
2. **Execute Flow Implementation**: Execution workflow with progress tracking
3. **Modernize Flow Implementation**: Modernization workflow support
4. **Performance Optimization**: Query optimization and caching

## 📊 Success Criteria

### **Technical Success**
- ✅ Single unified framework supports all 5 flow types
- ✅ Complete multi-tenant data isolation with no leakage
- ✅ Full rollback capability for any flow or cascade
- ✅ Proper normalization with strategic denormalization
- ✅ Clear data lineage and transformation tracking

### **User Experience Success**
- ✅ Seamless navigation between all flow phases
- ✅ Automatic handoffs between flows (Discovery → Assess → Plan → Execute → Modernize)
- ✅ Clear progress tracking across entire migration journey
- ✅ Reliable rollback with data integrity preservation

### **Business Success**
- ✅ Complete end-to-end migration workflow support
- ✅ Enterprise-grade multi-tenancy and data isolation
- ✅ Audit-compliant rollback and recovery capabilities
- ✅ Scalable architecture supporting future flow types

---

**This unified multi-flow architecture addresses the current fragmentation while providing a scalable foundation for the complete AI Force Migration Platform supporting all workflow types with proper data management, multi-tenancy, and rollback capabilities.** 