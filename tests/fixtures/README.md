# Test Fixtures

## test-cmdb-data.csv

Sample CMDB data for testing collection and discovery flows.

**Format**: CSV with headers

**Required Columns**:
- `application_name` - Application name
- `environment` - Environment (prod/staging/dev)
- `server_name` - Server hostname
- `ip_address` - Server IP address
- `owner` - Application owner

**Example**:
```csv
application_name,environment,server_name,ip_address,owner
CRM System,production,crm-prod-01,10.0.1.10,john@example.com
```

**Location**: `tests/fixtures/test-cmdb-data.csv`
