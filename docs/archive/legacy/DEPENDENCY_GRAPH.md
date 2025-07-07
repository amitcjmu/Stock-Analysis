# 🔗 **LEGACY CODE DEPENDENCY GRAPH ANALYSIS**

*AI Force Migration Platform - Discovery Flow Remediation*

**Analysis Date:** January 2025  
**Scope:** Backend legacy code dependencies and cleanup sequence  

---

## **📊 OVERVIEW**

This document provides visual dependency graphs and analysis for legacy code cleanup in the Discovery flow. Understanding these dependencies is critical for determining the safe order of removal and migration operations.

---

## **🎯 CRITICAL PATH ANALYSIS**

### **Primary Dependency Chain**
```mermaid
graph TD
    A[Database Schema<br/>session_id columns] --> B[Data Models<br/>session_id fields]
    B --> C[Service Layer<br/>session-based logic]
    C --> D[API Endpoints<br/>session_id parameters]
    D --> E[Frontend Integration<br/>mixed v1/v3 usage]
    
    F[Missing Models<br/>MappingLearningPattern] --> G[Broken Imports<br/>12 files affected]
    G --> H[Disabled Services<br/>vector_utils stubbed]
    H --> I[Reduced Functionality<br/>no pattern learning]
    
    J[Pseudo-Agent Base] --> K[Agent Implementations<br/>8 mixed agents]
    K --> L[Business Logic<br/>hardcoded rules]
    L --> M[CrewAI Integration<br/>inconsistent patterns]
    
    style A fill:#ff6b6b
    style F fill:#ff6b6b
    style J fill:#ff6b6b
```

### **Cleanup Sequence Priority**
1. **🔴 Database Foundation** - Remove schema dependencies first
2. **🟡 Import Chain Repair** - Fix broken references  
3. **🟢 Service Layer Migration** - Update business logic
4. **🔵 API Consolidation** - Standardize endpoints
5. **🟣 Documentation Cleanup** - Remove legacy references

---

## **📋 SESSION ID DEPENDENCY MAP**

### **Database Level Dependencies**
```mermaid
graph LR
    subgraph "Database Tables"
        DF[discovery_flows] --> |import_session_id| DIS[data_import_sessions]
        AS[assets] --> |session_id| DIS
        AAL[access_audit_log] --> |session_id| DIS
        FDA[flow_deletion_audit] --> |session_id| DIS
        LUL[llm_usage_logs] --> |session_id→flow_id| DIS
    end
    
    subgraph "Migration Script"
        MIG[remove_session_id_final_cleanup.py]
        MIG --> DF
        MIG --> AS
        MIG --> AAL
        MIG --> FDA
        MIG --> LUL
    end
    
    style DF fill:#ffeb3b
    style DIS fill:#4caf50
    style MIG fill:#2196f3
```

### **Service Layer Dependencies**
```mermaid
graph TD
    A[session_manager.py<br/>Core session logic] --> B[data_import_validation_service.py<br/>File-based sessions]
    A --> C[import_storage_handler.py<br/>validation_session_id]
    A --> D[discovery_flow_listener.py<br/>Fallback logic]
    
    E[session_to_flow.py<br/>Compatibility bridge] --> F[Flow State Management]
    E --> G[API Response Translation]
    
    B --> H[Frontend Session APIs]
    C --> H
    D --> H
    
    style A fill:#ff5722
    style E fill:#4caf50
    style H fill:#9c27b0
```

### **API Endpoint Dependencies**
```mermaid
graph LR
    subgraph "V1 API Endpoints"
        V1A[/unified-discovery/*]
        V1B[/session-comparison/*]
        V1C[/data-import handlers]
    end
    
    subgraph "V3 API Endpoints"
        V3A[/discovery-flow/*]
        V3B[/data-import/*]
        V3C[/field-mapping/*]
    end
    
    subgraph "Frontend Usage"
        FE[React Components]
    end
    
    V1A -.-> |Legacy| FE
    V1B -.-> |Legacy| FE
    V1C -.-> |Legacy| FE
    V3A --> |Current| FE
    V3B --> |Current| FE
    V3C --> |Current| FE
    
    style V1A fill:#ffeb3b
    style V1B fill:#ff5722
    style V1C fill:#ffeb3b
    style V3A fill:#4caf50
    style V3B fill:#4caf50
    style V3C fill:#4caf50
```

---

## **🤖 AGENT ARCHITECTURE DEPENDENCIES**

