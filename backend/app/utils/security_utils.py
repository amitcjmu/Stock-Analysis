"""
Security Utilities
Provides input sanitization and security validation functions.
"""

import re
import html
import json
from typing import Any, Dict, List, Union, Optional
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Utilities for sanitizing user input to prevent security vulnerabilities."""
    
    # XSS patterns to remove
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<applet[^>]*>.*?</applet>',
        r'<meta[^>]*>',
        r'<link[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'on\w+\s*=',
        r'expression\s*\(',
        r'@import',
        r'behaviour\s*:',
        r'-moz-binding',
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r'(\bunion\b.*\bselect\b)',
        r'(\bselect\b.*\bfrom\b)',
        r'(\binsert\b.*\binto\b)',
        r'(\bupdate\b.*\bset\b)',
        r'(\bdelete\b.*\bfrom\b)',
        r'(\bdrop\b.*\btable\b)',
        r'(\balter\b.*\btable\b)',
        r'(\bcreate\b.*\btable\b)',
        r'(\btruncate\b.*\btable\b)',
        r'(\bexec\b.*\()',
        r'(\bexecute\b.*\()',
        r'(\bsp_\w+)',
        r'(\bxp_\w+)',
    ]
    
    # Command injection patterns
    COMMAND_PATTERNS = [
        r'(\||&&|;|`|\$\()',
        r'(\bcat\b|\bls\b|\bps\b|\bwhoami\b)',
        r'(\bchmod\b|\bchown\b|\bsu\b|\bsudo\b)',
        r'(\bwget\b|\bcurl\b|\bftp\b|\bscp\b)',
        r'(\bnetcat\b|\bnc\b|\btelnet\b)',
        r'(\bping\b|\bnslookup\b|\bdig\b)',
        r'(\bfind\b|\bgrep\b|\bawk\b|\bsed\b)',
        r'(\bpython\b|\bperl\b|\bruby\b|\bnode\b)',
        r'(\bsh\b|\bbash\b|\bzsh\b|\bcsh\b)',
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 10000) -> str:
        """
        Sanitize string input to prevent XSS and other attacks.
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not value or not isinstance(value, str):
            return ""
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        # HTML escape
        value = html.escape(value)
        
        # Remove XSS patterns
        for pattern in InputSanitizer.XSS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove null bytes and other dangerous characters
        value = value.replace('\x00', '')
        value = value.replace('\r\n', '\n')
        value = value.replace('\r', '\n')
        
        # Remove excessive whitespace
        value = re.sub(r'\s+', ' ', value)
        
        return value.strip()
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized dictionary
        """
        if max_depth <= 0:
            logger.warning("Maximum sanitization depth reached")
            return {}
        
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            safe_key = InputSanitizer.sanitize_string(str(key), max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[safe_key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = InputSanitizer.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[safe_key] = InputSanitizer.sanitize_list(value, max_depth - 1)
            elif isinstance(value, (int, float, bool)):
                sanitized[safe_key] = value
            elif value is None:
                sanitized[safe_key] = None
            else:
                # Convert other types to string and sanitize
                sanitized[safe_key] = InputSanitizer.sanitize_string(str(value))
        
        return sanitized
    
    @staticmethod
    def sanitize_list(data: List[Any], max_depth: int = 10) -> List[Any]:
        """
        Recursively sanitize list values.
        
        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized list
        """
        if max_depth <= 0:
            logger.warning("Maximum sanitization depth reached")
            return []
        
        if not isinstance(data, list):
            return []
        
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(InputSanitizer.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(InputSanitizer.sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(InputSanitizer.sanitize_list(item, max_depth - 1))
            elif isinstance(item, (int, float, bool)):
                sanitized.append(item)
            elif item is None:
                sanitized.append(None)
            else:
                sanitized.append(InputSanitizer.sanitize_string(str(item)))
        
        return sanitized
    
    @staticmethod
    def check_sql_injection(value: str) -> bool:
        """
        Check if string contains SQL injection patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if SQL injection patterns found
        """
        if not value or not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        
        for pattern in InputSanitizer.SQL_PATTERNS:
            if re.search(pattern, value_lower):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def check_command_injection(value: str) -> bool:
        """
        Check if string contains command injection patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if command injection patterns found
        """
        if not value or not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        
        for pattern in InputSanitizer.COMMAND_PATTERNS:
            if re.search(pattern, value_lower):
                logger.warning(f"Command injection pattern detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email format
        """
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid URL format
        """
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL validation
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename or not isinstance(filename, str):
            return "untitled"
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[/\\:*?"<>|]', '', filename)
        
        # Remove relative path components
        filename = filename.replace('..', '')
        filename = filename.replace('./', '')
        filename = filename.replace('.\\', '')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        # Ensure not empty
        if not filename.strip():
            filename = "untitled"
        
        return filename.strip()
    
    @staticmethod
    def safe_json_loads(json_string: str) -> Optional[Union[Dict, List]]:
        """
        Safely parse JSON string.
        
        Args:
            json_string: JSON string to parse
            
        Returns:
            Parsed JSON object or None if invalid
        """
        try:
            if not json_string or not isinstance(json_string, str):
                return None
            
            # Limit JSON string length
            if len(json_string) > 100000:  # 100KB limit
                logger.warning("JSON string too large")
                return None
            
            return json.loads(json_string)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Invalid JSON: {e}")
            return None
    
    @staticmethod
    def sanitize_json_input(json_input: str) -> Optional[Union[Dict, List]]:
        """
        Sanitize and parse JSON input.
        
        Args:
            json_input: JSON input string
            
        Returns:
            Sanitized JSON object or None if invalid
        """
        # First sanitize the string
        sanitized_input = InputSanitizer.sanitize_string(json_input)
        
        # Then parse JSON
        parsed_json = InputSanitizer.safe_json_loads(sanitized_input)
        
        if parsed_json is None:
            return None
        
        # Sanitize the parsed JSON
        if isinstance(parsed_json, dict):
            return InputSanitizer.sanitize_dict(parsed_json)
        elif isinstance(parsed_json, list):
            return InputSanitizer.sanitize_list(parsed_json)
        else:
            return parsed_json


class SecurityValidator:
    """Additional security validation utilities."""
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """
        Validate UUID format.
        
        Args:
            uuid_string: UUID string to validate
            
        Returns:
            True if valid UUID format
        """
        if not uuid_string or not isinstance(uuid_string, str):
            return False
        
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, uuid_string.lower()))
    
    @staticmethod
    def validate_integer(value: Any, min_val: int = None, max_val: int = None) -> bool:
        """
        Validate integer value with optional range checking.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            True if valid integer within range
        """
        try:
            int_value = int(value)
            
            if min_val is not None and int_value < min_val:
                return False
            
            if max_val is not None and int_value > max_val:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_float(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """
        Validate float value with optional range checking.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            True if valid float within range
        """
        try:
            float_value = float(value)
            
            if min_val is not None and float_value < min_val:
                return False
            
            if max_val is not None and float_value > max_val:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: List[str] = None) -> bool:
        """
        Check if URL is safe for redirects.
        
        Args:
            url: URL to check
            allowed_hosts: List of allowed hostnames
            
        Returns:
            True if URL is safe for redirects
        """
        if not url or not isinstance(url, str):
            return False
        
        # Check for dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'ftp:']
        url_lower = url.lower()
        
        for protocol in dangerous_protocols:
            if url_lower.startswith(protocol):
                return False
        
        # If allowed hosts specified, check hostname
        if allowed_hosts and url.startswith('http'):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.hostname not in allowed_hosts:
                    return False
            except Exception:
                return False
        
        return True