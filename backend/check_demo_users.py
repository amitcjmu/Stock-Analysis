#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/app')

from app.core.database import AsyncSessionLocal
from app.models.client_account import User
from sqlalchemy import select

async def check_demo_users():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User.email, User.id, User.is_mock))
        users = result.fetchall()
        print('All users in database:')
        for email, user_id, is_mock in users:
            print(f'  Email: {email}, ID: {user_id}, Mock: {is_mock}')

if __name__ == "__main__":
    asyncio.run(check_demo_users()) 