#!/bin/bash

# Production Migration Fix Script
# This script checks and fixes missing Alembic migrations in production
# Created: 2025-09-03
# Issue: field_type column missing in import_field_mappings table

set -e

echo "🔍 Production Database Migration Check and Fix Script"
echo "====================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📋 Expected migrations (in order):"
echo "-----------------------------------"
cat << EOF
001_comprehensive_initial_schema
002_add_security_audit_tables
003_add_collection_flow_tables
004_add_platform_credentials_tables
005_add_gap_analysis_and_questionnaire_tables
006_add_collection_flow_next_phase
007_add_missing_collection_flow_columns
008_update_flow_type_constraint
009_add_collection_flow_id_to_questionnaires
010_add_timestamp_columns_to_collected_data_inventory
011_add_updated_at_to_collection_data_gaps
012_agent_observability_enhancement
013_fix_agent_task_history_foreign_keys
014_fix_remaining_agent_foreign_keys
015_add_asset_dependencies_table
016_add_security_constraints
017a_add_asset_id_to_questionnaire_responses
018_add_agent_execution_history
018b_fix_long_constraint_names
019_implement_row_level_security
020_merge_heads
021_fix_import_field_mappings_id_default
022_add_is_admin_to_users
023_fix_data_imports_foreign_key_constraint
024_add_cache_metadata_tables
025_migrate_8r_to_5r_strategies
026_add_assessment_readiness_fields_to_assets
027_add_indexes_and_failure_journal
028_add_updated_at_trigger_for_failure_journal
029_complete_assessment_flows_schema
030_add_sixr_analysis_tables
031_add_flow_deletion_audit_table
032_add_master_flow_id_to_assessment_flows
033_merge_all_heads
034_add_client_account_id_to_engagement_standards
035_fix_engagement_architecture_standards_schema
036_rename_metadata_columns
036b_fix_null_master_flow_ids
037_add_missing_audit_log_columns
038_add_agent_pattern_learning_columns
039_create_pattern_type_enum
040_add_missing_field_mapping_columns  <-- CRITICAL: Adds field_type column
041_add_hybrid_properties
042_add_vector_search_to_agent_patterns
043_merge_migration_heads
044_merge_036_and_questionnaire_asset_heads
045_merge_cache_and_platform_admin
046_fix_application_name_variants_timestamps
047_add_confidence_score_to_assets
048_add_technical_details_to_assets
049_add_collection_flow_applications_table
050_add_canonical_application_identity
051_migrate_existing_collection_applications
052_optimize_application_indexes
EOF

echo ""
echo "🚀 To check production database status on Railway:"
echo "---------------------------------------------------"
echo ""
echo -e "${YELLOW}1. Connect to Railway production database:${NC}"
echo "   railway run --service backend bash"
echo ""
echo -e "${YELLOW}2. Check current migration version:${NC}"
echo "   cd backend && python -m alembic current"
echo ""
echo -e "${YELLOW}3. Check if specific columns exist:${NC}"
cat << 'EOF'
   python -c "
from app.core.database import engine
import sqlalchemy as sa
from sqlalchemy import inspect

def check_columns():
    with engine.connect() as conn:
        inspector = inspect(conn)
        columns = inspector.get_columns('import_field_mappings', schema='migration')
        column_names = [col['name'] for col in columns]

        print('Current columns in import_field_mappings:')
        for col in column_names:
            print(f'  - {col}')

        missing = []
        if 'field_type' not in column_names:
            missing.append('field_type')
        if 'agent_reasoning' not in column_names:
            missing.append('agent_reasoning')

        if missing:
            print(f'\n❌ Missing columns: {missing}')
        else:
            print('\n✅ All required columns present')

check_columns()
"
EOF

echo ""
echo -e "${YELLOW}4. To apply missing migrations (if needed):${NC}"
echo "   cd backend && python -m alembic upgrade head"
echo ""
echo -e "${YELLOW}5. To apply a specific migration:${NC}"
echo "   cd backend && python -m alembic upgrade 040_add_missing_field_mapping_columns"
echo ""

echo "⚠️  IMPORTANT NOTES:"
echo "-------------------"
echo "• Always backup the production database before running migrations"
echo "• Run migrations during a maintenance window"
echo "• Test the migration rollback procedure first"
echo "• Monitor application logs after migration"
echo ""

echo "🔧 Quick Fix Commands for Railway:"
echo "----------------------------------"
echo ""
echo "If migration 040 is missing, run these commands in Railway shell:"
echo ""
cat << 'EOF'
# Option 1: Apply all missing migrations
railway run --service backend -- bash -c "cd backend && python -m alembic upgrade head"

# Option 2: Apply only the missing columns migration
railway run --service backend -- bash -c "cd backend && python -m alembic upgrade 040_add_missing_field_mapping_columns"

# Option 3: Manual column addition (EMERGENCY ONLY - if migrations are broken)
railway run --service backend -- python -c "
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check if columns exist first
    result = conn.execute(text('''
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'import_field_mappings'
        AND column_name IN ('field_type', 'agent_reasoning')
    '''))
    existing = [row[0] for row in result]

    if 'field_type' not in existing:
        conn.execute(text('''
            ALTER TABLE migration.import_field_mappings
            ADD COLUMN field_type VARCHAR(50)
        '''))
        print('✅ Added field_type column')

    if 'agent_reasoning' not in existing:
        conn.execute(text('''
            ALTER TABLE migration.import_field_mappings
            ADD COLUMN agent_reasoning TEXT
        '''))
        print('✅ Added agent_reasoning column')

    conn.commit()
"
EOF

echo ""
echo "📝 After fixing, verify the application works:"
echo "----------------------------------------------"
echo "1. Check the application logs for errors"
echo "2. Test the affected endpoints"
echo "3. Monitor for any new database errors"
echo ""

echo "✅ Script complete. Follow the steps above to fix production."
