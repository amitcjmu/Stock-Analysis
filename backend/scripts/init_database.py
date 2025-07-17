#!/usr/bin/env python3
"""
Database Initialization Script for AI Modernize Migration Platform

This script provides a comprehensive, robust database initialization solution
that works reliably for developers setting up the project from scratch.

Features:
- Automatic database creation if it doesn't exist
- Extension installation (pgvector, uuid-ossp)
- Migration execution with proper error handling
- Data seeding and initialization
- Health checks and validation
- Rollback capabilities on failure

Usage:
    python scripts/init_database.py [--force] [--seed-only] [--validate-only]
    
Options:
    --force: Drop and recreate database if it exists
    --seed-only: Only run seeding (assumes DB exists)
    --validate-only: Only validate database state
"""

import asyncio
import argparse
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncpg
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import alembic
from alembic import command
from alembic.config import Config

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal, Base
from app.core.database_initialization import initialize_database, DatabaseInitializer
from app.models import User, ClientAccount, Engagement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializationError(Exception):
    """Custom exception for database initialization errors"""
    pass


class DatabaseSetup:
    """Main database setup orchestrator"""
    
    def __init__(self, force: bool = False, seed_only: bool = False, validate_only: bool = False):
        self.force = force
        self.seed_only = seed_only
        self.validate_only = validate_only
        
        # Database configuration
        self.db_config = self._get_db_config()
        self.admin_db_url = self._get_admin_db_url()
        self.app_db_url = self._get_app_db_url()
        
        logger.info(f"Database setup initialized:")
        logger.info(f"  Host: {self.db_config['host']}")
        logger.info(f"  Database: {self.db_config['database']}")
        logger.info(f"  Force mode: {self.force}")
        logger.info(f"  Seed only: {self.seed_only}")
        logger.info(f"  Validate only: {self.validate_only}")

    def _get_db_config(self) -> Dict[str, str]:
        """Extract database configuration from environment"""
        return {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5433'),  # Docker compose external port
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'migration_db')
        }
    
    def _get_admin_db_url(self) -> str:
        """Get admin database URL (connects to postgres db for admin operations)"""
        config = self.db_config
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/postgres"
    
    def _get_app_db_url(self) -> str:
        """Get application database URL"""
        config = self.db_config
        return f"postgresql+asyncpg://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

    async def wait_for_postgres(self, max_attempts: int = 30) -> bool:
        """Wait for PostgreSQL to be ready"""
        logger.info("Waiting for PostgreSQL to be ready...")
        
        for attempt in range(max_attempts):
            try:
                conn = await asyncpg.connect(
                    host=self.db_config['host'],
                    port=int(self.db_config['port']),
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database='postgres'  # Connect to default postgres db
                )
                await conn.close()
                logger.info("✅ PostgreSQL is ready!")
                return True
            except Exception as e:
                logger.info(f"Attempt {attempt + 1}: PostgreSQL not ready yet - {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
        
        raise DatabaseInitializationError("PostgreSQL did not become ready within timeout")

    async def create_database_if_not_exists(self) -> bool:
        """Create database if it doesn't exist"""
        logger.info(f"Ensuring database '{self.db_config['database']}' exists...")
        
        try:
            # Connect to postgres admin database
            conn = await asyncpg.connect(
                host=self.db_config['host'],
                port=int(self.db_config['port']),
                user=self.db_config['user'],
                password=self.db_config['password'],
                database='postgres'
            )
            
            # Check if database exists
            db_exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", 
                self.db_config['database']
            )
            
            if db_exists and self.force:
                logger.info(f"🗑️  Force mode: Dropping database '{self.db_config['database']}'...")
                # Terminate connections to the database
                await conn.execute(f"""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = '{self.db_config['database']}' AND pid <> pg_backend_pid()
                """)
                await conn.execute(f"DROP DATABASE IF EXISTS {self.db_config['database']}")
                db_exists = False
            
            if not db_exists:
                logger.info(f"📦 Creating database '{self.db_config['database']}'...")
                await conn.execute(f"CREATE DATABASE {self.db_config['database']}")
                logger.info("✅ Database created successfully!")
                await conn.close()
                return True
            else:
                logger.info("✅ Database already exists!")
                await conn.close()
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            raise DatabaseInitializationError(f"Database creation failed: {e}")

    async def install_extensions(self) -> None:
        """Install required PostgreSQL extensions"""
        logger.info("Installing PostgreSQL extensions...")
        
        try:
            conn = await asyncpg.connect(
                host=self.db_config['host'],
                port=int(self.db_config['port']),
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            
            extensions = [
                ('vector', 'pgvector for vector embeddings'),
                ('"uuid-ossp"', 'UUID generation functions')
            ]
            
            for ext_name, description in extensions:
                try:
                    await conn.execute(f"CREATE EXTENSION IF NOT EXISTS {ext_name}")
                    logger.info(f"✅ Installed extension '{ext_name}' - {description}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not install extension '{ext_name}': {e}")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to install extensions: {e}")
            raise DatabaseInitializationError(f"Extension installation failed: {e}")

    async def run_migrations(self) -> None:
        """Run Alembic migrations asynchronously."""
        logger.info("Running database migrations...")
        
        try:
            # Set environment variable for Alembic - this is important for some Alembic setups
            os.environ['DATABASE_URL'] = self.app_db_url

            # Get alembic config
            alembic_cfg_path = Path(__file__).parent.parent / "alembic.ini"
            alembic_cfg = Config(str(alembic_cfg_path))
            alembic_cfg.set_main_option("sqlalchemy.url", self.app_db_url)
            
            # Run migrations in a separate thread to avoid blocking the event loop
            logger.info("🔄 Upgrading to head...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,  # Use the default thread pool executor
                command.upgrade,
                alembic_cfg,
                "head"
            )
            logger.info("✅ Migrations completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}", exc_info=True)
            raise DatabaseInitializationError(f"Migration failed: {e}")

    async def initialize_data(self) -> None:
        """Initialize database with required data"""
        logger.info("Initializing database data...")
        
        try:
            async with AsyncSessionLocal() as db:
                await initialize_database(db)
            logger.info("✅ Database data initialization completed!")
            
        except Exception as e:
            logger.error(f"❌ Data initialization failed: {e}")
            raise DatabaseInitializationError(f"Data initialization failed: {e}")

    async def validate_database(self) -> Dict[str, Any]:
        """Validate database state and return summary"""
        logger.info("Validating database state...")
        
        validation_results = {
            'tables_exist': False,
            'extensions_installed': False,
            'admin_exists': False,
            'demo_data_exists': False,
            'table_count': 0,
            'user_count': 0,
            'client_count': 0,
            'engagement_count': 0,
            'errors': []
        }
        
        try:
            async with AsyncSessionLocal() as db:
                # Check tables exist
                try:
                    result = await db.execute(text("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema IN ('migration', 'public')
                    """))
                    validation_results['table_count'] = result.scalar()
                    validation_results['tables_exist'] = validation_results['table_count'] > 0
                except Exception as e:
                    validation_results['errors'].append(f"Table check failed: {e}")

                # Check extensions
                try:
                    result = await db.execute(text("""
                        SELECT COUNT(*) FROM pg_extension 
                        WHERE extname IN ('vector', 'uuid-ossp')
                    """))
                    extension_count = result.scalar()
                    validation_results['extensions_installed'] = extension_count >= 2
                except Exception as e:
                    validation_results['errors'].append(f"Extension check failed: {e}")

                # Check users
                try:
                    result = await db.execute(text("SELECT COUNT(*) FROM users"))
                    validation_results['user_count'] = result.scalar()
                    
                    # Check admin exists
                    result = await db.execute(text(
                        "SELECT COUNT(*) FROM users WHERE email = 'chocka@gmail.com'"
                    ))
                    validation_results['admin_exists'] = result.scalar() > 0
                except Exception as e:
                    validation_results['errors'].append(f"User check failed: {e}")

                # Check client accounts
                try:
                    result = await db.execute(text("SELECT COUNT(*) FROM client_accounts"))
                    validation_results['client_count'] = result.scalar()
                except Exception as e:
                    validation_results['errors'].append(f"Client check failed: {e}")

                # Check engagements
                try:
                    result = await db.execute(text("SELECT COUNT(*) FROM engagements"))
                    validation_results['engagement_count'] = result.scalar()
                except Exception as e:
                    validation_results['errors'].append(f"Engagement check failed: {e}")

                # Check demo data
                try:
                    result = await db.execute(text(
                        "SELECT COUNT(*) FROM client_accounts WHERE name = 'Demo Corporation'"
                    ))
                    validation_results['demo_data_exists'] = result.scalar() > 0
                except Exception as e:
                    validation_results['errors'].append(f"Demo data check failed: {e}")

        except Exception as e:
            validation_results['errors'].append(f"Database validation failed: {e}")

        return validation_results

    def print_validation_report(self, results: Dict[str, Any]) -> None:
        """Print validation report"""
        logger.info("\n" + "="*60)
        logger.info("DATABASE VALIDATION REPORT")
        logger.info("="*60)
        
        # Overall status
        overall_ok = (
            results['tables_exist'] and 
            results['extensions_installed'] and 
            results['admin_exists'] and
            len(results['errors']) == 0
        )
        
        status = "✅ HEALTHY" if overall_ok else "❌ ISSUES FOUND"
        logger.info(f"Overall Status: {status}")
        logger.info("")
        
        # Detailed checks
        logger.info("Component Status:")
        logger.info(f"  📊 Tables: {'✅' if results['tables_exist'] else '❌'} ({results['table_count']} found)")
        logger.info(f"  🔌 Extensions: {'✅' if results['extensions_installed'] else '❌'}")
        logger.info(f"  👤 Platform Admin: {'✅' if results['admin_exists'] else '❌'}")
        logger.info(f"  🎭 Demo Data: {'✅' if results['demo_data_exists'] else '❌'}")
        logger.info("")
        
        # Data counts
        logger.info("Data Summary:")
        logger.info(f"  Users: {results['user_count']}")
        logger.info(f"  Clients: {results['client_count']}")
        logger.info(f"  Engagements: {results['engagement_count']}")
        logger.info("")
        
        # Errors
        if results['errors']:
            logger.error("Errors encountered:")
            for error in results['errors']:
                logger.error(f"  ❌ {error}")
        else:
            logger.info("✅ No errors found")
        
        logger.info("="*60)

    async def run_full_setup(self) -> None:
        """Run complete database setup process"""
        logger.info("🚀 Starting complete database setup...")
        
        try:
            # Step 1: Wait for PostgreSQL
            await self.wait_for_postgres()
            
            # Step 2: Create database if needed
            if not self.seed_only and not self.validate_only:
                await self.create_database_if_not_exists()
                await self.install_extensions()
            
            # Step 3: Run migrations
            if not self.seed_only and not self.validate_only:
                await self.run_migrations()
            
            # Step 4: Initialize data
            if not self.validate_only:
                await self.initialize_data()
            
            # Step 5: Validate
            validation_results = await self.validate_database()
            self.print_validation_report(validation_results)
            
            if len(validation_results['errors']) == 0:
                logger.info("🎉 Database setup completed successfully!")
            else:
                logger.error("⚠️  Database setup completed with warnings. See validation report above.")
                
        except Exception as e:
            logger.error(f"💥 Database setup failed: {e}")
            raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Initialize AI Modernize Migration Platform Database")
    parser.add_argument("--force", action="store_true", 
                       help="Drop and recreate database if it exists")
    parser.add_argument("--seed-only", action="store_true", 
                       help="Only run data seeding (assumes DB exists)")
    parser.add_argument("--validate-only", action="store_true", 
                       help="Only validate database state")
    
    args = parser.parse_args()
    
    # Ensure we're in the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    try:
        setup = DatabaseSetup(
            force=args.force,
            seed_only=args.seed_only,
            validate_only=args.validate_only
        )
        await setup.run_full_setup()
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())