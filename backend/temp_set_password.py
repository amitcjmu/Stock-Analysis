#!/usr/bin/env python3
"""
Temporary script to set password for chocka@gmail.com user
"""
import asyncio
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
import sys
import os

# Add the backend directory to the path
sys.path.append('/app')

# Database URL
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"

async def set_user_password():
    """Set password for chocka@gmail.com user"""
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Hash the password
            password = "admin123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update the user's password
            from sqlalchemy import text
            result = await session.execute(
                text("UPDATE migration.users SET password_hash = :password_hash WHERE email = :email"),
                {"password_hash": password_hash, "email": "chocka@gmail.com"}
            )
            
            await session.commit()
            
            if result.rowcount > 0:
                print(f"✅ Password updated successfully for chocka@gmail.com")
                print(f"   New password: admin123")
                print(f"   Hash: {password_hash[:50]}...")
            else:
                print("❌ No user found with email chocka@gmail.com")
                
    except Exception as e:
        print(f"❌ Error updating password: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(set_user_password()) 