### **Agent Implementation Hierarchy**
```mermaid
graph TD
    subgraph "Legacy Base Classes"
        OLD_BASE[base_discovery_agent.py<br/>Old pseudo-agent base]
        OLD_BASE --> PSEUDO1[data_import_validation_agent.py]
        OLD_BASE --> PSEUDO2[attribute_mapping_agent.py]
        OLD_BASE --> PSEUDO3[tech_debt_analysis_agent.py]
        OLD_BASE --> PSEUDO4[dependency_analysis_agent.py]
    end
    
    subgraph "Modern Base Classes"
        NEW_BASE[base_agent.py<br/>CrewAI-based base]
        NEW_BASE --> CREW1[data_cleansing_agent_crewai.py]
        NEW_BASE --> CREW2[asset_inventory_agent_crewai.py]
        NEW_BASE --> CREW3[field_mapping_agent.py]
    end
    
    subgraph "Dual Implementations"
        DUAL1[data_cleansing_agent.py] -.-> |Remove| OLD_BASE
        DUAL2[asset_inventory_agent.py] -.-> |Remove| OLD_BASE
        CREW1 --> |Keep| NEW_BASE
        CREW2 --> |Keep| NEW_BASE
    end
    
    subgraph "Flow Integration"
        UDF[UnifiedDiscoveryFlow]
        UDF --> PSEUDO1
        UDF --> PSEUDO2
        UDF --> PSEUDO3
        UDF --> PSEUDO4
        UDF --> CREW1
        UDF --> CREW2
        UDF --> CREW3
    end
    
    style OLD_BASE fill:#ff5722
    style NEW_BASE fill:#4caf50
    style DUAL1 fill:#ffeb3b
    style DUAL2 fill:#ffeb3b
```

### **Agent Conversion Dependencies**
```mermaid
graph LR
    A[Pseudo-Agent Logic<br/>Hard-coded rules] --> B[Business Requirements<br/>Domain knowledge]
    B --> C[CrewAI Agent<br/>LLM-driven decisions]
    
    A --> D[Testing Framework<br/>Validate outputs]
    D --> C
    
    A --> E[Performance Baselines<br/>Accuracy metrics]
    E --> C
    
    C --> F[Flow Integration<br/>Updated coordination]
    
    style A fill:#ff5722
    style C fill:#4caf50
```

---

## **💔 BROKEN IMPORT CHAIN ANALYSIS**

### **Missing Model Impact**
```mermaid
graph TD
    A[MappingLearningPattern<br/>REMOVED MODEL] --> B[vector_utils_old.py<br/>Import errors]
    A --> C[agent_learning_system.py<br/>Commented imports]
    A --> D[embedding_service.py<br/>Pattern storage broken]
    
    B --> E[VectorUtils Class<br/>Stubbed methods]
    C --> F[Pattern Storage<br/>Disabled functionality]
    D --> G[Learning System<br/>No pattern retention]
    
    E --> H[Field Mapping<br/>No similarity search]
    F --> H
    G --> H
    
    style A fill:#ff5722
    style E fill:#ffeb3b
    style F fill:#ffeb3b
    style G fill:#ffeb3b
    style H fill:#ff9800
```

### **Import Resolution Options**
```mermaid
graph LR
    A[DECISION POINT<br/>Missing Models] --> B[Option 1: Restore Models<br/>Re-enable functionality]
    A --> C[Option 2: Remove References<br/>Simplify architecture]
    
    B --> D[Pros: Full functionality<br/>Cons: Complexity]
    C --> E[Pros: Clean architecture<br/>Cons: Lost features]
    
    B --> F[Requires: Model recreation<br/>Database migration<br/>Vector embedding setup]
    C --> G[Requires: Import cleanup<br/>Stub removal<br/>Test updates]
    
    style A fill:#9c27b0
    style B fill:#4caf50
    style C fill:#2196f3
```

---

## **🔄 API VERSION DEPENDENCIES**

### **API Usage Patterns**
```mermaid
graph TD
    subgraph "Frontend Components"
        FC1[Discovery Flow UI]
        FC2[Field Mapping UI]
        FC3[Asset Inventory UI]
        FC4[Admin Panels]
    end
    
    subgraph "API v1 Endpoints"
        V1_1[/unified-discovery/*]
        V1_2[/data-import/*]
        V1_3[/assets/*]
        V1_4[/admin/*]
    end
    
    subgraph "API v3 Endpoints"
        V3_1[/discovery-flow/*]
        V3_2[/data-import/*]
        V3_3[/field-mapping/*]
        V3_4[/admin/*]
    end
    
    FC1 --> V1_1
    FC1 -.-> V3_1
    FC2 --> V1_2
    FC2 -.-> V3_2
    FC3 --> V1_3
    FC4 --> V1_4
    FC4 -.-> V3_4
    
    style V1_1 fill:#ffeb3b
    style V1_2 fill:#ffeb3b
    style V1_3 fill:#ffeb3b
    style V1_4 fill:#ffeb3b
    style V3_1 fill:#4caf50
    style V3_2 fill:#4caf50
    style V3_3 fill:#4caf50
    style V3_4 fill:#4caf50
```

### **Migration Path**
```mermaid
graph LR
    A[Mixed API Usage<br/>v1 + v3] --> B[Deprecation Warnings<br/>v1 endpoints]
    B --> C[Dual Support Period<br/>Both versions active]
    C --> D[V3 Full Adoption<br/>Frontend migration]
    D --> E[V1 Removal<br/>Legacy cleanup]
    
    style A fill:#ff5722
    style B fill:#ffeb3b
    style C fill:#ff9800
    style D fill:#4caf50
    style E fill:#2196f3
```

