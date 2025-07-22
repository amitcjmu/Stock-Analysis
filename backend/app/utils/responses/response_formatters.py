"""
Response formatting utilities for consistent data presentation.
Provides formatting functions for common data types and response sanitization.
"""

import logging
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """
    Utility class for formatting response data consistently.
    """
    
    @staticmethod
    def format_datetime(dt: Union[datetime, date, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
        """
        Format datetime objects to string.
        
        Args:
            dt: Datetime object, date object, or ISO string
            format_str: Format string for output
            
        Returns:
            Formatted datetime string or None
        """
        if dt is None:
            return None
        
        try:
            if isinstance(dt, str):
                # Try to parse ISO format
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            elif isinstance(dt, date) and not isinstance(dt, datetime):
                # Convert date to datetime
                dt = datetime.combine(dt, datetime.min.time())
            
            return dt.strftime(format_str)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to format datetime {dt}: {e}")
            return str(dt) if dt else None
    
    @staticmethod
    def format_currency(amount: Union[float, Decimal, int], currency: str = "USD", 
                       locale: str = "en_US") -> str:
        """
        Format currency amounts.
        
        Args:
            amount: Monetary amount
            currency: Currency code
            locale: Locale for formatting
            
        Returns:
            Formatted currency string
        """
        if amount is None:
            return "N/A"
        
        try:
            # Convert to decimal for precision
            if isinstance(amount, (int, float)):
                amount = Decimal(str(amount))
            
            # Basic currency formatting
            if currency == "USD":
                return f"${amount:,.2f}"
            elif currency == "EUR":
                return f"€{amount:,.2f}"
            elif currency == "GBP":
                return f"£{amount:,.2f}"
            else:
                return f"{amount:,.2f} {currency}"
        except Exception as e:
            logger.warning(f"Failed to format currency {amount}: {e}")
            return str(amount)
    
    @staticmethod
    def format_percentage(value: Union[float, Decimal, int], decimals: int = 2) -> str:
        """
        Format percentage values.
        
        Args:
            value: Percentage value (0-100 or 0-1)
            decimals: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        if value is None:
            return "N/A"
        
        try:
            # Convert to float
            if isinstance(value, Decimal):
                value = float(value)
            
            # Determine if value is in 0-1 or 0-100 range
            if value <= 1.0:
                value *= 100
            
            return f"{value:.{decimals}f}%"
        except Exception as e:
            logger.warning(f"Failed to format percentage {value}: {e}")
            return str(value)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted file size string
        """
        if size_bytes is None:
            return "N/A"
        
        if size_bytes == 0:
            return "0 B"
        
        try:
            size_bytes = int(size_bytes)
            size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
            
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024
                i += 1
            
            return f"{size_bytes:.1f} {size_names[i]}"
        except Exception as e:
            logger.warning(f"Failed to format file size {size_bytes}: {e}")
            return str(size_bytes)
    
    @staticmethod
    def format_duration(seconds: Union[int, float]) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds is None:
            return "N/A"
        
        try:
            seconds = float(seconds)
            
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.1f}m"
            elif seconds < 86400:
                hours = seconds / 3600
                return f"{hours:.1f}h"
            else:
                days = seconds / 86400
                return f"{days:.1f}d"
        except Exception as e:
            logger.warning(f"Failed to format duration {seconds}: {e}")
            return str(seconds)
    
    @staticmethod
    def format_number(value: Union[int, float, Decimal], decimals: Optional[int] = None) -> str:
        """
        Format numbers with thousand separators.
        
        Args:
            value: Number to format
            decimals: Number of decimal places (None for auto)
            
        Returns:
            Formatted number string
        """
        if value is None:
            return "N/A"
        
        try:
            if decimals is not None:
                return f"{value:,.{decimals}f}"
            elif isinstance(value, int):
                return f"{value:,}"
            else:
                return f"{value:,.2f}"
        except Exception as e:
            logger.warning(f"Failed to format number {value}: {e}")
            return str(value)

def sanitize_response_data(data: Any, max_string_length: int = 10000) -> Any:
    """
    Sanitize response data to prevent XSS and limit size.
    
    Args:
        data: Data to sanitize
        max_string_length: Maximum length for string values
        
    Returns:
        Sanitized data
    """
    if data is None:
        return None
    
    if isinstance(data, str):
        # Truncate long strings
        if len(data) > max_string_length:
            data = data[:max_string_length] + "..."
        
        # Basic XSS prevention
        data = (data.replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("&", "&amp;")
                   .replace("\"", "&quot;")
                   .replace("'", "&#x27;"))
        
        return data
    
    elif isinstance(data, dict):
        return {key: sanitize_response_data(value, max_string_length) 
                for key, value in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_response_data(item, max_string_length) 
                for item in data]
    
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    
    elif isinstance(data, Decimal):
        return float(data)
    
    else:
        return data

def mask_sensitive_data(data: Any, sensitive_fields: Optional[List[str]] = None) -> Any:
    """
    Mask sensitive data in response.
    
    Args:
        data: Data to mask
        sensitive_fields: List of field names to mask
        
    Returns:
        Data with sensitive fields masked
    """
    if sensitive_fields is None:
        sensitive_fields = [
            "password", "secret", "token", "key", "api_key", "auth_token",
            "credit_card", "ssn", "social_security", "phone", "email"
        ]
    
    def mask_value(value: str) -> str:
        """Mask a sensitive value."""
        if len(value) <= 4:
            return "*" * len(value)
        else:
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if field should be masked
            if any(sensitive_field in key_lower for sensitive_field in sensitive_fields):
                if isinstance(value, str) and value:
                    result[key] = mask_value(value)
                else:
                    result[key] = "***"
            else:
                result[key] = mask_sensitive_data(value, sensitive_fields)
        
        return result
    
    elif isinstance(data, list):
        return [mask_sensitive_data(item, sensitive_fields) for item in data]
    
    else:
        return data

def apply_response_filters(data: Any, filters: Optional[Dict[str, Any]] = None) -> Any:
    """
    Apply filters to response data.
    
    Args:
        data: Data to filter
        filters: Filter configuration
        
    Returns:
        Filtered data
    """
    if filters is None:
        return data
    
    # Apply field selection
    if "fields" in filters and isinstance(data, dict):
        fields = filters["fields"]
        if isinstance(fields, str):
            fields = [f.strip() for f in fields.split(",")]
        
        if fields:
            return {key: value for key, value in data.items() if key in fields}
    
    # Apply field exclusion
    if "exclude_fields" in filters and isinstance(data, dict):
        exclude_fields = filters["exclude_fields"]
        if isinstance(exclude_fields, str):
            exclude_fields = [f.strip() for f in exclude_fields.split(",")]
        
        if exclude_fields:
            return {key: value for key, value in data.items() if key not in exclude_fields}
    
    return data

# Convenience functions
def format_datetime(dt: Union[datetime, date, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """Format datetime objects to string."""
    return ResponseFormatter.format_datetime(dt, format_str)

def format_currency(amount: Union[float, Decimal, int], currency: str = "USD") -> str:
    """Format currency amounts."""
    return ResponseFormatter.format_currency(amount, currency)

def format_percentage(value: Union[float, Decimal, int], decimals: int = 2) -> str:
    """Format percentage values."""
    return ResponseFormatter.format_percentage(value, decimals)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    return ResponseFormatter.format_file_size(size_bytes)

def format_duration(seconds: Union[int, float]) -> str:
    """Format duration in human-readable format."""
    return ResponseFormatter.format_duration(seconds)

def format_number(value: Union[int, float, Decimal], decimals: Optional[int] = None) -> str:
    """Format numbers with thousand separators."""
    return ResponseFormatter.format_number(value, decimals)