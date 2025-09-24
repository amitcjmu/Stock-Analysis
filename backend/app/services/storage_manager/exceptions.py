"""
Storage Manager Exceptions

Storage-specific exceptions for the StorageManager system.
These exceptions provide fine-grained error handling for different
storage operations and backend failures.
"""

from typing import Any, Callable, Dict, Optional


class StorageError(Exception):
    """Base exception for all storage-related errors"""

    def __init__(
        self,
        message: str,
        operation_id: Optional[str] = None,
        storage_type: Optional[str] = None,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.operation_id = operation_id
        self.storage_type = storage_type
        self.key = key
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "operation_id": self.operation_id,
            "storage_type": self.storage_type,
            "key": self.key,
            "metadata": self.metadata,
        }


class StorageBackendError(StorageError):
    """Exception raised when a storage backend fails"""

    def __init__(
        self,
        message: str,
        backend_name: str,
        operation_id: Optional[str] = None,
        original_error: Optional[Exception] = None,
        **kwargs,
    ):
        super().__init__(message, operation_id=operation_id, **kwargs)
        self.backend_name = backend_name
        self.original_error = original_error

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.original_error:
            return f"{base_msg} (Backend: {self.backend_name}, Original: {self.original_error})"
        return f"{base_msg} (Backend: {self.backend_name})"


class StorageConnectionError(StorageBackendError):
    """Exception raised when connection to storage backend fails"""

    def __init__(
        self, backend_name: str, connection_details: Optional[str] = None, **kwargs
    ):
        message = f"Failed to connect to {backend_name} storage backend"
        if connection_details:
            message += f": {connection_details}"
        super().__init__(message, backend_name=backend_name, **kwargs)


class StorageTimeoutError(StorageError):
    """Exception raised when storage operation times out"""

    def __init__(
        self,
        message: str,
        timeout_duration: float,
        operation_type: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.timeout_duration = timeout_duration
        self.operation_type = operation_type

    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"{base_msg} (Timeout: {self.timeout_duration}s, Operation: {self.operation_type})"


class StorageCapacityError(StorageError):
    """Exception raised when storage capacity limits are exceeded"""

    def __init__(self, message: str, current_size: int, max_size: int, **kwargs):
        super().__init__(message, **kwargs)
        self.current_size = current_size
        self.max_size = max_size

    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"{base_msg} (Used: {self.current_size}/{self.max_size})"


class StorageValidationError(StorageError):
    """Exception raised when storage operation validation fails"""

    def __init__(
        self, message: str, validation_rules: Optional[Dict[str, Any]] = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.validation_rules = validation_rules or {}


class StorageSerializationError(StorageError):
    """Exception raised when data serialization/deserialization fails"""

    def __init__(
        self,
        message: str,
        data_type: Optional[str] = None,
        serialization_format: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.data_type = data_type
        self.serialization_format = serialization_format


class StoragePermissionError(StorageError):
    """Exception raised when storage operation lacks permissions"""

    def __init__(
        self,
        message: str,
        required_permission: Optional[str] = None,
        user_context: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.required_permission = required_permission
        self.user_context = user_context


class StorageConfigurationError(StorageError):
    """Exception raised when storage configuration is invalid"""

    def __init__(
        self,
        message: str,
        config_section: Optional[str] = None,
        expected_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.config_section = config_section
        self.expected_config = expected_config or {}


class StorageRetryExhaustedError(StorageError):
    """Exception raised when all retry attempts for an operation are exhausted"""

    def __init__(
        self,
        message: str,
        retry_count: int,
        max_retries: int,
        last_error: Optional[Exception] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.last_error = last_error

    def __str__(self) -> str:
        base_msg = super().__str__()
        msg = f"{base_msg} (Retries: {self.retry_count}/{self.max_retries})"
        if self.last_error:
            msg += f" Last error: {self.last_error}"
        return msg


class StorageIntegrityError(StorageError):
    """Exception raised when storage data integrity check fails"""

    def __init__(
        self,
        message: str,
        expected_checksum: Optional[str] = None,
        actual_checksum: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.expected_checksum = expected_checksum
        self.actual_checksum = actual_checksum


class StorageQueueFullError(StorageCapacityError):
    """Exception raised when storage operation queue is full"""

    def __init__(self, queue_type: str, current_size: int, max_size: int, **kwargs):
        message = f"Storage {queue_type} queue is full"
        super().__init__(
            message, current_size=current_size, max_size=max_size, **kwargs
        )
        self.queue_type = queue_type


# Exception utilities
def wrap_storage_exception(
    func_name: str,
    storage_type: Optional[str] = None,
    operation_id: Optional[str] = None,
    key: Optional[str] = None,
) -> Callable:
    """
    Decorator factory to wrap functions with storage exception handling.

    Args:
        func_name: Name of the function being wrapped
        storage_type: Type of storage being accessed
        operation_id: ID of the operation being performed
        key: Storage key being accessed

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except StorageError:
                # Re-raise storage errors as-is
                raise
            except ConnectionError as e:
                raise StorageConnectionError(
                    backend_name=storage_type or "unknown",
                    connection_details=str(e),
                    operation_id=operation_id,
                    key=key,
                    original_error=e,
                )
            except TimeoutError as e:
                raise StorageTimeoutError(
                    message=f"Timeout in {func_name}",
                    timeout_duration=getattr(e, "timeout", 0),
                    operation_type=func_name,
                    operation_id=operation_id,
                    storage_type=storage_type,
                    key=key,
                )
            except PermissionError as e:
                raise StoragePermissionError(
                    message=f"Permission denied in {func_name}",
                    operation_id=operation_id,
                    storage_type=storage_type,
                    key=key,
                    original_error=e,
                )
            except (ValueError, TypeError) as e:
                raise StorageValidationError(
                    message=f"Validation error in {func_name}: {e}",
                    operation_id=operation_id,
                    storage_type=storage_type,
                    key=key,
                )
            except Exception as e:
                raise StorageError(
                    message=f"Unexpected error in {func_name}: {e}",
                    operation_id=operation_id,
                    storage_type=storage_type,
                    key=key,
                    metadata={"original_error_type": type(e).__name__},
                )

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
