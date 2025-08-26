import logging
import os
from fastapi.middleware.cors import CORSMiddleware


def add_cors(app, settings):
    def get_cors_origins():
        cors_origins = []
        env = getattr(settings, "ENVIRONMENT", "development").lower()
        is_dev = env in ["development", "dev", "local", "localhost"]

        if is_dev or env not in ["production", "prod"]:
            cors_origins.extend(
                [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://localhost:8080",
                    "http://localhost:8081",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:8080",
                    "http://127.0.0.1:8081",
                ]
            )
        else:
            cors_origins.extend(
                [
                    "https://aiforce-assess.vercel.app",
                    "https://migrate-ui-orchestrator-production.up.railway.app",
                ]
            )

        if (
            os.getenv("RAILWAY_ENVIRONMENT")
            or os.getenv("RAILWAY_PROJECT_NAME")
            or os.getenv("PORT")
            or "railway.app" in os.getenv("DATABASE_URL", "")
        ):
            cors_origins.extend(
                [
                    "https://aiforce-assess.vercel.app",
                    "https://migrate-ui-orchestrator-production.up.railway.app",
                ]
            )

        if hasattr(settings, "FRONTEND_URL") and settings.FRONTEND_URL:
            cors_origins.append(settings.FRONTEND_URL)

        if hasattr(settings, "allowed_origins_list"):
            cors_origins.extend(settings.allowed_origins_list)

        if (
            (
                os.getenv("DATABASE_URL")
                and "railway.app" in os.getenv("DATABASE_URL", "")
            )
            or os.getenv("PORT")
            or os.getenv("RAILWAY_ENVIRONMENT")
            or env == "production"
        ):
            vercel_domain = "https://aiforce-assess.vercel.app"
            if vercel_domain not in cors_origins:
                cors_origins.append(vercel_domain)

        return list(set(filter(None, cors_origins)))

    origins = get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Client-Account-ID",
            "X-Client-ID",
            "X-Engagement-ID",
            "X-Trace-ID",
            "X-Request-ID",
            "X-User-ID",
            "X-User-Role",
            "X-Flow-ID",
            "Cache-Control",
            "Pragma",
            "Accept",
            "Accept-Language",
            "Accept-Encoding",
            "Content-Language",
        ],
        expose_headers=["X-Trace-ID", "X-RateLimit-Limit", "X-RateLimit-Reset"],
        max_age=3600,
    )
    logging.getLogger(__name__).info("✅ CORS middleware added")
