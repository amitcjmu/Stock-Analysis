"""migrate_session_to_flow_id

Migration to replace session_id with flow_id as primary identifier.
This migration must:
1. Add flow_id columns where missing
2. Populate flow_id from existing session data
3. Update foreign key relationships
4. Create indexes for performance
5. Be reversible for safety

Revision ID: migrate_session_to_flow_id
Revises: ce14d7658e0c
Create Date: 2025-06-29 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid

# revision identifiers
revision = 'migrate_session_to_flow_id'
down_revision = 'ce14d7658e0c'
branch_labels = None
depends_on = None


def upgrade():
    """Migrate from session_id to flow_id as primary identifier."""
    
    # Start transaction
    conn = op.get_bind()
    
    print("🚀 Starting session_id to flow_id migration...")
    
    # ========================================
    # STEP 1: Add flow_id columns where missing
    # ========================================
    
    print("📊 Step 1: Adding flow_id columns...")
    
    # Add flow_id to assets table if it doesn't exist
    try:
        op.add_column('assets', sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=True, index=True))
        print("✅ Added flow_id column to assets table")
    except Exception as e:
        print(f"⚠️ flow_id column might already exist in assets: {e}")
    
    # Add flow_id to flow_deletion_audit table if it doesn't exist
    try:
        op.add_column('flow_deletion_audit', sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=True, index=True))
        print("✅ Added flow_id column to flow_deletion_audit table")
    except Exception as e:
        print(f"⚠️ flow_id column might already exist in flow_deletion_audit: {e}")
    
    # ========================================
    # STEP 2: Create mapping from session_id to flow_id
    # ========================================
    
    print("📊 Step 2: Creating session_id to flow_id mapping...")
    
    # Create temporary table to store session to flow mappings
    op.execute(text("""
        CREATE TEMPORARY TABLE session_flow_mapping (
            session_id UUID,
            flow_id UUID,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    # Map existing data_import_sessions to discovery_flows
    # This assumes that data_import_sessions correspond to discovery flows
    mapping_result = conn.execute(text("""
        INSERT INTO session_flow_mapping (session_id, flow_id)
        SELECT 
            dis.id as session_id,
            df.flow_id as flow_id
        FROM data_import_sessions dis
        LEFT JOIN discovery_flows df ON df.import_session_id = dis.id
        WHERE df.flow_id IS NOT NULL
        RETURNING session_id, flow_id
    """))
    
    mapping_count = mapping_result.rowcount
    print(f"✅ Created {mapping_count} session-to-flow mappings from existing data")
    
    # For sessions without corresponding flows, create new flows
    orphaned_sessions = conn.execute(text("""
        SELECT dis.id, dis.client_account_id, dis.engagement_id, dis.session_name, dis.created_by, dis.created_at
        FROM data_import_sessions dis
        LEFT JOIN session_flow_mapping sfm ON sfm.session_id = dis.id
        WHERE sfm.session_id IS NULL
    """)).fetchall()
    
    for session in orphaned_sessions:
        # Generate new flow_id for orphaned sessions
        new_flow_id = str(uuid.uuid4())
        
        # Create corresponding discovery_flow
        conn.execute(text("""
            INSERT INTO discovery_flows (
                id, flow_id, client_account_id, engagement_id, user_id, 
                import_session_id, flow_name, flow_description, status, 
                progress_percentage, crewai_state_data, created_at
            ) VALUES (
                :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                :import_session_id, :flow_name, :flow_description, :status,
                :progress_percentage, :crewai_state_data, :created_at
            )
        """), {
            'id': str(uuid.uuid4()),
            'flow_id': new_flow_id,
            'client_account_id': session.client_account_id,
            'engagement_id': session.engagement_id,
            'user_id': session.created_by,
            'import_session_id': session.id,
            'flow_name': f"Migration Flow: {session.session_name}",
            'flow_description': f"Auto-created during session-to-flow migration",
            'status': 'migrated',
            'progress_percentage': 100.0,
            'crewai_state_data': '{}',
            'created_at': session.created_at
        })
        
        # Add to mapping table
        conn.execute(text("""
            INSERT INTO session_flow_mapping (session_id, flow_id)
            VALUES (:session_id, :flow_id)
        """), {
            'session_id': session.id,
            'flow_id': new_flow_id
        })
    
    orphaned_count = len(orphaned_sessions)
    print(f"✅ Created {orphaned_count} new flows for orphaned sessions")
    
    # ========================================
    # STEP 3: Populate flow_id in assets table
    # ========================================
    
    print("📊 Step 3: Populating flow_id in assets table...")
    
    # Update assets table with flow_id based on session_id
    assets_updated = conn.execute(text("""
        UPDATE assets 
        SET flow_id = sfm.flow_id
        FROM session_flow_mapping sfm
        WHERE assets.session_id = sfm.session_id
          AND assets.flow_id IS NULL
    """)).rowcount
    
    print(f"✅ Updated {assets_updated} asset records with flow_id")
    
    # For assets without session_id, try to map via discovery_flows
    assets_no_session = conn.execute(text("""
        UPDATE assets 
        SET flow_id = df.flow_id
        FROM discovery_flows df
        WHERE assets.client_account_id = df.client_account_id
          AND assets.engagement_id = df.engagement_id
          AND assets.session_id IS NULL
          AND assets.flow_id IS NULL
          AND df.created_at <= assets.created_at
          AND df.created_at = (
              SELECT MAX(df2.created_at)
              FROM discovery_flows df2
              WHERE df2.client_account_id = assets.client_account_id
                AND df2.engagement_id = assets.engagement_id
                AND df2.created_at <= assets.created_at
          )
    """)).rowcount
    
    print(f"✅ Updated {assets_no_session} assets without session_id using discovery_flows")
    
    # ========================================
    # STEP 4: Populate flow_id in flow_deletion_audit table
    # ========================================
    
    print("📊 Step 4: Populating flow_id in flow_deletion_audit table...")
    
    # Update flow_deletion_audit table with flow_id based on session_id
    audit_updated = conn.execute(text("""
        UPDATE flow_deletion_audit 
        SET flow_id = sfm.flow_id
        FROM session_flow_mapping sfm
        WHERE flow_deletion_audit.session_id = sfm.session_id
          AND flow_deletion_audit.flow_id IS NULL
    """)).rowcount
    
    print(f"✅ Updated {audit_updated} audit records with flow_id")
    
    # ========================================
    # STEP 5: Create indexes for performance
    # ========================================
    
    print("📊 Step 5: Creating indexes for performance...")
    
    try:
        op.create_index('idx_assets_flow_id', 'assets', ['flow_id'])
        print("✅ Created index on assets.flow_id")
    except Exception as e:
        print(f"⚠️ Index might already exist: {e}")
    
    try:
        op.create_index('idx_flow_deletion_audit_flow_id', 'flow_deletion_audit', ['flow_id'])
        print("✅ Created index on flow_deletion_audit.flow_id")
    except Exception as e:
        print(f"⚠️ Index might already exist: {e}")
    
    # ========================================
    # STEP 6: Add foreign key constraints
    # ========================================
    
    print("📊 Step 6: Adding foreign key constraints...")
    
    try:
        op.create_foreign_key(
            'fk_assets_flow_id',
            'assets', 'discovery_flows',
            ['flow_id'], ['flow_id'],
            ondelete='CASCADE'
        )
        print("✅ Added foreign key constraint for assets.flow_id")
    except Exception as e:
        print(f"⚠️ Foreign key constraint might already exist: {e}")
    
    try:
        op.create_foreign_key(
            'fk_flow_deletion_audit_flow_id',
            'flow_deletion_audit', 'discovery_flows',
            ['flow_id'], ['flow_id'],
            ondelete='CASCADE'
        )
        print("✅ Added foreign key constraint for flow_deletion_audit.flow_id")
    except Exception as e:
        print(f"⚠️ Foreign key constraint might already exist: {e}")
    
    # ========================================
    # STEP 7: Validation
    # ========================================
    
    print("📊 Step 7: Validating migration...")
    
    # Check for orphaned records
    orphaned_assets = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM assets
        WHERE flow_id IS NULL AND session_id IS NOT NULL
    """)).fetchone().count
    
    if orphaned_assets > 0:
        print(f"⚠️ Warning: {orphaned_assets} assets still have NULL flow_id")
    else:
        print("✅ All assets with session_id now have flow_id")
    
    # Check mapping completeness
    total_sessions = conn.execute(text("SELECT COUNT(*) as count FROM data_import_sessions")).fetchone().count
    total_mappings = conn.execute(text("SELECT COUNT(*) as count FROM session_flow_mapping")).fetchone().count
    
    print(f"📊 Migration Summary:")
    print(f"   - Total sessions: {total_sessions}")
    print(f"   - Total mappings: {total_mappings}")
    print(f"   - Assets updated: {assets_updated + assets_no_session}")
    print(f"   - Audit records updated: {audit_updated}")
    
    print("🎉 Session-to-flow migration completed successfully!")


def downgrade():
    """Rollback the migration."""
    
    print("🔄 Rolling back session_id to flow_id migration...")
    
    # Remove foreign key constraints
    try:
        op.drop_constraint('fk_assets_flow_id', 'assets', type_='foreignkey')
        print("✅ Removed foreign key constraint for assets.flow_id")
    except Exception as e:
        print(f"⚠️ Foreign key constraint might not exist: {e}")
    
    try:
        op.drop_constraint('fk_flow_deletion_audit_flow_id', 'flow_deletion_audit', type_='foreignkey')
        print("✅ Removed foreign key constraint for flow_deletion_audit.flow_id")
    except Exception as e:
        print(f"⚠️ Foreign key constraint might not exist: {e}")
    
    # Remove indexes
    try:
        op.drop_index('idx_assets_flow_id', table_name='assets')
        print("✅ Removed index on assets.flow_id")
    except Exception as e:
        print(f"⚠️ Index might not exist: {e}")
    
    try:
        op.drop_index('idx_flow_deletion_audit_flow_id', table_name='flow_deletion_audit')
        print("✅ Removed index on flow_deletion_audit.flow_id")
    except Exception as e:
        print(f"⚠️ Index might not exist: {e}")
    
    # Remove flow_id columns
    try:
        op.drop_column('assets', 'flow_id')
        print("✅ Removed flow_id column from assets table")
    except Exception as e:
        print(f"⚠️ Column might not exist: {e}")
    
    try:
        op.drop_column('flow_deletion_audit', 'flow_id')
        print("✅ Removed flow_id column from flow_deletion_audit table")
    except Exception as e:
        print(f"⚠️ Column might not exist: {e}")
    
    # Remove auto-created discovery flows
    conn = op.get_bind()
    removed_flows = conn.execute(text("""
        DELETE FROM discovery_flows 
        WHERE status = 'migrated' 
          AND flow_description LIKE '%Auto-created during session-to-flow migration%'
    """)).rowcount
    
    print(f"✅ Removed {removed_flows} auto-created discovery flows")
    print("🔄 Rollback completed successfully!")