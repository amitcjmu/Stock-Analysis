#!/usr/bin/env python3
"""
Railway Migration Fix Script
Creates missing tables directly using psycopg2 (sync) to avoid asyncpg SSL issues
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_sync_database_url():
    """Convert DATABASE_URL to sync psycopg2 format."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return None
    
    # Convert asyncpg URL to psycopg2 format if needed
    if 'postgresql+asyncpg://' in database_url:
        sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    else:
        sync_url = database_url
    
    return sync_url

def create_missing_table():
    """Create the crewai_flow_state_extensions table if it doesn't exist."""
    
    sync_url = get_sync_database_url()
    if not sync_url:
        return False
    
    try:
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(sync_url)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'crewai_flow_state_extensions'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Table crewai_flow_state_extensions already exists")
            cursor.close()
            conn.close()
            return True
        
        print("🏗️ Creating crewai_flow_state_extensions table...")
        
        # Create the table with all required columns
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS crewai_flow_state_extensions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            flow_id VARCHAR(255) UNIQUE NOT NULL,
            client_account_id UUID,
            engagement_id UUID,
            user_id UUID,
            flow_type VARCHAR(50),
            flow_name VARCHAR(255),
            flow_status VARCHAR(50),
            flow_configuration JSONB,
            flow_persistence_data JSONB,
            agent_collaboration_log JSONB,
            memory_usage_metrics JSONB,
            knowledge_base_analytics JSONB,
            phase_execution_times JSONB,
            agent_performance_metrics JSONB,
            crew_coordination_analytics JSONB,
            learning_patterns JSONB,
            user_feedback_history JSONB,
            adaptation_metrics JSONB,
            phase_transitions JSONB,
            error_history JSONB,
            retry_count INTEGER DEFAULT 0,
            parent_flow_id VARCHAR(255),
            child_flow_ids JSONB,
            flow_metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        print("✅ Table created successfully!")
        
        # Create indexes for performance
        print("🔧 Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_crewai_flow_client_account ON crewai_flow_state_extensions(client_account_id);",
            "CREATE INDEX IF NOT EXISTS idx_crewai_flow_engagement ON crewai_flow_state_extensions(engagement_id);",
            "CREATE INDEX IF NOT EXISTS idx_crewai_flow_user ON crewai_flow_state_extensions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_crewai_flow_type ON crewai_flow_state_extensions(flow_type);",
            "CREATE INDEX IF NOT EXISTS idx_crewai_flow_status ON crewai_flow_state_extensions(flow_status);"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("✅ Indexes created successfully!")
        
        cursor.close()
        conn.close()
        
        print("🎉 Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Railway migration fix...")
    success = create_missing_table()
    
    if success:
        print("✅ Migration fix completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration fix failed!")
        sys.exit(1)