---

## **📊 CLEANUP SEQUENCE MATRIX**

### **Safe Operations (No Dependencies)**
```mermaid
graph LR
    A[Documentation Updates] --> B[Comment Cleanup]
    B --> C[Legacy File Removal<br/>*_legacy.py, *_old.py]
    C --> D[Empty Directory Cleanup<br/>/api/v2/]
    D --> E[Test File Updates]
    
    style A fill:#4caf50
    style B fill:#4caf50
    style C fill:#4caf50
    style D fill:#4caf50
    style E fill:#4caf50
```

### **Dependency-Ordered Operations**
```mermaid
graph TD
    A[Database Migration<br/>session_id columns] --> B[Service Layer Updates<br/>session→flow logic]
    B --> C[API Endpoint Updates<br/>Parameter changes]
    C --> D[Frontend Integration<br/>API client updates]
    
    E[Import Chain Repair<br/>Missing models] --> F[Service Restoration<br/>Vector utils, learning]
    F --> G[Feature Re-enabling<br/>Pattern storage]
    
    H[Agent Base Consolidation<br/>Remove old base class] --> I[Agent Conversions<br/>Pseudo→CrewAI]
    I --> J[Flow Integration<br/>Updated coordination]
    
    style A fill:#ff5722
    style E fill:#ff5722
    style H fill:#ff5722
```

---

## **⚠️ RISK ASSESSMENT BY DEPENDENCY**

### **High Risk Dependencies**
| Component | Dependency Risk | Impact | Mitigation |
|-----------|----------------|---------|------------|
| Database Migration | 🔴 Very High | Critical system functions | Full backup + staging test |
| Service Layer Logic | 🔴 High | Active flow executions | Compatibility layer |
| Agent Business Logic | 🔴 High | AI accuracy | Parallel testing |
| API Endpoint Changes | 🟡 Medium | Frontend integration | Deprecation period |

### **Medium Risk Dependencies**
| Component | Dependency Risk | Impact | Mitigation |
|-----------|----------------|---------|------------|
| Import Chain Repair | 🟡 Medium | Feature availability | Graceful degradation |
| Model Removal | 🟡 Medium | Vector search | Alternative implementation |
| Base Class Changes | 🟡 Medium | Agent inheritance | Gradual migration |

### **Low Risk Dependencies**
| Component | Dependency Risk | Impact | Mitigation |
|-----------|----------------|---------|------------|
| Documentation | 🟢 Low | Developer experience | Version control |
| Legacy Files | 🟢 Low | Code maintenance | Automated testing |
| Comments | 🟢 Low | Code clarity | Review process |

---

## **🛠️ IMPLEMENTATION STRATEGY**

### **Phase 1: Foundation (Week 1-2)**
```mermaid
graph LR
    A[Database Backup] --> B[Schema Migration]
    B --> C[Service Compatibility]
    C --> D[Import Repair]
    D --> E[Legacy File Cleanup]
```

### **Phase 2: Core Changes (Week 3-4)**
```mermaid
graph LR
    A[Agent Conversions] --> B[Service Updates]
    B --> C[API Consolidation]
    C --> D[Integration Testing]
```

### **Phase 3: Final Cleanup (Week 5-6)**
```mermaid
graph LR
    A[Documentation Updates] --> B[Performance Testing]
    B --> C[Security Validation]
    C --> D[Production Deployment]
```

---

## **📈 DEPENDENCY VALIDATION**

### **Pre-Change Validation**
```bash
# Dependency analysis commands
find . -name "*.py" -exec grep -l "session_id" {} \;
find . -name "*.py" -exec grep -l "MappingLearningPattern" {} \;
find . -name "*.py" -exec grep -l "BaseDiscoveryAgent" {} \;
```

### **Post-Change Validation**
```bash
# Verification commands
python -m py_compile $(find . -name "*.py")
pytest --import-mode=importlib
python -c "import app; print('All imports successful')"
```

### **Dependency Health Metrics**
- **Import Success Rate**: 100% (no broken imports)
- **Test Pass Rate**: 95%+ (no regression)
- **Service Availability**: 99.9% (no downtime)
- **Performance Baseline**: ±5% (no degradation)

---

## **🔗 CROSS-REFERENCES**

- [Comprehensive Legacy Analysis](./COMPREHENSIVE_LEGACY_ANALYSIS.md) - Main analysis report
- [Session ID Migration Details](./SESSION_ID_MIGRATION.md) - Database and service migration
- [Agent Conversion Plan](./AGENT_CONVERSION_PLAN.md) - Pseudo-agent to CrewAI migration
- [Cleanup Manifest](./CLEANUP_MANIFEST.md) - File-by-file action plan
- [Execution Phases](./EXECUTION_PHASES.md) - Implementation timeline

---

*This dependency analysis ensures safe and systematic legacy code removal while maintaining system stability and functionality.*

**Last Updated:** January 2025  
**Next Review:** After each major dependency change