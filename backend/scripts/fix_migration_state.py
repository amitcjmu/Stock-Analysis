#!/usr/bin/env python3
"""
Migration State Fix Script

This script fixes common Alembic migration state issues that occur when:
1. Database has tables but alembic_version is empty
2. Database has tables but alembic_version references non-existent migrations
3. Missing migration files that are referenced in alembic_version

Used by CC to resolve migration conflicts during deployment.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expected migration version (the current comprehensive schema)
EXPECTED_MIGRATION_VERSION = "014_fix_remaining_agent_foreign_keys"

# Expected core tables that should exist in a properly migrated database
EXPECTED_CORE_TABLES = {
    "client_accounts",
    "users", 
    "engagements",
    "user_profiles",
    "assets",
    "data_imports",
    "discovery_flows",
    "crewai_flow_state_extensions",
    "migration_waves",
    "assessments"
}


class MigrationStateFixer:
    """Handles migration state fixes"""
    
    def __init__(self):
        self.settings = Settings()
        self.engine = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.engine = create_async_engine(
            self.settings.database_url_async,
            echo=False,
            pool_pre_ping=True
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.engine:
            await self.engine.dispose()
    
    async def check_database_connection(self) -> bool:
        """Test database connectivity"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def get_existing_tables(self) -> List[str]:
        """Get list of existing tables in the database"""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'migration' OR table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                logger.info(f"Found {len(tables)} existing tables")
                return tables
        except Exception as e:
            logger.error(f"Failed to get existing tables: {e}")
            return []
    
    async def get_alembic_version(self) -> Optional[str]:
        """Get current Alembic version from database"""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                row = result.fetchone()
                version = row[0] if row else None
                logger.info(f"Current Alembic version: {version or 'None'}")
                return version
        except Exception as e:
            logger.warning(f"Could not read alembic_version table: {e}")
            return None
    
    async def check_alembic_version_table_exists(self) -> bool:
        """Check if alembic_version table exists"""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'alembic_version'
                        AND (table_schema = 'migration' OR table_schema = 'public')
                    )
                """))
                exists = result.scalar()
                logger.info(f"alembic_version table exists: {exists}")
                return exists
        except Exception as e:
            logger.error(f"Failed to check alembic_version table: {e}")
            return False
    
    async def create_alembic_version_table(self):
        """Create alembic_version table if it doesn't exist"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS alembic_version (
                        version_num VARCHAR(50) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    )
                """))
                await conn.commit()
                logger.info("✅ Created alembic_version table")
        except Exception as e:
            logger.error(f"Failed to create alembic_version table: {e}")
            raise
    
    async def set_migration_version(self, version: str):
        """Set the migration version in alembic_version table"""
        try:
            async with self.engine.connect() as conn:
                # Clear existing version
                await conn.execute(text("DELETE FROM alembic_version"))
                
                # Insert new version
                await conn.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
                    {"version": version}
                )
                await conn.commit()
                logger.info(f"✅ Set migration version to: {version}")
        except Exception as e:
            logger.error(f"Failed to set migration version: {e}")
            raise
    
    async def validate_core_tables(self, existing_tables: List[str]) -> bool:
        """Validate that core tables exist"""
        missing_tables = EXPECTED_CORE_TABLES - set(existing_tables)
        if missing_tables:
            logger.warning(f"Missing core tables: {missing_tables}")
            return False
        
        logger.info("✅ All core tables present")
        return True
    
    async def check_migration_files_exist(self) -> bool:
        """Check if expected migration files exist"""
        alembic_versions_dir = Path(__file__).parent.parent / "alembic" / "versions"
        expected_migration_file = alembic_versions_dir / f"{EXPECTED_MIGRATION_VERSION}.py"
        
        exists = expected_migration_file.exists()
        logger.info(f"Migration file {EXPECTED_MIGRATION_VERSION}.py exists: {exists}")
        
        if not exists:
            logger.warning(f"Expected migration file not found: {expected_migration_file}")
            # List available migration files
            if alembic_versions_dir.exists():
                available_files = list(alembic_versions_dir.glob("*.py"))
                logger.info(f"Available migration files: {[f.name for f in available_files]}")
        
        return exists
    
    async def fix_migration_state(self) -> bool:
        """Main method to fix migration state issues"""
        logger.info("🔧 Starting migration state fix...")
        
        # Check database connection
        if not await self.check_database_connection():
            return False
        
        # Get existing tables
        existing_tables = await self.get_existing_tables()
        if not existing_tables:
            logger.error("No tables found in database")
            return False
        
        # Check if core tables exist
        has_core_tables = await self.validate_core_tables(existing_tables)
        
        # Check alembic_version table
        alembic_table_exists = await self.check_alembic_version_table_exists()
        
        if not alembic_table_exists:
            logger.info("Creating missing alembic_version table...")
            await self.create_alembic_version_table()
        await self.alter_version_num_length()
        
        # Get current migration version
        current_version = await self.get_alembic_version()
        
        # Check if migration files exist
        migration_files_exist = await self.check_migration_files_exist()
        
        # Determine the fix strategy
        if has_core_tables and not current_version:
            # Case 1: Tables exist but no version recorded
            logger.info("🔧 Fix Strategy: Tables exist but no migration version recorded")
            if migration_files_exist:
                await self.set_migration_version(EXPECTED_MIGRATION_VERSION)
                logger.info("✅ Migration state fixed successfully")
                return True
            else:
                logger.error("❌ Cannot fix: Migration files missing")
                return False
                
        elif has_core_tables and current_version and not migration_files_exist:
            # Case 2: Tables exist, version recorded, but migration files missing
            logger.info("🔧 Fix Strategy: Migration files missing but database has tables")
            await self.set_migration_version(EXPECTED_MIGRATION_VERSION)
            logger.info("✅ Migration state fixed by resetting to current schema version")
            return True
            
        elif current_version == EXPECTED_MIGRATION_VERSION:
            # Case 3: Everything looks correct
            logger.info("✅ Migration state appears correct")
            return True
            
        elif current_version and current_version != EXPECTED_MIGRATION_VERSION:
            # Case 4: Different version recorded
            logger.info(f"🔧 Fix Strategy: Updating version from {current_version} to {EXPECTED_MIGRATION_VERSION}")
            await self.set_migration_version(EXPECTED_MIGRATION_VERSION)
            logger.info("✅ Migration version updated")
            return True
            
        else:
            # Case 5: Fresh database
            logger.info("Database appears to be fresh - migration system should handle initialization")
            return True

    async def alter_version_num_length(self):
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(50)"))
                await conn.commit()
                logger.info("✅ Altered version_num to VARCHAR(50)")
        except Exception as e:
            logger.warning(f"Failed to alter version_num length: {e}")


async def main():
    """Main entry point"""
    logger.info("🚀 Migration State Fixer Starting...")
    
    try:
        async with MigrationStateFixer() as fixer:
            success = await fixer.fix_migration_state()
            
            if success:
                logger.info("✅ Migration state fix completed successfully")
                return 0
            else:
                logger.error("❌ Migration state fix failed")
                return 1
                
    except Exception as e:
        logger.error(f"💥 Migration state fix crashed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)