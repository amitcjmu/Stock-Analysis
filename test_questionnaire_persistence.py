#!/usr/bin/env python3
"""
Test script to debug questionnaire persistence issues
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

# Import the models and functions we need to test
import sys
import os
sys.path.append('/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend')

from app.models.collection_flow import CollectionFlow
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse

async def test_questionnaire_persistence():
    """Test the questionnaire response storage and retrieval"""

    # Create async engine - use Docker database
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/migration_platform"
    engine = create_async_engine(DATABASE_URL, echo=True)

    # Create async session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        # Test 1: Check if we can query collection flows
        print("\n=== Test 1: Query Collection Flows ===")
        result = await session.execute(
            select(CollectionFlow).limit(5)
        )
        flows = result.scalars().all()
        print(f"Found {len(flows)} collection flows")
        for flow in flows:
            print(f"  - Flow ID: {flow.flow_id}, Status: {flow.status}")

        # Test 2: Check if we can query questionnaire responses
        print("\n=== Test 2: Query Questionnaire Responses ===")
        result = await session.execute(
            select(CollectionQuestionnaireResponse).limit(10)
        )
        responses = result.scalars().all()
        print(f"Found {len(responses)} questionnaire responses")
        for response in responses:
            print(f"  - Question: {response.question_id}, Value: {response.response_value}")

        # Test 3: Check the table structure
        print("\n=== Test 3: Check CollectionQuestionnaireResponse columns ===")
        if responses:
            sample = responses[0]
            print(f"Sample response attributes:")
            attrs_to_check = ['id', 'collection_flow_id', 'asset_id', 'questionnaire_type',
                             'question_id', 'response_value', 'response_metadata']
            for attr in attrs_to_check:
                if hasattr(sample, attr):
                    try:
                        value = getattr(sample, attr)
                        print(f"  - {attr}: {value}")
                    except:
                        print(f"  - {attr}: <error reading>")

        # Test 4: Check for specific flow
        print("\n=== Test 4: Check for specific flow responses ===")
        test_flow_id = "117381a0-21e0-46d6-8737-3eba06496046"  # From the Playwright test

        # First find the collection flow by flow_id
        flow_result = await session.execute(
            select(CollectionFlow).where(CollectionFlow.flow_id == test_flow_id)
        )
        flow = flow_result.scalar_one_or_none()

        if flow:
            print(f"Found flow: {flow.id} (flow_id: {flow.flow_id})")

            # Now query responses for this flow
            resp_result = await session.execute(
                select(CollectionQuestionnaireResponse)
                .where(CollectionQuestionnaireResponse.collection_flow_id == flow.id)
            )
            flow_responses = resp_result.scalars().all()
            print(f"Found {len(flow_responses)} responses for this flow")
            for resp in flow_responses:
                print(f"  - {resp.question_id}: {resp.response_value}")
        else:
            print(f"Flow {test_flow_id} not found")

if __name__ == "__main__":
    asyncio.run(test_questionnaire_persistence())
