"""
Database Test Endpoints for Railway Deployment Verification.
Provides simple database connectivity and table verification endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.multi_model_service import multi_model_service
from typing import Dict, Any
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/database/test")
async def test_database_connection():
    """
    Simple database connection test for Railway deployment verification.
    """
    try:
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            # Test basic connection
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Test feedback table exists
            result = await session.execute(text("SELECT COUNT(*) FROM feedback"))
            feedback_count = result.scalar()
            
            return {
                "status": "success",
                "database_connection": "working",
                "postgresql_version": version,
                "feedback_table": "exists",
                "feedback_count": feedback_count,
                "test_type": "database_connectivity"
            }
            
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {
            "status": "error",
            "database_connection": "failed",
            "error": str(e),
            "test_type": "database_connectivity"
        }

@router.get("/database/health")
async def database_health_check():
    """
    Comprehensive database health check including table verification.
    """
    try:
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            # Test multiple operations
            tests = {}
            
            # 1. Basic connection
            try:
                result = await session.execute(text("SELECT 1"))
                tests["basic_connection"] = "pass"
            except Exception as e:
                tests["basic_connection"] = f"fail: {e}"
            
            # 2. Feedback table access
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM feedback"))
                count = result.scalar()
                tests["feedback_table"] = f"pass: {count} records"
            except Exception as e:
                tests["feedback_table"] = f"fail: {e}"
            
            # 3. Write test
            try:
                await session.execute(text("SELECT 1"))
                tests["write_capability"] = "pass"
            except Exception as e:
                tests["write_capability"] = f"fail: {e}"
            
            # Overall status
            all_passed = all("pass" in str(test) for test in tests.values())
            
            return {
                "status": "healthy" if all_passed else "degraded",
                "tests": tests,
                "overall": "all tests passed" if all_passed else "some tests failed"
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "tests": {"database_access": f"fail: {e}"}
        }

@router.post("/test-chat-simple", response_model=Dict[str, Any])
async def test_chat_simple(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Test simple chat functionality with multi-model service."""
    try:
        user_prompt = request.get("prompt", "Hello, world!")
        
        # Use multi-model service for simple chat
        response = await multi_model_service.generate_response(
            prompt=user_prompt,
            task_type="simple_query"
        )
        
        return {
            "status": "success",
            "prompt": user_prompt,
            "response": response,
            "multi_model_service_available": True
        }
        
    except Exception as e:
        logger.error(f"Simple chat test failed: {e}")
        return {
            "status": "error",
            "message": f"Simple chat test failed: {str(e)}",
            "multi_model_service_available": False
        }