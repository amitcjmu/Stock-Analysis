"""
Enhanced Health Check for Assessment Flow

Extends the existing health check to include assessment flow services.
"""

import logging
from datetime import datetime

try:
    from fastapi import APIRouter, Response
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.database import AsyncSessionLocal

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object
    Response = object
    text = None
    AsyncSession = object
    AsyncSessionLocal = None

logger = logging.getLogger(__name__)

router = APIRouter() if FASTAPI_AVAILABLE else None


class HealthCheckError(Exception):
    """Health check specific error"""

    pass


async def check_assessment_tables_health():
    """Check that assessment flow tables are accessible"""
    if not AsyncSessionLocal:
        raise HealthCheckError("Database not available")

    async with AsyncSessionLocal() as db:
        try:
            # Check basic assessment flow tables exist
            tables_to_check = [
                "assessment_flows",
                "engagement_architecture_standards",
                "application_architecture_overrides",
                "application_components",
                "tech_debt_analysis",
                "component_treatments",
                "sixr_decisions",
                "assessment_learning_feedback",
            ]

            for table in tables_to_check:
                try:
                    await db.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                except Exception as e:
                    # Table might not exist yet or be empty - that's ok for development
                    logger.warning(f"Assessment table {table} check failed: {str(e)}")

            logger.debug("Assessment tables health check completed")

        except Exception as e:
            raise HealthCheckError(f"Assessment tables unhealthy: {str(e)}")


async def check_crewai_health():
    """Check CrewAI service availability"""
    try:
        # Import here to avoid circular imports
        from app.services.crewai_service import get_crewai_service

        service = get_crewai_service()

        # Basic configuration check
        if not service or not hasattr(service, "is_configured"):
            raise HealthCheckError("CrewAI service not available")

        # Check if service is configured (this should be fast)
        if not service.is_configured():
            raise HealthCheckError("CrewAI service not properly configured")

        logger.debug("CrewAI health check completed")

    except ImportError:
        # CrewAI service not available yet - this is ok during development
        logger.warning("CrewAI service not available - assessment flow may not work")
    except Exception as e:
        raise HealthCheckError(f"CrewAI service unhealthy: {str(e)}")


async def check_assessment_flow_service():
    """Check assessment flow service availability"""
    try:
        # Try to import assessment flow components
        from app.services.crewai_flows.unified_assessment_flow import \
            UnifiedAssessmentFlow

        # Basic import successful
        logger.debug("Assessment flow service import successful")

    except ImportError as e:
        # Assessment flow not implemented yet - this is expected during development
        logger.warning(f"Assessment flow service not available: {str(e)}")
    except Exception as e:
        raise HealthCheckError(f"Assessment flow service unhealthy: {str(e)}")


async def check_sse_health():
    """Check Server-Sent Events service"""
    try:
        # Check if SSE is enabled
        import os

        sse_enabled = os.getenv("SSE_ENABLED", "false").lower() == "true"

        if sse_enabled:
            # Could add more sophisticated SSE health checks here
            logger.debug("SSE service enabled and healthy")
        else:
            logger.debug("SSE service disabled")

    except Exception as e:
        raise HealthCheckError(f"SSE service unhealthy: {str(e)}")


async def check_redis_health():
    """Check Redis connectivity for assessment flow workers"""
    try:
        import os

        redis_url = os.getenv("REDIS_URL")

        if not redis_url:
            logger.debug("Redis not configured - worker mode disabled")
            return

        # Try to connect to Redis
        try:
            import redis.asyncio as redis

            redis_client = redis.from_url(redis_url)
            await redis_client.ping()
            await redis_client.close()

            logger.debug("Redis health check completed")

        except ImportError:
            logger.warning("Redis client not available")
        except Exception as e:
            raise HealthCheckError(f"Redis unhealthy: {str(e)}")

    except Exception as e:
        raise HealthCheckError(f"Redis health check failed: {str(e)}")


