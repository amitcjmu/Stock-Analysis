"""
Check database schema status.
"""
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal


async def check_schema():
    """Check if database schema is ready."""
    print("Checking database schema...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check for key tables
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN (
                    'users', 'client_accounts', 'engagements', 
                    'user_profiles', 'user_roles', 'discovery_flows',
                    'data_imports', 'crewai_flow_state_extensions'
                )
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print(f"\nFound {len(tables)}/8 required tables:")
            for table in tables:
                print(f"  ✓ {table}")
            
            missing_tables = {
                'users', 'client_accounts', 'engagements', 
                'user_profiles', 'user_roles', 'discovery_flows',
                'data_imports', 'crewai_flow_state_extensions'
            } - set(tables)
            
            if missing_tables:
                print("\nMissing tables:")
                for table in missing_tables:
                    print(f"  ✗ {table}")
            
            # Check specific columns
            print("\nChecking client_accounts columns...")
            result = await db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'client_accounts'
                AND column_name IN ('id', 'name', 'slug', 'created_at')
                ORDER BY column_name
            """))
            columns = [row[0] for row in result]
            
            for col in ['id', 'name', 'slug', 'created_at']:
                if col in columns:
                    print(f"  ✓ {col}")
                else:
                    print(f"  ✗ {col} (missing)")
            
            # Check if migrations are needed
            if len(tables) < 8 or 'slug' not in columns:
                print("\n⚠️  Database schema is incomplete. Please run migrations:")
                print("    docker exec migration_backend alembic upgrade head")
                return False
            else:
                print("\n✅ Database schema is ready for seeding!")
                return True
                
        except Exception as e:
            print(f"\n❌ Error checking schema: {str(e)}")
            return False


if __name__ == "__main__":
    asyncio.run(check_schema())