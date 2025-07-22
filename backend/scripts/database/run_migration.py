#!/usr/bin/env python3
"""
Railway Database Migration Script
Runs database migrations and creates feedback tables in Railway production
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def run_migration():
    """Run database migrations for Railway deployment."""
    print("🚀 Starting Railway Database Migration...")
    print("=" * 50)
    
    # Check environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found. This script should run on Railway.")
        return False
    
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
    print(f"🗄️ Database URL: {'Set' if database_url else 'Not Set'}")
    
    try:
        # Import after path setup
        from app.core.database import AsyncSessionLocal, Base, engine
        from app.models.client_account import ClientAccount, Engagement, User
        from app.models.feedback import Feedback, FeedbackSummary
        print("✅ Database modules imported successfully")
        
        # Test connection
        print("\n🔍 Testing database connection...")
        from sqlalchemy import text
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("✅ PostgreSQL Connection: SUCCESS")
            print(f"📋 Database Version: {version}")
        
        # Create all tables
        print("\n🔧 Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")
        
        # Test feedback table specifically
        print("\n🧪 Testing feedback table...")
        async with AsyncSessionLocal() as session:
            from sqlalchemy import func, select
            
            # Check if feedback table exists and is accessible
            result = await session.execute(text("SELECT COUNT(*) FROM feedback"))
            count = result.scalar()
            print(f"📊 Feedback table: {count} records found")
            
            # Test a simple insert
            print("\n💾 Testing feedback insertion...")
            feedback = Feedback(
                feedback_type="page_feedback",
                page="Railway Migration Test",
                rating=5,
                comment="Testing feedback table creation in Railway",
                category="migration",
                breadcrumb="Railway > Migration > Test",
                status="new"
            )
            
            session.add(feedback)
            await session.commit()
            await session.refresh(feedback)
            
            print(f"✅ Test feedback created with ID: {feedback.id}")
            
            # Verify the insert
            result = await session.execute(text("SELECT COUNT(*) FROM feedback"))
            new_count = result.scalar()
            print(f"📊 Feedback table after insert: {new_count} records")
        
        print("\n" + "=" * 50)
        print("🎉 Railway Database Migration: SUCCESSFUL")
        print("✅ Feedback system is ready for production use!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    if success:
        print("\n🚀 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Migration failed!")
        sys.exit(1) 