"""
Structured logging configuration for the AI Modernize Migration Platform.

Provides centralized logging with:
- Request trace IDs for tracking
- Structured context information
- Performance metrics
- Security-aware filtering
"""

import contextvars
import json
import logging
import sys
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

# Context variables for request tracking
request_context = contextvars.ContextVar('request_context', default={})
trace_id_context = contextvars.ContextVar('trace_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Get context information
        context = request_context.get()
        trace_id = trace_id_context.get()
        
        # Build structured log entry
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context if available
        if context:
            log_data["context"] = {
                "client_account_id": context.get("client_account_id"),
                "engagement_id": context.get("engagement_id"),
                "user_id": context.get("user_id"),
                "flow_id": context.get("flow_id"),
            }
        
        # Add extra fields from the record
        if hasattr(record, 'extra'):
            for key, value in record.extra.items():
                if key not in log_data:
                    log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add performance metrics if present
        if hasattr(record, 'duration_ms'):
            log_data["performance"] = {
                "duration_ms": record.duration_ms
            }
        
        return json.dumps(log_data)


class SecurityFilter(logging.Filter):
    """Filter to prevent logging of sensitive information"""
    
    SENSITIVE_FIELDS = {
        'password', 'token', 'api_key', 'secret', 'auth',
        'authorization', 'cookie', 'session', 'credit_card',
        'ssn', 'social_security', 'private_key'
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out records containing sensitive information"""
        # Check message for sensitive keywords
        message_lower = record.getMessage().lower()
        for field in self.SENSITIVE_FIELDS:
            if field in message_lower:
                # Redact sensitive parts
                record.msg = self._redact_sensitive(record.msg, field)
        
        # Check extra fields
        if hasattr(record, 'extra'):
            for key in list(record.extra.keys()):
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    record.extra[key] = "[REDACTED]"
        
        return True
    
    def _redact_sensitive(self, message: str, field: str) -> str:
        """Redact sensitive information from message"""
        import re
        # Simple redaction - replace the value after the field name
        pattern = rf"({field}['\"]?\s*[:=]\s*)(['\"]?)([^'\"{{}}\\s]+)(['\"]?)"
        return re.sub(pattern, r'\1\2[REDACTED]\4', message, flags=re.IGNORECASE)


class ContextLogger:
    """Logger that automatically includes context information"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """Log with automatic context injection"""
        extra = kwargs.get('extra', {})
        
        # Add trace ID if available
        trace_id = trace_id_context.get()
        if trace_id:
            extra['trace_id'] = trace_id
        
        # Add request context if available
        context = request_context.get()
        if context:
            extra.update({
                f"ctx_{k}": v for k, v in context.items()
                if k in ['client_account_id', 'engagement_id', 'user_id', 'flow_id']
            })
        
        kwargs['extra'] = extra
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, exc_info=True, **kwargs):
        """Log exception with traceback"""
        kwargs['exc_info'] = exc_info
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)


def get_logger(name: str) -> ContextLogger:
    """Get a context-aware logger instance"""
    return ContextLogger(name)


def set_trace_id(trace_id: str):
    """Set the trace ID for the current context"""
    trace_id_context.set(trace_id)


def set_request_context(
    client_account_id: Optional[int] = None,
    engagement_id: Optional[int] = None,
    user_id: Optional[str] = None,
    flow_id: Optional[str] = None,
    **kwargs
):
    """Set request context for logging"""
    context = request_context.get().copy()
    
    if client_account_id is not None:
        context['client_account_id'] = client_account_id
    if engagement_id is not None:
        context['engagement_id'] = engagement_id
    if user_id is not None:
        context['user_id'] = user_id
    if flow_id is not None:
        context['flow_id'] = flow_id
    
    # Add any additional context
    context.update(kwargs)
    
    request_context.set(context)


def log_performance(func):
    """Decorator to log function performance"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        logger = get_logger(func.__module__)
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                f"{func.__name__} completed",
                extra={
                    'duration_ms': duration_ms,
                    'function': func.__name__,
                    'status': 'success'
                }
            )
            
            return result
        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(
                f"{func.__name__} failed: {str(e)}",
                extra={
                    'duration_ms': duration_ms,
                    'function': func.__name__,
                    'status': 'error',
                    'error_type': type(e).__name__
                }
            )
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        logger = get_logger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                f"{func.__name__} completed",
                extra={
                    'duration_ms': duration_ms,
                    'function': func.__name__,
                    'status': 'success'
                }
            )
            
            return result
        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(
                f"{func.__name__} failed: {str(e)}",
                extra={
                    'duration_ms': duration_ms,
                    'function': func.__name__,
                    'status': 'error',
                    'error_type': type(e).__name__
                }
            )
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def configure_logging(
    level: str = "INFO",
    format: str = "json",
    enable_security_filter: bool = True
):
    """
    Configure application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format ('json' or 'text')
        enable_security_filter: Whether to enable security filtering
    """
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on format
    if format == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    # Add security filter if enabled
    if enable_security_filter:
        handler.addFilter(SecurityFilter())
    
    # Add handler to root logger
    root_logger.addHandler(handler)
    
    # Configure specific loggers
    _configure_library_loggers()
    
    logger = get_logger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": level,
            "format": format,
            "security_filter": enable_security_filter
        }
    )


def _configure_library_loggers():
    """Configure logging levels for third-party libraries"""
    # Suppress verbose logs from libraries
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("h11").setLevel(logging.ERROR)
    
    # SQL logs
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    # LLM-related logs
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.ERROR)
    logging.getLogger("deepinfra").setLevel(logging.WARNING)
    
    # Keep application logs visible
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)