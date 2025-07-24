#!/usr/bin/env python3
"""
Migration script to update learning pattern tables for Week 2 implementation.
Updates vector dimensions and creates missing tables with proper schema.
"""

import asyncio
import sys

# Add the backend directory to the path
sys.path.append("/app")

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def update_learning_tables():
    """Update learning pattern tables to match new schema."""
    print("🔧 Updating Learning Pattern Tables")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        try:
            # 1. Update asset_classification_patterns vector dimensions from 1536 to 1024
            print("\n📝 Updating asset_classification_patterns vector dimensions...")

            # Drop existing vector columns and recreate with correct dimensions
            await session.execute(
                text(
                    """
                ALTER TABLE migration.asset_classification_patterns 
                DROP COLUMN IF EXISTS asset_name_embedding CASCADE;
            """
                )
            )

            await session.execute(
                text(
                    """
                ALTER TABLE migration.asset_classification_patterns 
                DROP COLUMN IF EXISTS metadata_embedding CASCADE;
            """
                )
            )

            # Add new vector columns with 1024 dimensions
            await session.execute(
                text(
                    """
                ALTER TABLE migration.asset_classification_patterns 
                ADD COLUMN asset_name_embedding vector(1024);
            """
                )
            )

            await session.execute(
                text(
                    """
                ALTER TABLE migration.asset_classification_patterns 
                ADD COLUMN metadata_embedding vector(1024);
            """
                )
            )

            print("✅ Updated asset_classification_patterns vector dimensions to 1024")

            # 2. Backup existing mapping_learning_patterns table
            print("\n📝 Backing up existing mapping_learning_patterns table...")

            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS migration.mapping_learning_patterns_backup AS 
                SELECT * FROM migration.mapping_learning_patterns;
            """
                )
            )

            print("✅ Backed up existing mapping_learning_patterns table")

            # 3. Drop existing mapping_learning_patterns table
            print("\n📝 Dropping old mapping_learning_patterns table...")

            await session.execute(
                text(
                    """
                DROP TABLE IF EXISTS migration.mapping_learning_patterns CASCADE;
            """
                )
            )

            print("✅ Dropped old mapping_learning_patterns table")

            # 4. Create new mapping_learning_patterns table with vector support
            print("\n📝 Creating new mapping_learning_patterns table...")

            await session.execute(
                text(
                    """
                CREATE TABLE migration.mapping_learning_patterns (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id VARCHAR(255) NOT NULL,
                    engagement_id VARCHAR(255),
                    
                    -- Source field information
                    source_field_name VARCHAR(255) NOT NULL,
                    source_field_embedding vector(1024) NOT NULL,
                    source_sample_values JSONB,
                    source_sample_embedding vector(1024),
                    
                    -- Target field information
                    target_field_name VARCHAR(255) NOT NULL,
                    target_field_type VARCHAR(100),
                    
                    -- Pattern metadata
                    pattern_context JSONB,
                    confidence_score FLOAT DEFAULT 0.0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used_at TIMESTAMP WITH TIME ZONE,
                    
                    -- Learning metadata
                    learned_from_user BOOLEAN DEFAULT true,
                    learning_source VARCHAR(100),
                    
                    -- Audit fields
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    created_by VARCHAR(255)
                );
            """
                )
            )

            print("✅ Created new mapping_learning_patterns table")

            # 5. Create indexes for performance
            print("\n📝 Creating indexes...")

            # Indexes for mapping_learning_patterns
            await session.execute(
                text(
                    """
                CREATE INDEX idx_mapping_patterns_client_source 
                ON migration.mapping_learning_patterns (client_account_id, source_field_name);
            """
                )
            )

            await session.execute(
                text(
                    """
                CREATE INDEX idx_mapping_patterns_target 
                ON migration.mapping_learning_patterns (target_field_name);
            """
                )
            )

            await session.execute(
                text(
                    """
                CREATE INDEX idx_mapping_patterns_confidence 
                ON migration.mapping_learning_patterns (confidence_score);
            """
                )
            )

            await session.execute(
                text(
                    """
                CREATE INDEX idx_mapping_patterns_embedding 
                ON migration.mapping_learning_patterns 
                USING ivfflat (source_field_embedding vector_cosine_ops);
            """
                )
            )

            # Indexes for asset_classification_patterns
            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_classification_patterns_name_embedding 
                ON migration.asset_classification_patterns 
                USING ivfflat (asset_name_embedding vector_cosine_ops);
            """
                )
            )

            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_classification_patterns_metadata_embedding 
                ON migration.asset_classification_patterns 
                USING ivfflat (metadata_embedding vector_cosine_ops);
            """
                )
            )

            print("✅ Created performance indexes")

            # 6. Create missing tables
            print("\n📝 Creating missing learning tables...")

            # Create confidence_thresholds table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS migration.confidence_thresholds (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id VARCHAR(255) NOT NULL,
                    engagement_id VARCHAR(255),
                    
                    -- Threshold configuration
                    operation_type VARCHAR(100) NOT NULL,
                    threshold_name VARCHAR(100) NOT NULL,
                    threshold_value FLOAT NOT NULL,
                    
                    -- Adaptation metadata
                    initial_value FLOAT NOT NULL,
                    adjustment_count INTEGER DEFAULT 0,
                    last_adjustment TIMESTAMP WITH TIME ZONE,
                    
                    -- Performance tracking
                    true_positives INTEGER DEFAULT 0,
                    false_positives INTEGER DEFAULT 0,
                    true_negatives INTEGER DEFAULT 0,
                    false_negatives INTEGER DEFAULT 0,
                    
                    -- Calculated metrics
                    precision FLOAT DEFAULT 0.0,
                    recall FLOAT DEFAULT 0.0,
                    f1_score FLOAT DEFAULT 0.0,
                    
                    -- Audit fields
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    created_by VARCHAR(255)
                );
            """
                )
            )

            # Create user_feedback_events table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS migration.user_feedback_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id VARCHAR(255) NOT NULL,
                    engagement_id VARCHAR(255),
                    
                    -- Feedback context
                    feedback_type VARCHAR(100) NOT NULL,
                    operation_id VARCHAR(255),
                    
                    -- Original suggestion
                    original_suggestion JSONB NOT NULL,
                    original_confidence FLOAT,
                    
                    -- User correction
                    user_correction JSONB NOT NULL,
                    correction_type VARCHAR(100) NOT NULL,
                    
                    -- Pattern references
                    related_patterns JSONB,
                    
                    -- Learning impact
                    pattern_updates_applied BOOLEAN DEFAULT false,
                    threshold_updates_applied BOOLEAN DEFAULT false,
                    
                    -- Audit fields
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    created_by VARCHAR(255)
                );
            """
                )
            )

            print("✅ Created missing learning tables")

            # 7. Create additional indexes
            print("\n📝 Creating additional indexes...")

            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_confidence_thresholds_client_operation 
                ON migration.confidence_thresholds (client_account_id, operation_type);
            """
                )
            )

            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_feedback_events_client_type 
                ON migration.user_feedback_events (client_account_id, feedback_type);
            """
                )
            )

            print("✅ Created additional indexes")

            # Commit all changes
            await session.commit()

            print("\n🎯 Learning Tables Update Complete!")
            print("\n📊 Summary:")
            print("   - ✅ Updated asset_classification_patterns to 1024 dimensions")
            print("   - ✅ Backed up old mapping_learning_patterns table")
            print("   - ✅ Created new mapping_learning_patterns with vector support")
            print("   - ✅ Created confidence_thresholds table")
            print("   - ✅ Created user_feedback_events table")
            print("   - ✅ Created performance indexes with pgvector support")
            print(
                "   - ✅ All tables ready for thenlper/gte-large model (1024 dimensions)"
            )

        except Exception as e:
            print(f"❌ Error updating tables: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(update_learning_tables())
