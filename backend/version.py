"""
AI Modernize Migration Platform - Version Information
"""

__version__ = "0.2.0"
__title__ = "AI Modernize Migration Platform"
__description__ = (
    "AI-powered cloud migration management platform with intelligent automation"
)
__author__ = "AI Modernize Migration Team"
__license__ = "MIT"
__copyright__ = "Copyright 2025 AI Modernize Migration Platform"

# Release Information
RELEASE_NAME = "Sprint 1 Complete - Backend & Docker"
RELEASE_DATE = "2025-01-27"
RELEASE_NOTES = """
Major Release - Complete Backend Implementation & Docker Containerization

This release marks the completion of Sprint 1 with:
- Complete FastAPI backend with CrewAI integration
- Full Docker containerization with multi-service setup
- PostgreSQL database with comprehensive models
- WebSocket support for real-time updates
- Fixed port assignments and development environment
- Comprehensive documentation and setup automation
"""

# API Information
API_VERSION = "v1"
API_TITLE = f"{__title__} API"
API_DESCRIPTION = f"{__description__} - REST API"

# Build Information
BUILD_INFO = {
    "version": __version__,
    "release_name": RELEASE_NAME,
    "release_date": RELEASE_DATE,
    "api_version": API_VERSION,
    "python_version": "3.11+",
    "framework": "FastAPI",
    "database": "PostgreSQL",
    "ai_framework": "CrewAI",
}
