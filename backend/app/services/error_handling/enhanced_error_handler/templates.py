"""
Enhanced Error Handler - Message Templates

Message templates for different error categories and user audiences.
Provides contextual error messages and recovery suggestions.

Key Features:
- Audience-specific message templates
- Category-based error messaging
- Recovery suggestion templates
- Internationalization-ready structure
"""

from typing import Any, Dict

from .base import ErrorCategory, UserAudience


def get_message_templates() -> Dict[ErrorCategory, Dict[UserAudience, Dict[str, Any]]]:
    """Get error message templates for different categories and audiences"""
    return {
        ErrorCategory.AUTHENTICATION: {
            UserAudience.END_USER: {
                "message": "Authentication failed. Please check your credentials.",
                "suggestions": [
                    "Verify your username and password",
                    "Check if your account is locked",
                    "Try resetting your password if needed",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Authentication service error detected.",
                "suggestions": [
                    "Check authentication service health",
                    "Verify user account status",
                    "Review authentication logs",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Authentication error in auth service pipeline.",
                "suggestions": [
                    "Check auth service connectivity",
                    "Verify JWT token validation",
                    "Review authentication middleware logs",
                ],
            },
        },
        ErrorCategory.CACHE: {
            UserAudience.END_USER: {
                "message": "System is running slower than usual. Please be patient.",
                "suggestions": [
                    "Your request is being processed",
                    "Performance will improve shortly",
                    "Try refreshing the page if needed",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Cache service degradation detected.",
                "suggestions": [
                    "Check Redis service status",
                    "Review cache performance metrics",
                    "Consider manual cache warmup",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Cache layer failure, fallback systems active.",
                "suggestions": [
                    "Check Redis connectivity and health",
                    "Review cache miss rates",
                    "Verify fallback cache configuration",
                ],
            },
        },
        ErrorCategory.DATABASE: {
            UserAudience.END_USER: {
                "message": "We're experiencing technical difficulties. Please try again in a moment.",
                "suggestions": [
                    "Your data is safe",
                    "Try your request again in a few minutes",
                    "Contact support if the issue persists",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Database service error detected.",
                "suggestions": [
                    "Check database connectivity",
                    "Review database performance metrics",
                    "Verify backup systems are functioning",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Database connection or query error.",
                "suggestions": [
                    "Check database connection pool",
                    "Review slow query logs",
                    "Verify database schema integrity",
                ],
            },
        },
        ErrorCategory.SERVICE_UNAVAILABLE: {
            UserAudience.END_USER: {
                "message": "Service temporarily unavailable. We're working to restore it.",
                "suggestions": [
                    "Please try again in a few minutes",
                    "Check our status page for updates",
                    "Your data and settings are preserved",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Critical service unavailability detected.",
                "suggestions": [
                    "Review service health dashboard",
                    "Check if failover systems are active",
                    "Consider manual service restart",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Service circuit breaker activated or service down.",
                "suggestions": [
                    "Check service health endpoints",
                    "Review circuit breaker status",
                    "Verify service dependencies",
                ],
            },
        },
        ErrorCategory.NETWORK: {
            UserAudience.END_USER: {
                "message": "Connection timeout. Please check your internet connection.",
                "suggestions": [
                    "Check your internet connection",
                    "Try refreshing the page",
                    "Wait a moment and try again",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Network connectivity issues detected.",
                "suggestions": [
                    "Check network infrastructure",
                    "Review network monitoring alerts",
                    "Verify external service connectivity",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Network timeout or connectivity error.",
                "suggestions": [
                    "Check network configuration",
                    "Review timeout settings",
                    "Verify DNS resolution",
                ],
            },
        },
        ErrorCategory.AUTHORIZATION: {
            UserAudience.END_USER: {
                "message": "You don't have permission to access this resource.",
                "suggestions": [
                    "Contact your administrator for access",
                    "Verify you're logged into the correct account",
                    "Check if your permissions have changed",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Authorization failure detected.",
                "suggestions": [
                    "Review user permissions and roles",
                    "Check authorization service health",
                    "Verify role-based access control rules",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Authorization check failed in security pipeline.",
                "suggestions": [
                    "Verify permission validation logic",
                    "Check role assignment mechanisms",
                    "Review authorization middleware logs",
                ],
            },
        },
        ErrorCategory.VALIDATION: {
            UserAudience.END_USER: {
                "message": "The information provided is invalid. Please check your input.",
                "suggestions": [
                    "Review the required fields",
                    "Check data format requirements",
                    "Ensure all required fields are filled",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Data validation error detected.",
                "suggestions": [
                    "Review validation rules configuration",
                    "Check data quality standards",
                    "Verify input format requirements",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Input validation failed in data processing pipeline.",
                "suggestions": [
                    "Check validation schema definitions",
                    "Review input sanitization logic",
                    "Verify data type constraints",
                ],
            },
        },
        ErrorCategory.RATE_LIMITING: {
            UserAudience.END_USER: {
                "message": "Too many requests. Please wait a moment before trying again.",
                "suggestions": [
                    "Wait a few seconds before retrying",
                    "Reduce the frequency of your requests",
                    "Contact support if you need higher limits",
                ],
            },
            UserAudience.ADMIN_USER: {
                "message": "Rate limiting activated for user or service.",
                "suggestions": [
                    "Review rate limiting policies",
                    "Check if limits need adjustment",
                    "Monitor abuse patterns",
                ],
            },
            UserAudience.DEVELOPER: {
                "message": "Rate limit exceeded in API throttling system.",
                "suggestions": [
                    "Review API rate limiting configuration",
                    "Implement exponential backoff",
                    "Check rate limit headers and status codes",
                ],
            },
        },
    }
