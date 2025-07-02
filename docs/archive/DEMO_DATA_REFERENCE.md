# Demo Data Quick Reference

## Primary Demo Identifiers

### Core IDs (Hardcoded for Demo)
```python
DEMO_CLIENT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"
DEMO_USER_ID = "33333333-3333-3333-3333-333333333333"  # demo@democorp.com
ANALYST_USER_ID = "44444444-4444-4444-4444-444444444444"  # analyst@democorp.com
VIEWER_USER_ID = "55555555-5555-5555-5555-555555555555"  # viewer@democorp.com
CLIENT_ADMIN_USER_ID = "66666666-6666-6666-6666-666666666666"  # client.admin@democorp.com
```

### Demo User Accounts
| Email | Password | RBAC Role | Access Level | Purpose |
|-------|----------|-----------|--------------|---------|
| demo@democorp.com | Demo123! | ENGAGEMENT_MANAGER | READ_WRITE | Primary demo user - manages engagements |
| analyst@democorp.com | Demo123! | ANALYST | READ_WRITE | Data analysis and reporting |
| viewer@democorp.com | Demo123! | VIEWER | READ_ONLY | Read-only access to view data |
| client.admin@democorp.com | Demo123! | CLIENT_ADMIN | ADMIN | Client-level administration |

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

### Applications (10 total)
- 3 Web Applications (1 Java, 1 .NET, 1 Python)
- 4 Business Applications (ERP, CRM, HR, Finance)
- 3 Custom Applications

### Servers (35 total)
- 20 Linux Servers (12 RHEL, 8 Ubuntu)
- 15 Windows Servers (5 Win 2016, 7 Win 2019, 3 Win 2022)

### Databases (10 total)
- 4 Oracle (Production)
- 3 SQL Server (Mixed environments)
- 3 PostgreSQL (Development)

### Sample Asset Names
```
Web/App Servers:
- demo-web-prod-01 through demo-web-prod-05
- demo-app-prod-01 through demo-app-prod-10
- demo-app-dev-01 through demo-app-dev-05

Database Servers:
- demo-db-oracle-prod-01 through demo-db-oracle-prod-04
- demo-db-mssql-prod-01 through demo-db-mssql-prod-03
- demo-db-postgres-dev-01 through demo-db-postgres-dev-03

Applications:
- CustomerPortal (Java web app)
- FinanceSystem (.NET app)
- HRManagement (Python web app)
- InventoryERP (Legacy)
```

## Migration Waves

### Wave 1: "Dev/Test Systems" (Month 1-2)
- 8 development servers
- 3 test databases
- Low risk, high learning

### Wave 2: "Non-Critical Apps" (Month 3-4)
- 5 internal applications
- 10 application servers
- Medium complexity

### Wave 3: "Customer-Facing Apps" (Month 5-6)
- 3 web applications
- 12 production servers
- Complex dependencies

### Wave 4: "Core Business Systems" (Month 7-8)
- 2 critical applications (ERP, CRM)
- 7 database servers
- 5 app servers
- High complexity

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
- [ ] Asset inventory displays 60 assets total
- [ ] Field mappings has pending approvals
- [ ] Dependency graph renders properly with connections
- [ ] Migration waves show 4 waves with proper asset distribution
- [ ] Analytics has performance data
- [ ] No empty state messages appear
- [ ] Asset breakdown shows: 10 apps, 35 servers, 10 databases, 5 network devices

## Notes

- All timestamps use relative dates (e.g., "3 days ago")
- Performance metrics update daily via scheduled job
- Demo data is isolated via client_account_id
- Safe to reset demo data without affecting other clients