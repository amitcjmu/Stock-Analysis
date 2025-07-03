# AI Force Migration Platform - Data Flow Diagram

## Overview
This document provides a comprehensive data flow diagram for the AI Force Migration Platform, showing how data moves through the system from user interaction to final processing.

## High-Level Data Flow

```mermaid
graph TB
    subgraph "Frontend (Vercel)"
        UI[React UI]
        Hooks[useUnifiedDiscoveryFlow Hook]
        UI --> Hooks
    end

    subgraph "API Gateway"
        APIv3[API v3 Endpoints<br/>Primary Target]
        APIv1[API v1 Endpoints<br/>Still in Use]
        Hooks --> APIv3
        Hooks -.-> APIv1
    end

    subgraph "Multi-Tenant Context Layer"
        Auth[Authentication]
        Context[Context Extraction<br/>X-Client-Account-ID<br/>X-Engagement-ID<br/>X-User-ID]
        APIv3 --> Auth
        APIv1 --> Auth
        Auth --> Context
    end

    subgraph "Service Layer"
        DFS[V3DiscoveryFlowService]
        DIS[V3DataImportService]
        FMS[V3FieldMappingService]
        Context --> DFS
        Context --> DIS
        Context --> FMS
    end

    subgraph "CrewAI Flow Orchestration"
        UDF[UnifiedDiscoveryFlow]
        FSB[FlowStateBridge]
        DFS --> UDF
        UDF --> FSB
    end

    subgraph "Repository Layer"
        CAR[ContextAwareRepository]
        DFR[DiscoveryFlowRepository]
        DIR[DataImportRepository]
        FMR[FieldMappingRepository]
        DFS --> CAR
        DIS --> CAR
        FMS --> CAR
        CAR --> DFR
        CAR --> DIR
        CAR --> FMR
    end

    subgraph "PostgreSQL Database"
        DF[DiscoveryFlow Table]
        DI[DataImport Table]
        FM[FieldMapping Table]
        AS[Asset Table]
        DFR --> DF
        DIR --> DI
        FMR --> FM
        FSB --> DF
    end

    subgraph "CrewAI Agents"
        DVA[Data Validation Agent]
        AMA[Attribute Mapping Agent]
        DCA[Data Cleansing Agent]
        ADA[Asset Discovery Agent]
        DIA[Dependency Intelligence Agent]
        UDF --> DVA
        UDF --> AMA
        UDF --> DCA
        UDF --> ADA
        UDF --> DIA
    end

    style APIv3 fill:#90EE90
    style APIv1 fill:#FFE4B5
    style UDF fill:#87CEEB
    style FSB fill:#87CEEB
```

## Detailed Flow Sequences

### 1. Data Import Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant APIv3
    participant DataImportService
    participant DiscoveryFlowService
    participant CrewAI
    participant PostgreSQL

    User->>Frontend: Upload CMDB File
    Frontend->>APIv3: POST /api/v3/data-import/imports/upload<br/>Headers: X-Client-Account-ID, X-Engagement-ID
    APIv3->>DataImportService: Process Upload
    DataImportService->>PostgreSQL: Create DataImport Record
    DataImportService->>DiscoveryFlowService: Create Associated Flow
    DiscoveryFlowService->>PostgreSQL: Create DiscoveryFlow Record
    DiscoveryFlowService->>CrewAI: Initialize UnifiedDiscoveryFlow
    CrewAI->>PostgreSQL: Store Initial State
    PostgreSQL-->>APIv3: Return import_id, flow_id
    APIv3-->>Frontend: Import Created Response
    Frontend->>Frontend: Navigate to Flow Status
```

### 2. CrewAI Flow Execution

```mermaid
stateDiagram-v2
    [*] --> Initialize: @start()
    Initialize --> DataValidation: @listen(initialize)
    DataValidation --> AttributeMapping: @listen(data_validation)
    AttributeMapping --> DataCleansing: @listen(attribute_mapping)
    DataCleansing --> AssetDiscovery: @listen(data_cleansing)
    AssetDiscovery --> ParallelAnalysis: @listen(asset_discovery)
    
    state ParallelAnalysis {
        [*] --> DependencyAnalysis
        [*] --> TechDebtAnalysis
        [*] --> RiskAssessment
        DependencyAnalysis --> [*]
        TechDebtAnalysis --> [*]
        RiskAssessment --> [*]
    }
    
    ParallelAnalysis --> UserApproval: @listen(parallel_analysis)
    UserApproval --> WavePlanning: Approved
    UserApproval --> [*]: Rejected
    WavePlanning --> [*]: Complete
