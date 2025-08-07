"""
Secure Logging Utilities

Provides utilities to mask sensitive data in log messages to prevent
B106 bandit violations and protect PII, UUIDs, and other identifiers.
"""

import re
from typing import Any, Union
from uuid import UUID


def mask_uuid(uuid_value: Union[str, UUID, None]) -> str:
    """
    Mask a UUID or UUID string for logging.
    
    Shows only the last 8 characters with *** prefix.
    
    Args:
        uuid_value: UUID string, UUID object, or None
        
    Returns:
        Masked string (***12345678) or 'None' if input is None
    """
    if uuid_value is None:
        return "None"
    
    uuid_str = str(uuid_value)
    if len(uuid_str) >= 8:
        return f"***{uuid_str[-8:]}"
    return f"***{uuid_str}"


def mask_id(id_value: Union[str, int, UUID, None]) -> str:
    """
    Mask any ID value for logging.
    
    Shows only the last 6-8 characters with *** prefix.
    
    Args:
        id_value: ID of any type or None
        
    Returns:
        Masked string (***123456) or 'None' if input is None
    """
    if id_value is None:
        return "None"
    
    id_str = str(id_value)
    if len(id_str) >= 8:
        return f"***{id_str[-8:]}"
    elif len(id_str) >= 6:
        return f"***{id_str[-6:]}"
    elif len(id_str) >= 4:
        return f"***{id_str[-4:]}"
    return f"***{id_str}"


def mask_email(email: Union[str, None]) -> str:
    """
    Mask email address for logging.
    
    Shows first 3 characters and domain: abc***@domain.com
    
    Args:
        email: Email string or None
        
    Returns:
        Masked email or 'None' if input is None
    """
    if email is None:
        return "None"
    
    if "@" not in email:
        # Not a valid email, just mask as generic string
        return mask_string(email)
    
    local, domain = email.split("@", 1)
    if len(local) <= 3:
        return f"***@{domain}"
    return f"{local[:3]}***@{domain}"


def mask_string(value: Union[str, None], show_chars: int = 4) -> str:
    """
    Mask a string value for logging.
    
    Shows only the last few characters with *** prefix.
    
    Args:
        value: String to mask or None
        show_chars: Number of characters to show at the end
        
    Returns:
        Masked string or 'None' if input is None
    """
    if value is None:
        return "None"
    
    if len(value) <= show_chars:
        return f"***{value}"
    return f"***{value[-show_chars:]}"


def mask_database_url(db_url: Union[str, None]) -> str:
    """
    Mask database URL for logging.
    
    Removes password and shows only protocol and host.
    
    Args:
        db_url: Database URL string or None
        
    Returns:
        Masked database URL or 'None' if input is None
    """
    if db_url is None:
        return "None"
    
    # Pattern to match database URLs and extract components
    pattern = r'^(.*?)://(.*?):(.*?)@(.*?)/(.*?)(\?.*)?$'
    match = re.match(pattern, db_url)
    
    if match:
        protocol, username, password, host, database, params = match.groups()
        return f"{protocol}://{username}:***@{host}/{database}"
    
    # If pattern doesn't match, just mask the whole thing
    return "***DATABASE_URL***"


def mask_token(token: Union[str, None], show_chars: int = 8) -> str:
    """
    Mask authentication token for logging.
    
    Shows only the last few characters with *** prefix.
    
    Args:
        token: Token string or None
        show_chars: Number of characters to show at the end
        
    Returns:
        Masked token or 'None' if input is None
    """
    if token is None:
        return "None"
    
    if len(token) <= show_chars:
        return "***TOKEN***"
    return f"***{token[-show_chars:]}"


def secure_format(message: str, **kwargs: Any) -> str:
    """
    Secure string formatting that automatically masks sensitive data.
    
    This function can be used as a drop-in replacement for f-strings
    when logging potentially sensitive data.
    
    Args:
        message: Format string with {key} placeholders
        **kwargs: Values to format, will be automatically masked if sensitive
        
    Returns:
        Formatted string with sensitive data masked
    """
    # Known sensitive field patterns
    sensitive_patterns = {
        'id', 'uuid', 'user_id', 'client_id', 'account_id', 'engagement_id',
        'flow_id', 'session_id', 'token', 'key', 'secret', 'password',
        'email', 'database_url', 'connection_string'
    }
    
    formatted_kwargs = {}
    for key, value in kwargs.items():
        key_lower = key.lower()
        
        # Check if this looks like a sensitive field
        is_sensitive = any(pattern in key_lower for pattern in sensitive_patterns)
        
        if is_sensitive:
            if 'email' in key_lower:
                formatted_kwargs[key] = mask_email(value)
            elif any(pattern in key_lower for pattern in ['url', 'connection']):
                formatted_kwargs[key] = mask_database_url(value)
            elif any(pattern in key_lower for pattern in ['token', 'key', 'secret']):
                formatted_kwargs[key] = mask_token(value)
            elif 'id' in key_lower or 'uuid' in key_lower:
                formatted_kwargs[key] = mask_id(value)
            else:
                formatted_kwargs[key] = mask_string(value)
        else:
            formatted_kwargs[key] = value
    
    return message.format(**formatted_kwargs)


# Convenience function for common logging scenarios
def log_user_action(user_id: Union[str, UUID, None], action: str) -> str:
    """Log user action with masked user ID."""
    return f"User {mask_id(user_id)} performed action: {action}"


def log_flow_action(flow_id: Union[str, UUID, None], action: str) -> str:
    """Log flow action with masked flow ID."""
    return f"Flow {mask_id(flow_id)} {action}"


def log_database_operation(operation: str, table: str, record_id: Union[str, UUID, None] = None) -> str:
    """Log database operation with masked record ID."""
    if record_id:
        return f"Database {operation} on {table} for record {mask_id(record_id)}"
    return f"Database {operation} on {table}"


# Example usage and testing
if __name__ == "__main__":
    # Test the masking functions
    test_uuid = "f1111111-1111-1111-1111-111111111111"
    test_email = "user@example.com"
    test_db_url = "postgresql://user:password@localhost:5432/dbname"
    
    print("Testing secure logging utilities:")
    print(f"UUID: {mask_uuid(test_uuid)}")
    print(f"Email: {mask_email(test_email)}")
    print(f"DB URL: {mask_database_url(test_db_url)}")
    print(f"Formatted: {secure_format('User {user_id} accessed flow {flow_id}', user_id=test_uuid, flow_id=test_uuid)}")