async def get_assessment_flow_metrics():
    """Get basic assessment flow metrics for health reporting"""
    metrics = {
        "assessment_flows_active": 0,
        "assessment_flows_total": 0,
        "last_flow_created": None,
    }

    try:
        if not AsyncSessionLocal:
            return metrics

        async with AsyncSessionLocal() as db:
            # Try to get basic metrics from assessment flows table
            try:
                result = await db.execute(
                    text(
                        """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status IN ('initialized', 'processing', 'paused_for_user_input')) as active,
                        MAX(created_at) as last_created
                    FROM assessment_flows
                """
                    )
                )

                row = result.fetchone()
                if row:
                    metrics["assessment_flows_total"] = row.total or 0
                    metrics["assessment_flows_active"] = row.active or 0
                    metrics["last_flow_created"] = (
                        row.last_created.isoformat() if row.last_created else None
                    )

            except Exception:
                # Table might not exist yet - that's ok
                pass

    except Exception as e:
        logger.warning(f"Could not get assessment flow metrics: {str(e)}")

    return metrics


if FASTAPI_AVAILABLE:

    @router.get("/health/assessment")
    async def assessment_health_check():
        """Assessment Flow specific health check"""

        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "assessment_flow",
            "version": "1.0.0",
            "checks": {},
        }

        checks = [
            ("database", check_assessment_tables_health),
            ("crewai", check_crewai_health),
            ("assessment_service", check_assessment_flow_service),
            ("sse", check_sse_health),
            ("redis", check_redis_health),
        ]

        for check_name, check_func in checks:
            try:
                await check_func()
                health_status["checks"][check_name] = "healthy"
            except HealthCheckError as e:
                health_status["checks"][check_name] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
            except Exception as e:
                health_status["checks"][check_name] = f"error: {str(e)}"
                health_status["status"] = "degraded"

        # Add metrics
        try:
            health_status["metrics"] = await get_assessment_flow_metrics()
        except Exception as e:
            health_status["metrics"] = {"error": str(e)}

        # Determine overall status
        unhealthy_checks = [
            k for k, v in health_status["checks"].items() if v.startswith("unhealthy")
        ]
        if unhealthy_checks:
            health_status["status"] = "unhealthy"
            health_status["unhealthy_checks"] = unhealthy_checks

        status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503

        return Response(
            content=health_status,
            status_code=status_code,
            media_type="application/json",
        )

    @router.get("/health/assessment/detailed")
    async def detailed_assessment_health():
        """Detailed assessment flow health check with component status"""

        detailed_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "metrics": {},
            "configuration": {},
        }

        # Component health checks
        components = {
            "database": check_assessment_tables_health,
            "crewai_service": check_crewai_health,
            "assessment_flow": check_assessment_flow_service,
            "sse_service": check_sse_health,
            "redis_cache": check_redis_health,
        }

        for component_name, check_func in components.items():
            component_status = {
                "status": "unknown",
                "last_check": datetime.utcnow().isoformat(),
                "details": {},
            }

            try:
                await check_func()
                component_status["status"] = "healthy"
            except HealthCheckError as e:
                component_status["status"] = "unhealthy"
                component_status["error"] = str(e)
                detailed_status["overall_status"] = "degraded"
            except Exception as e:
                component_status["status"] = "error"
                component_status["error"] = str(e)
                detailed_status["overall_status"] = "degraded"

            detailed_status["components"][component_name] = component_status

        # Get metrics
        detailed_status["metrics"] = await get_assessment_flow_metrics()

        # Configuration summary
        import os

        detailed_status["configuration"] = {
            "assessment_flow_enabled": os.getenv("ASSESSMENT_FLOW_ENABLED", "false"),
            "crewai_enabled": os.getenv("CREWAI_ASSESSMENT_AGENTS_ENABLED", "false"),
            "sse_enabled": os.getenv("SSE_ENABLED", "false"),
            "redis_configured": bool(os.getenv("REDIS_URL")),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
        }

        return detailed_status

else:
    # Fallback when FastAPI is not available
    async def assessment_health_check():
        return {"status": "unavailable", "reason": "FastAPI not available"}

    async def detailed_assessment_health():
        return {"status": "unavailable", "reason": "FastAPI not available"}
