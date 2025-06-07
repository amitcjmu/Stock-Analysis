#!/usr/bin/env python3

import asyncio
from app.models.user_profile import UserProfile
from app.schemas.auth_schemas import UserStatus
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, and_

async def test_user_lookup():
    async with AsyncSessionLocal() as session:
        try:
            # Check what users exist in the database
            query = select(UserProfile).where(UserProfile.status == UserStatus.ACTIVE)
            result = await session.execute(query)
            users = result.scalars().all()
            
            print(f'Found {len(users)} active users:')
            for user in users:
                print(f'  - user_id: {user.user_id}')
                print(f'  - status: {user.status}')
                print(f'  - has deactivate method: {hasattr(user, "deactivate")}')
                if user.user:
                    print(f'  - email: {user.user.email}')
                    print(f'  - full_name: {user.user.first_name} {user.user.last_name}')
                print()
                
            # Test looking up specific test user
            test_user_email = 'test.working@example.com'
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == test_user_email,
                    UserProfile.status == UserStatus.ACTIVE
                )
            )
            result = await session.execute(query)
            user_profile = result.scalar_one_or_none()
            
            if user_profile:
                print(f'Found user to deactivate: {test_user_email}')
                print(f'  - status: {user_profile.status}')
                print(f'  - has deactivate method: {hasattr(user_profile, "deactivate")}')
                
                # Test if deactivate method exists and works
                if hasattr(user_profile, 'deactivate'):
                    print('Testing deactivate method...')
                    try:
                        user_profile.deactivate('admin_user', 'Testing deactivation')
                        await session.commit()
                        print('Deactivation test successful!')
                    except Exception as e:
                        print(f'Deactivation test failed: {e}')
                        await session.rollback()
                else:
                    print('deactivate method not found!')
            else:
                print(f'User {test_user_email} not found or not active')
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_user_lookup()) 