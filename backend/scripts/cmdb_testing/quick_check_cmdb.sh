#!/bin/bash
# Quick CMDB data checker
# Usage: ./quick_check_cmdb.sh <flow_id>

FLOW_ID=$1

if [ -z "$FLOW_ID" ]; then
    echo "Usage: ./quick_check_cmdb.sh <flow_id>"
    exit 1
fi

echo "Checking CMDB data for flow: $FLOW_ID"
echo ""

docker exec migration_postgres psql -U postgres -d migration_db <<EOF
\echo '=== Assets Count ==='
SELECT COUNT(*) as total_assets FROM migration.assets WHERE discovery_flow_id = '$FLOW_ID';

\echo ''
\echo '=== CMDB Fields Population ==='
SELECT
    COUNT(*) as total,
    COUNT(business_unit) as has_business_unit,
    COUNT(vendor) as has_vendor,
    COUNT(lifecycle) as has_lifecycle,
    COUNT(hosting_model) as has_hosting,
    COUNT(pii_flag) as has_pii,
    COUNT(risk_level) as has_risk,
    COUNT(tshirt_size) as has_tshirt
FROM migration.assets
WHERE discovery_flow_id = '$FLOW_ID';

\echo ''
\echo '=== Child Tables Count ==='
SELECT
    (SELECT COUNT(*) FROM migration.asset_eol_assessments ae
     JOIN migration.assets a ON ae.asset_id = a.id
     WHERE a.discovery_flow_id = '$FLOW_ID') as eol_records,
    (SELECT COUNT(*) FROM migration.asset_contacts ac
     JOIN migration.assets a ON ac.asset_id = a.id
     WHERE a.discovery_flow_id = '$FLOW_ID') as contact_records;

\echo ''
\echo '=== Sample Asset (First One) ==='
SELECT
    name, business_unit, vendor, lifecycle, hosting_model,
    risk_level, tshirt_size, pii_flag
FROM migration.assets
WHERE discovery_flow_id = '$FLOW_ID'
LIMIT 1;
EOF
