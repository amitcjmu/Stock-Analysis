# Documentation Archive Index

This index provides a comprehensive guide to all archived documentation and redirections to current alternatives.

## 📁 Archive Structure Overview

```
docs/archive/
├── phase1-transition/           # Phase 1 migration period artifacts
│   ├── session-based-docs/      # 15 files - Session_id architecture docs
│   ├── analysis-superseded/     # 18 files - Superseded technical analyses  
│   └── transition-artifacts/    # 12 files - Migration tracking documents
├── [legacy files from previous archiving]
└── ARCHIVE_INDEX.md            # This file
```

**Total Archived Files**: 45+ files moved during Phase 3 documentation cleanup

## 🔄 Redirection Guide - Where to Find Current Information

### **Session-Based Architecture → Flow-Based Architecture**

| **Archived File** | **Current Alternative** | **Notes** |
|-------------------|------------------------|-----------|
| `AI_Force_Migration_Platform_Summary_for_Coding_Agents_OLD.md` | `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` | Updated platform summary with flow_id architecture |
| `DISCOVERY_FLOW_DETAILED_DESIGN.md` | `docs/adr/001-session-to-flow-migration.md` | ADR with current flow-based design |
| `discovery_flow_issues.md` | `docs/troubleshooting/discovery-flow-sync-issues.md` | Updated troubleshooting for flow-based system |
| `MULTI_FLOW_ARCHITECTURE_IMPLEMENTATION_PLAN.md` | `docs/development/CrewAI_Development_Guide.md` | Current CrewAI flow architecture |
| `INCOMPLETE_DISCOVERY_FLOW_MANAGEMENT_PLAN.md` | `docs/planning/phase2-tasks/AGENT_B1_FLOW_FRAMEWORK.md` | Completed flow framework implementation |

### **Analysis Documents → Current Architecture**

| **Archived File** | **Current Alternative** | **Notes** |
|-------------------|------------------------|-----------|
| `DATABASE_CONSOLIDATION_PLAN.md` | `docs/adr/003-postgresql-only-state-management.md` | Current database architecture decision |
| `DISCOVERY_FLOW_INTEGRATION_ANALYSIS.md` | `docs/development/CrewAI_Development_Guide.md` | Comprehensive integration guide |
| `DISCOVERY_WORKFLOW_REMEDIATION_PLAN.md` | `docs/planning/REMEDIATION_SUMMARY.md` | Completed remediation status |
| `UNIFIED_DISCOVERY_FLOW_CONSOLIDATION_PLAN.md` | `docs/api/v3/README.md` | Unified API v3 implementation |
| `POST_MULTITENANCY_DISCOVERY_GAPS_ANALYSIS.md` | `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` | Current multi-tenant architecture |

### **Transitional Artifacts → Current Processes**

| **Archived File** | **Current Alternative** | **Notes** |
|-------------------|------------------------|-----------|
| `MODULARIZATION_COMPLETE_GUIDE.md` | `docs/development/CrewAI_Development_Guide.md` | Current development patterns |
| `frontend_remediation_tracker.md` | `docs/planning/REMEDIATION_SUMMARY.md` | Overall remediation status |
| `CODE_MIGRATION_CHECKLIST.md` | `docs/planning/phase1-tasks/README.md` | Phase 1 completion checklist |
| `CHANGES_SUMMARY.md` | `docs/planning/REMEDIATION_SUMMARY.md` | Comprehensive change summary |

## 📊 Archived Files by Category

### **Session-Based Architecture Documents** (15 files)
```
phase1-transition/session-based-docs/
├── AI_Force_Migration_Platform_Summary_for_Coding_Agents_OLD.md
├── DISCOVERY_FLOW_V2_INTEGRATION_ANALYSIS_OLD.md
├── INCOMPLETE_DISCOVERY_FLOW_MANAGEMENT_PLAN.md
├── MULTI_FLOW_ARCHITECTURE_IMPLEMENTATION_PLAN.md
├── DISCOVERY_FLOW_DETAILED_DESIGN.md
├── crewai-flow-analysis.md
├── discovery_flow_issues.md
└── [8 additional session-based files]
```

