import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware


def add_middlewares(app, settings):  # noqa: C901
    logger = logging.getLogger(__name__)

    # Trace ID middleware
    class TraceIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
            try:
                from app.core.logging import set_trace_id

                set_trace_id(trace_id)
            except Exception:
                pass
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            return response

    app.add_middleware(TraceIDMiddleware)
    logger.info("✅ Trace ID middleware added")

    # Tenant/Context/Request log/rate/security middlewares
    from app.core.middleware import ContextMiddleware, RequestLoggingMiddleware
    from app.middleware.adaptive_rate_limit_middleware import (
        AdaptiveRateLimitMiddleware,
    )
    from app.middleware.security_headers import (
        SecurityAuditMiddleware,
        SecurityHeadersMiddleware,
    )
    from app.middleware.tenant_context import TenantContextMiddleware
    from app.middleware.request_context_enforcement import (
        RequestContextEnforcementMiddleware,
    )

    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(RequestContextEnforcementMiddleware)
    logger.info(
        "✅ RequestContext enforcement middleware added for collection endpoints"
    )
    app.add_middleware(
        ContextMiddleware,
        require_client=True,
        require_engagement=True,
        additional_exempt_paths=[
            "/api/v1/context/me",
            "/api/v1/clients/default",
            "/api/v1/clients",
            "/api/v1/context/clients",
            "/api/v1/context/engagements",
            "/api/v1/context-establishment/clients",
            "/api/v1/context-establishment/engagements",
            "/api/v1/admin/clients/dashboard/stats",
            "/api/v1/admin/engagements/dashboard/stats",
            "/api/v1/auth/admin/dashboard-stats",
            "/api/v1/admin/",
            "/api/v1/auth/admin/",
            "/api/v1/data-import/latest-import",
            "/api/v1/data-import/status",
            "/api/v1/unified-discovery/flow/health",
            "/api/v1/unified-discovery/flow/status",
        ],
    )
    app.add_middleware(RequestLoggingMiddleware, excluded_paths=["/health"])
    app.add_middleware(AdaptiveRateLimitMiddleware)
    app.add_middleware(SecurityAuditMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("✅ Core middlewares added")

    # Optional cache middleware
    try:
        if settings.REDIS_ENABLED:
            from app.middleware.cache_middleware import (
                CacheInstrumentationMiddleware,
                CacheMiddleware,
            )

            app.add_middleware(CacheMiddleware)
            app.add_middleware(CacheInstrumentationMiddleware)
            logger.info("✅ Redis cache middleware added")
    except Exception as e:  # pragma: no cover
        logger.warning("Could not add cache middleware: %s", e)

    # Flow ID requirement middleware for discovery endpoints
    try:
        from app.middleware.flow_id_middleware import FlowIDRequirementMiddleware

        app.add_middleware(
            FlowIDRequirementMiddleware,
            exempt_paths=[
                "/api/v1/unified-discovery/flow/create",
                "/api/v1/unified-discovery/flow/list",
                # Legacy discovery endpoints removed - use MFO or unified-discovery
            ],
        )
        logger.info("✅ Flow ID requirement middleware added for discovery endpoints")
    except Exception as e:  # pragma: no cover
        logger.warning("Could not add Flow ID middleware: %s", e)

    # Legacy endpoint guard
    try:
        from app.middleware.legacy_endpoint_guard import (
            LegacyEndpointGuardMiddleware,
        )

        app.add_middleware(LegacyEndpointGuardMiddleware)
        logger.info("✅ Legacy endpoint guard middleware added")
    except Exception as e:  # pragma: no cover
        logger.warning("Could not add legacy endpoint guard: %s", e)
