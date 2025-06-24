"""fix_crewai_extensions_workflow_to_discovery_flow

Revision ID: 5be554823421
Revises: c547c104e9b1
Create Date: 2025-06-24 02:07:38.093170

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '5be554823421'
down_revision = 'c547c104e9b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get database connection for checking table state
    conn = op.get_bind()
    
    # Check if crewai_flow_state_extensions table exists
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'crewai_flow_state_extensions'
        );
    """)).scalar()
    
    if table_exists:
        # Check if session_id column exists
        session_id_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'crewai_flow_state_extensions' 
                AND column_name = 'session_id'
            );
        """)).scalar()
        
        # Check if discovery_flow_id column exists
        discovery_flow_id_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'crewai_flow_state_extensions' 
                AND column_name = 'discovery_flow_id'
            );
        """)).scalar()
        
        # Only proceed with column changes if we have session_id but not discovery_flow_id
        if session_id_exists and not discovery_flow_id_exists:
            print("🔄 Migrating CrewAI Flow State Extensions from workflow_states to discovery_flows...")
            
            # Step 1: Drop any existing foreign key constraints on session_id
            try:
                # Find foreign key constraints on session_id
                fk_result = conn.execute(text("""
                    SELECT tc.constraint_name 
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = 'crewai_flow_state_extensions' 
                    AND tc.constraint_type = 'FOREIGN KEY'
                    AND kcu.column_name = 'session_id'
                """)).fetchall()
                
                for constraint in fk_result:
                    print(f"🗑️ Dropping foreign key constraint: {constraint[0]}")
                    op.drop_constraint(constraint[0], 'crewai_flow_state_extensions', type_='foreignkey')
            except Exception as e:
                print(f"⚠️ No foreign key constraints to drop: {e}")
            
            # Step 2: Add discovery_flow_id column (nullable initially)
            print("➕ Adding discovery_flow_id column...")
            op.add_column('crewai_flow_state_extensions', 
                         sa.Column('discovery_flow_id', sa.UUID(), nullable=True))
            
            # Step 3: Create index for discovery_flow_id
            print("📊 Creating index for discovery_flow_id...")
            op.create_index(op.f('ix_crewai_flow_state_extensions_discovery_flow_id'), 
                           'crewai_flow_state_extensions', ['discovery_flow_id'], unique=False)
            
            # Step 4: Create foreign key to discovery_flows
            print("🔗 Creating foreign key to discovery_flows...")
            op.create_foreign_key(None, 'crewai_flow_state_extensions', 'discovery_flows', 
                                 ['discovery_flow_id'], ['id'], ondelete='CASCADE')
            
            # Step 5: Drop the old session_id column
            print("🗑️ Dropping session_id column...")
            op.drop_column('crewai_flow_state_extensions', 'session_id')
            
            print("✅ CrewAI Flow State Extensions migration completed!")
        else:
            if not session_id_exists:
                print("ℹ️ session_id column doesn't exist, skipping migration")
            if discovery_flow_id_exists:
                print("ℹ️ discovery_flow_id column already exists, skipping migration")
    else:
        print("ℹ️ crewai_flow_state_extensions table doesn't exist, skipping migration")
    
    # Apply discovery_flows table improvements
    print("🔧 Applying discovery_flows table improvements...")
    
    # Create indexes for discovery_assets
    try:
        op.create_index(op.f('ix_discovery_assets_id'), 'discovery_assets', ['id'], unique=False)
        print("✅ Created ix_discovery_assets_id index")
    except Exception as e:
        print(f"ℹ️ ix_discovery_assets_id index already exists: {e}")
    
    # Fix discovery_flows indexes
    try:
        # Drop old unique constraint if it exists
        op.drop_constraint('discovery_flows_flow_id_key', 'discovery_flows', type_='unique')
        print("✅ Dropped discovery_flows_flow_id_key constraint")
    except Exception as e:
        print(f"ℹ️ discovery_flows_flow_id_key constraint doesn't exist: {e}")
    
    try:
        # Drop old index if it exists
        op.drop_index('ix_discovery_flows_flow_id', table_name='discovery_flows')
        print("✅ Dropped old ix_discovery_flows_flow_id index")
    except Exception as e:
        print(f"ℹ️ Old ix_discovery_flows_flow_id index doesn't exist: {e}")
    
    # Create new indexes
    indexes_to_create = [
        ('ix_discovery_flows_flow_id', ['flow_id'], True),
        ('ix_discovery_flows_data_import_id', ['data_import_id'], False),
        ('ix_discovery_flows_id', ['id'], False),
        ('ix_discovery_flows_import_session_id', ['import_session_id'], False)
    ]
    
    for index_name, columns, unique in indexes_to_create:
        try:
            op.create_index(op.f(index_name), 'discovery_flows', columns, unique=unique)
            print(f"✅ Created {index_name} index")
        except Exception as e:
            print(f"ℹ️ {index_name} index already exists: {e}")
    
    print("🎉 Migration completed successfully!")