```

### 3. Multi-Tenant Data Access Pattern

```mermaid
graph LR
    subgraph "Request Flow"
        REQ[API Request] --> MW[Middleware]
        MW --> CTX[Extract Context]
        CTX --> VAL[Validate Tenant]
    end

    subgraph "Data Access"
        VAL --> REPO[Create Repository<br/>with client_account_id]
        REPO --> QUERY[Auto-filtered Query]
        QUERY --> DB[(PostgreSQL)]
    end

    subgraph "Response"
        DB --> FILTER[Tenant-Scoped Results]
        FILTER --> RESP[API Response]
    end

    style CTX fill:#FFD700
    style REPO fill:#FFD700
```

### 4. State Management Flow

```mermaid
graph TD
    subgraph "CrewAI State"
        CS[CrewAI Flow State<br/>In-Memory]
        CS --> FSB[FlowStateBridge]
    end

    subgraph "Persistence Layer"
        FSB --> PSP[PostgreSQLFlowPersistence]
        PSP --> SER[State Serialization]
        SER --> DB[(PostgreSQL)]
    end

    subgraph "State Recovery"
        DB --> DESER[State Deserialization]
        DESER --> REC[FlowStateRecovery]
        REC --> CS
    end

    style FSB fill:#87CEEB
    style PSP fill:#87CEEB
```

### 5. Field Mapping Flow

```mermaid
flowchart LR
    subgraph "Auto-Generation"
        UPLOAD[File Upload] --> ANALYZE[Schema Analyzer Tool]
        ANALYZE --> SUGGEST[AI Suggestions]
        SUGGEST --> MAP[Initial Mappings]
    end

    subgraph "User Review"
        MAP --> UI[Mapping UI]
        UI --> EDIT[User Edits]
        EDIT --> VALIDATE[Validation]
    end

    subgraph "Application"
        VALIDATE --> SAVE[Save Mappings]
        SAVE --> APPLY[Apply to Data]
        APPLY --> TRANSFORM[Data Transformation]
    end

    style ANALYZE fill:#90EE90
    style SUGGEST fill:#90EE90
```

## Key Data Flow Characteristics

### 1. **Multi-Tenant Isolation**
- Every request includes tenant context headers
- All database queries automatically filtered by client_account_id
- No cross-tenant data access possible

### 2. **Event-Driven Architecture**
- CrewAI Flow uses @start/@listen decorators
- Asynchronous phase execution
- Real-time status updates via polling

### 3. **State Management**
- PostgreSQL as single source of truth
- CrewAI state persisted after each phase
- Automatic recovery on failure

### 4. **API Transition**
- v3 API is target architecture
- v1 API still in use during remediation
- Frontend uses mixed API calls

### 5. **Agent Intelligence**
- Business logic in CrewAI agents
- No hard-coded rules
- Learning from user feedback

## Data Security Flow

```mermaid
graph TD
    subgraph "Authentication Layer"
        LOGIN[User Login] --> AUTH[Supabase Auth]
        AUTH --> TOKEN[JWT Token]
    end

    subgraph "Authorization Layer"
        TOKEN --> VALIDATE[Token Validation]
        VALIDATE --> PROFILE[Load UserProfile]
        PROFILE --> CHECK[Check Status=Active]
    end

    subgraph "Tenant Isolation"
        CHECK --> CONTEXT[Set Tenant Context]
        CONTEXT --> SCOPE[Scope All Queries]
        SCOPE --> DATA[Tenant Data Only]
    end

    style AUTH fill:#FF6B6B
    style CHECK fill:#FF6B6B
    style SCOPE fill:#FF6B6B
```

## Performance Considerations

1. **Caching Strategy**
   - 15-minute cache for web fetches
   - React Query caching for API responses
   - PostgreSQL query optimization

2. **Async Processing**
   - All CrewAI phases run asynchronously
   - Background job processing for heavy operations
   - Event-driven updates reduce polling

3. **Database Optimization**
   - Indexed on client_account_id for all tables
   - JSON fields for flexible agent data
   - Connection pooling via AsyncSessionLocal

## Current Remediation Impact

### Active Issues Affecting Data Flow:
1. **Flow Context Sync**: Sometimes data written to wrong tables
2. **Session ID References**: 132+ files still use legacy identifiers
3. **API Version Mix**: Frontend confusion between v1/v3
4. **Field Mapping UI**: Shows "0 active flows" incorrectly

### Mitigation Strategies:
- Always include all context headers
- Verify flow_id in responses
- Test both API versions
- Use flow debugging tools

---

*Last Updated: January 2025*  
*Platform State: Phase 5 + Remediation Phase 1 (75% complete)*