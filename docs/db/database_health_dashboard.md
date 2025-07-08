# 🏥 Database Health Dashboard

## Overview

This dashboard provides a real-time view of database health metrics and remediation progress for the AI Force Migration Platform.

## 📊 Current Health Status

### **Overall Database Health: 85.2%** ⚠️

| Category | Status | Score | Issues |
|----------|--------|-------|--------|
| Multi-Tenant Isolation | ✅ Excellent | 100% | 0 |
| Foreign Key Integrity | ✅ Good | 92.3% | 13 orphaned records |
| Master Flow Linkage | ⚠️ Needs Attention | 73.7% | 220 unlinked records |
| Data Quality | ✅ Good | 96.8% | Minor inconsistencies |
| Performance | ✅ Good | 94.1% | Within thresholds |

## 🚨 Critical Issues Summary

### **High Priority (Fix within 24 hours)**
- **11 orphaned discovery flows** with invalid `master_flow_id` references
- **Impact**: Flow management failures, deletion errors
- **Estimated Fix Time**: 4-6 hours

### **Medium Priority (Fix within 1 week)**
- **29 assets** without master flow linkage
- **2 discovery flows** without master flow association
- **Impact**: Reduced traceability and audit capabilities
- **Estimated Fix Time**: 6-8 hours

### **Low Priority (Fix within 1 month)**
- **178 field mappings** without master flow linkage
- **Impact**: Limited metadata tracking
- **Estimated Fix Time**: 2-3 hours

## 📈 Progress Tracking

### **Remediation Phases**

| Phase | Status | Completion | Target Date |
|-------|--------|------------|-------------|
| Phase 1: Discovery Flow Fixes | ✅ Complete | 100% | 2025-01-07 |
| Phase 2: Asset Linkage | 🔄 In Progress | 0% | 2025-01-09 |
| Phase 3: Field Mapping Linkage | ⏳ Pending | 0% | 2025-01-15 |
| Phase 4: Constraint Enforcement | ⏳ Pending | 0% | 2025-01-20 |

### **Success Metrics**

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Orphaned Discovery Flows | 11 | 0 | 🔴 |
| Unlinked Assets | 29 | 0 | 🟡 |
| Foreign Key Violations | 13 | 0 | 🟡 |
| Master Flow Coverage | 73.7% | 100% | 🟡 |

## 🔍 Table-by-Table Health

### **Core Tables Status**

| Table | Records | Health | Issues | Action Required |
|-------|---------|--------|--------|-----------------|
| `crewai_flow_state_extensions` | 20 | ✅ 100% | None | None |
| `discovery_flows` | 13 | ⚠️ 84.6% | 2 unlinked | Link to master flows |
| `data_imports` | 16 | ✅ 100% | None | None |
| `raw_import_records` | 265 | ✅ 100% | None | None |
| `assets` | 29 | ⚠️ 0% | 29 unlinked | Link to master flows |
| `import_field_mappings` | 178 | ⚠️ 0% | 178 unlinked | Link to master flows |

### **Supporting Tables Status**

| Table | Records | Health | Issues | Action Required |
|-------|---------|--------|--------|-----------------|
| `client_accounts` | 2 | ✅ 100% | None | None |
| `engagements` | 2 | ✅ 100% | None | None |
| `users` | 3 | ✅ 100% | None | None |
| `user_profiles` | 3 | ✅ 100% | None | None |

## 🛠️ Quick Actions

### **Run Health Check**
```bash
# Quick database health validation
docker exec migration_backend python scripts/validate_flow_relationships.py

# Detailed table analysis
docker exec migration_backend python -c "
import asyncio
from scripts.database_health_checker import run_complete_health_check
asyncio.run(run_complete_health_check())
"
```

### **Fix Critical Issues**
```bash
# Fix orphaned discovery flows (HIGH PRIORITY)
docker exec migration_backend python scripts/fix_orphaned_discovery_flows.py

# Link assets to master flows (MEDIUM PRIORITY)
docker exec migration_backend python scripts/link_assets_to_flows.py

# Link field mappings to master flows (LOW PRIORITY)
docker exec migration_backend python scripts/link_field_mappings_to_flows.py
```

## 📋 Daily Checklist

### **Morning Health Check (5 minutes)**
- [ ] Run database health validation
- [ ] Check for new orphaned records
- [ ] Verify master flow linkage coverage
- [ ] Review foreign key violations

### **Weekly Deep Dive (30 minutes)**
- [ ] Full table-by-table analysis
- [ ] Performance metrics review
- [ ] Multi-tenant isolation verification
- [ ] Update remediation progress

### **Monthly Audit (2 hours)**
- [ ] Complete database schema review
- [ ] Constraint effectiveness analysis
- [ ] Performance optimization opportunities
- [ ] Update monitoring queries

## 🎯 Success Criteria

### **Phase 1 Complete When:**
- ✅ 0 orphaned discovery flows
- ✅ 0 foreign key violations
- ✅ 100% master flow coverage for core tables

### **Phase 2 Complete When:**
- ✅ All assets linked to master flows
- ✅ All discovery flows have master flow association
- ✅ 95%+ database health score

### **Phase 3 Complete When:**
- ✅ All field mappings linked to master flows
- ✅ Database constraints enforced
- ✅ Automated monitoring in place

## 🔗 Related Documentation

- [Complete Database Audit Report](./complete_database_audit_report.md)
- [Database Validation Scripts](./database_validation_scripts.md)
- [Discovery Flow Data Architecture Analysis](../architecture/discovery-flow-data-architecture-analysis.md)
- [Discovery Flow Data Integrity Fix Plan](../architecture/discovery-flow-data-integrity-fix-plan.md)

---

**Last Updated**: January 7, 2025  
**Next Review**: January 9, 2025  
**Responsible Team**: Database Architecture Team