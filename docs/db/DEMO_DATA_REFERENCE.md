# Demo Data Quick Reference

## Primary Demo Identifiers

### Core IDs (Hardcoded for Demo)
```python
DEMO_CLIENT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"
DEMO_USER_ID = "33333333-3333-3333-3333-333333333333"
ANALYST_USER_ID = "44444444-4444-4444-4444-444444444444"
MANAGER_USER_ID = "55555555-5555-5555-5555-555555555555"
```

### Demo User Accounts
| Email | Password | Role | Purpose |
|-------|----------|------|---------|
| demo@democorp.com | Demo123! | Migration Architect | Primary demo user |
| analyst@democorp.com | Demo123! | Data Analyst | Read/analyze workflows |
| manager@democorp.com | Demo123! | Program Manager | Administrative views |

## Demo Scenarios

### Scenario 1: "Complete Success Story"
- **Flow ID**: `demo-flow-001-complete`
- **Status**: Completed
- **Assets**: 100 fully analyzed
- **Purpose**: Show successful end-to-end flow

### Scenario 2: "In-Progress Analysis"  
- **Flow ID**: `demo-flow-002-progress`
- **Status**: At field mapping stage
- **Assets**: 50 pending approval
- **Purpose**: Demonstrate active workflow

### Scenario 3: "Large Enterprise"
- **Flow ID**: `demo-flow-003-enterprise`
- **Status**: Asset inventory phase
- **Assets**: 500 being processed
- **Purpose**: Show scale capabilities

### Scenario 4: "Error Recovery"
- **Flow ID**: `demo-flow-004-error`
- **Status**: Failed at import
- **Error**: Data validation issues
- **Purpose**: Demonstrate error handling

## Sample Asset Categories

### Applications (150 total)
- 50 Web Applications (Java, .NET, Python)
- 30 Databases (Oracle, SQL Server, PostgreSQL)
- 40 Middleware (WebLogic, JBoss, Tomcat)
- 30 Custom Applications

### Servers (200 total)
- 120 Linux Servers (RHEL, Ubuntu)
- 80 Windows Servers (2016, 2019, 2022)

### Sample Asset Names
```
Web Servers:
- demo-web-prod-01 through demo-web-prod-20
- demo-web-staging-01 through demo-web-staging-10

App Servers:
- demo-app-prod-01 through demo-app-prod-30
- demo-app-dev-01 through demo-app-dev-10

Databases:
- demo-db-oracle-prod-01
- demo-db-mssql-prod-01
- demo-db-postgres-prod-01
```

## Migration Waves

### Wave 1: "Dev/Test Systems" (Month 1-2)
- 50 non-production assets
- Low risk, high learning

### Wave 2: "Stateless Web Tier" (Month 3-4)
- 75 web servers
- Medium complexity

### Wave 3: "Application Tier" (Month 5-6)
- 100 application servers
- Complex dependencies

### Wave 4: "Data Tier" (Month 7-8)
- 50 databases
- High complexity

### Wave 5: "Production Critical" (Month 9-10)
- 25 mission-critical systems
- Extensive planning required

## Sample Field Mappings

### Common CMDB → Platform Mappings
| Source Field | Target Field | Confidence |
|--------------|--------------|------------|
| server_name | hostname | 95% |
| ip_addr | ip_address | 98% |
| operating_sys | operating_system | 92% |
| business_unit | department | 87% |
| tech_contact | technical_owner | 85% |

## Demo Metrics

### Discovery Performance
- Average import time: 45 seconds
- Field mapping accuracy: 89%
- Asset discovery rate: 95%
- Dependency mapping: 78%

### Migration Readiness
- Ready for migration: 65%
- Needs remediation: 25%
- Blocked by dependencies: 10%

## Quick SQL Queries

### Get all demo assets
```sql
SELECT * FROM assets 
WHERE client_account_id = '11111111-1111-1111-1111-111111111111'
ORDER BY created_at DESC;
```

### Check discovery flow status
```sql
SELECT flow_name, status, progress_percentage 
FROM discovery_flows 
WHERE engagement_id = '22222222-2222-2222-2222-222222222222';
```

### View pending field mappings
```sql
SELECT * FROM import_field_mappings 
WHERE status = 'suggested' 
AND client_account_id = '11111111-1111-1111-1111-111111111111';
```

## Testing Checklist

When logged in as demo@democorp.com, verify:

- [ ] Dashboard shows 5 discovery flows
- [ ] Asset inventory displays 500 assets
- [ ] Field mappings has pending approvals
- [ ] Dependency graph renders properly
- [ ] Migration waves show 5 waves
- [ ] Analytics has performance data
- [ ] No empty state messages appear

## Notes

- All timestamps use relative dates (e.g., "3 days ago")
- Performance metrics update daily via scheduled job
- Demo data is isolated via client_account_id
- Safe to reset demo data without affecting other clients