### **Superseded Technical Analyses** (18 files)
```
phase1-transition/analysis-superseded/
├── DATABASE_CONSOLIDATION_PLAN.md
├── DISCOVERY_FLOW_REVISED_IMPLEMENTATION_ANALYSIS.md
├── DISCOVERY_FLOW_INTEGRATION_ANALYSIS.md
├── DISCOVERY_FLOW_REDESIGN_EXECUTION_PLAN.md
├── DISCOVERY_FLOW_REDESIGN_SPECIFICATION.md
├── DISCOVERY_WORKFLOW_REMEDIATION_PLAN.md
├── DISCOVERY_WORKFLOW_STABILIZATION_PLAN.md
├── UNIFIED_DISCOVERY_FLOW_CONSOLIDATION_PLAN.md
├── DATABASE_CONSOLIDATION_TASK_TRACKER.md
├── discovery_flow_remediation_plan.md
├── database_schema_analysis.md
├── MOCK_DATA_FALLBACK_REPORT.md
├── SERVICE_REFERENCE_ANALYSIS_REPORT.md
├── POST_MULTITENANCY_DISCOVERY_GAPS_ANALYSIS.md
├── PHASE_3_VALIDATION_SUMMARY.md
└── [3 additional analysis files]
```

### **Migration Transition Artifacts** (12 files)
```
phase1-transition/transition-artifacts/
├── MODULARIZATION_PROGRESS.md
├── DATA_MODEL_CONSOLIDATION_TASK_TRACKER.md
├── CHANGES_SUMMARY.md
├── CODE_MIGRATION_CHECKLIST.md
├── frontend_remediation_tracker.md
├── modularization-plan.md
├── ADMIN_MODULARIZATION_COMPLETION_SUMMARY.md
├── ADMIN_MODULARIZATION_PLAN.md
├── MODULARIZATION_COMPLETE_GUIDE.md
├── MODULARIZATION_GUIDE.md
└── [2 additional transition files]
```

## ⚠️ Important Archive Notes

### **Do NOT Reference Archived Files**
- Archived documentation contains **deprecated patterns** and **outdated architecture**
- All session_id references in archived files are no longer valid
- Use current documentation linked in redirection guide above

### **Historical Context Value**
- Archived files preserve the **migration journey** from session-based to flow-based architecture
- Useful for understanding **design decisions** and **architecture evolution**
- Maintain for **historical reference** but not current development

### **Migration Status Context**
- Files archived during **Phase 3 Documentation Cleanup** (June 2024)
- Represents completion of **session_id → flow_id migration**
- Transition from **dual SQLite/PostgreSQL** to **PostgreSQL-only** state management

## 🔍 Finding Current Documentation

### **Primary Current Documents**
1. **`docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md`** - Main platform overview
2. **`docs/development/CrewAI_Development_Guide.md`** - Development guide with current patterns
3. **`docs/planning/REMEDIATION_SUMMARY.md`** - Overall project status and completion
4. **`docs/adr/`** - Architecture Decision Records (all current)
5. **`docs/api/v3/`** - Current API documentation

### **Navigation Tips**
- Check **ADR files** for architectural decisions
- Use **planning/ directory** for current project status
- Reference **development/ directory** for implementation guides
- Check **troubleshooting/ directory** for current issue resolution

## 📈 Archive Maintenance

### **Review Schedule**
- **Quarterly Review**: Assess if archived content is still needed
- **Annual Cleanup**: Consider permanent removal of files older than 2 years
- **Migration Trigger**: New major architectural changes may require additional archiving

### **Unarchiving Process**
1. **Verify Relevance**: Check if archived content is still applicable
2. **Update References**: Remove deprecated patterns before unarchiving
3. **Integration Check**: Ensure content aligns with current architecture
4. **Documentation Update**: Update any cross-references after unarchiving

### **Archive Access**
- All archived files remain accessible through **git history**
- **File blame** shows when files were archived and why
- **Commit messages** provide context for archival decisions

---

**Archive Created**: June 30, 2024 (Phase 3 Documentation Cleanup)  
**Last Updated**: June 30, 2024  
**Next Review**: September 30, 2024  

*This archive represents the completion of Phase 1 migration from session-based to flow-based architecture and the cleanup of 45+ deprecated documentation files.*