def downgrade() -> None:
    print("⬇️ Downgrading CrewAI Flow State Extensions migration...")
    
    # Reverse the discovery_flows changes
    indexes_to_drop = [
        'ix_discovery_flows_import_session_id',
        'ix_discovery_flows_id', 
        'ix_discovery_flows_data_import_id',
        'ix_discovery_flows_flow_id',
        'ix_discovery_assets_id'
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(op.f(index_name), table_name='discovery_flows' if 'discovery_flows' in index_name else 'discovery_assets')
            print(f"✅ Dropped {index_name} index")
        except Exception as e:
            print(f"ℹ️ {index_name} index doesn't exist: {e}")
    
    # Recreate old discovery_flows constraints
    try:
        op.create_index(op.f('ix_discovery_flows_flow_id'), 'discovery_flows', ['flow_id'], unique=False)
        op.create_unique_constraint('discovery_flows_flow_id_key', 'discovery_flows', ['flow_id'])
        print("✅ Recreated old discovery_flows constraints")
    except Exception as e:
        print(f"ℹ️ Could not recreate old constraints: {e}")
    
    # Reverse the CrewAI Flow State Extensions changes
    conn = op.get_bind()
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'crewai_flow_state_extensions'
        );
    """)).scalar()
    
    if table_exists:
        discovery_flow_id_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'crewai_flow_state_extensions' 
                AND column_name = 'discovery_flow_id'
            );
        """)).scalar()
        
        if discovery_flow_id_exists:
            print("🔄 Reverting CrewAI Flow State Extensions to workflow_states...")
            
            # Add session_id column back
            try:
                op.add_column('crewai_flow_state_extensions', 
                             sa.Column('session_id', sa.UUID(), nullable=True))
                print("✅ Added session_id column back")
            except Exception as e:
                print(f"ℹ️ session_id column already exists: {e}")
            
            # Drop discovery_flow_id foreign key and index
            try:
                # Find and drop foreign key constraints on discovery_flow_id
                fk_result = conn.execute(text("""
                    SELECT tc.constraint_name 
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = 'crewai_flow_state_extensions' 
                    AND tc.constraint_type = 'FOREIGN KEY'
                    AND kcu.column_name = 'discovery_flow_id'
                """)).fetchall()
                
                for constraint in fk_result:
                    op.drop_constraint(constraint[0], 'crewai_flow_state_extensions', type_='foreignkey')
                    print(f"✅ Dropped foreign key constraint: {constraint[0]}")
            except Exception as e:
                print(f"ℹ️ No foreign key constraints to drop: {e}")
            
            try:
                op.drop_index(op.f('ix_crewai_flow_state_extensions_discovery_flow_id'), 
                             table_name='crewai_flow_state_extensions')
                print("✅ Dropped discovery_flow_id index")
            except Exception as e:
                print(f"ℹ️ discovery_flow_id index doesn't exist: {e}")
            
            try:
                op.drop_column('crewai_flow_state_extensions', 'discovery_flow_id')
                print("✅ Dropped discovery_flow_id column")
            except Exception as e:
                print(f"ℹ️ discovery_flow_id column doesn't exist: {e}")
    
    print("⬇️ Downgrade completed!") 