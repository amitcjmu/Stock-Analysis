"""
Base validators and common validation functions.
Provides reusable validation patterns for different data types.
"""

import json
import logging
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseValidator(ABC):
    """Abstract base validator class."""

    def __init__(self, error_message: Optional[str] = None):
        self.error_message = error_message

    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """Validate a value."""
        pass

    def __call__(self, value: Any) -> ValidationResult:
        """Allow validator to be called directly."""
        return self.validate(value)


class EmailValidator(BaseValidator):
    """Email address validator."""

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __init__(self, allow_empty: bool = False, error_message: Optional[str] = None):
        super().__init__(error_message or "Invalid email address")
        self.allow_empty = allow_empty

    def validate(self, value: Any) -> ValidationResult:
        """Validate email address."""
        if value is None or value == "":
            if self.allow_empty:
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message="Email address is required",
                    error_code="EMAIL_REQUIRED",
                )

        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message="Email must be a string",
                error_code="EMAIL_INVALID_TYPE",
            )

        if not self.EMAIL_REGEX.match(value):
            return ValidationResult(
                is_valid=False,
                error_message=self.error_message,
                error_code="EMAIL_INVALID_FORMAT",
                suggestions=["Check email format (e.g., user@example.com)"],
            )

        # Additional checks
        if len(value) > 254:
            return ValidationResult(
                is_valid=False,
                error_message="Email address is too long",
                error_code="EMAIL_TOO_LONG",
            )

        return ValidationResult(is_valid=True)


class URLValidator(BaseValidator):
    """URL validator."""

    URL_REGEX = re.compile(
        r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$"
    )

    def __init__(
        self, require_https: bool = False, error_message: Optional[str] = None
    ):
        super().__init__(error_message or "Invalid URL")
        self.require_https = require_https

    def validate(self, value: Any) -> ValidationResult:
        """Validate URL."""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message="URL must be a string",
                error_code="URL_INVALID_TYPE",
            )

        if not self.URL_REGEX.match(value):
            return ValidationResult(
                is_valid=False,
                error_message=self.error_message,
                error_code="URL_INVALID_FORMAT",
                suggestions=["Check URL format (e.g., https://example.com)"],
            )

        if self.require_https and not value.startswith("https://"):
            return ValidationResult(
                is_valid=False,
                error_message="HTTPS is required",
                error_code="URL_HTTPS_REQUIRED",
            )

        return ValidationResult(is_valid=True)


class IPAddressValidator(BaseValidator):
    """IP address validator."""

    IPv4_REGEX = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    def __init__(self, version: int = 4, error_message: Optional[str] = None):
        super().__init__(error_message or f"Invalid IPv{version} address")
        self.version = version

    def validate(self, value: Any) -> ValidationResult:
        """Validate IP address."""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message="IP address must be a string",
                error_code="IP_INVALID_TYPE",
            )

        if self.version == 4:
            if not self.IPv4_REGEX.match(value):
                return ValidationResult(
                    is_valid=False,
                    error_message=self.error_message,
                    error_code="IP_INVALID_FORMAT",
                    suggestions=["Check IPv4 format (e.g., 192.168.1.1)"],
                )
        else:
            # IPv6 validation would be more complex
            return ValidationResult(
                is_valid=False,
                error_message="IPv6 validation not implemented",
                error_code="IP_VERSION_UNSUPPORTED",
            )

        return ValidationResult(is_valid=True)


class DateValidator(BaseValidator):
    """Date validator."""

    def __init__(
        self,
        date_format: str = "%Y-%m-%d",
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
        error_message: Optional[str] = None,
    ):
        super().__init__(
            error_message or f"Invalid date format (expected: {date_format})"
        )
        self.date_format = date_format
        self.min_date = min_date
        self.max_date = max_date

    def validate(self, value: Any) -> ValidationResult:
        """Validate date."""
        if isinstance(value, (date, datetime)):
            parsed_date = value.date() if isinstance(value, datetime) else value
        elif isinstance(value, str):
            try:
                parsed_date = datetime.strptime(value, self.date_format).date()
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    error_message=self.error_message,
                    error_code="DATE_INVALID_FORMAT",
                    suggestions=[f"Use format: {self.date_format}"],
                )
        else:
            return ValidationResult(
                is_valid=False,
                error_message="Date must be a string or date object",
                error_code="DATE_INVALID_TYPE",
            )

        # Check date range
        if self.min_date and parsed_date < self.min_date:
            return ValidationResult(
                is_valid=False,
                error_message=f"Date must be after {self.min_date}",
                error_code="DATE_TOO_EARLY",
            )

        if self.max_date and parsed_date > self.max_date:
            return ValidationResult(
                is_valid=False,
                error_message=f"Date must be before {self.max_date}",
                error_code="DATE_TOO_LATE",
            )

        return ValidationResult(is_valid=True)


class NumericValidator(BaseValidator):
    """Numeric value validator."""

    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        allow_decimal: bool = True,
        error_message: Optional[str] = None,
    ):
        super().__init__(error_message or "Invalid numeric value")
        self.min_value = min_value
        self.max_value = max_value
        self.allow_decimal = allow_decimal

    def validate(self, value: Any) -> ValidationResult:
        """Validate numeric value."""
        try:
            if isinstance(value, str):
                if self.allow_decimal:
                    numeric_value = float(value)
                else:
                    numeric_value = int(value)
            elif isinstance(value, (int, float)):
                numeric_value = value
                if (
                    not self.allow_decimal
                    and isinstance(value, float)
                    and value != int(value)
                ):
                    return ValidationResult(
                        is_valid=False,
                        error_message="Decimal values not allowed",
                        error_code="NUMERIC_DECIMAL_NOT_ALLOWED",
                    )
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message="Value must be numeric",
                    error_code="NUMERIC_INVALID_TYPE",
                )
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_message=self.error_message,
                error_code="NUMERIC_INVALID_FORMAT",
            )

        # Check range
        if self.min_value is not None and numeric_value < self.min_value:
            return ValidationResult(
                is_valid=False,
                error_message=f"Value must be at least {self.min_value}",
                error_code="NUMERIC_TOO_SMALL",
            )

        if self.max_value is not None and numeric_value > self.max_value:
            return ValidationResult(
                is_valid=False,
                error_message=f"Value must be at most {self.max_value}",
                error_code="NUMERIC_TOO_LARGE",
            )

        return ValidationResult(is_valid=True)


class StringValidator(BaseValidator):
    """String validator."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        allowed_chars: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        super().__init__(error_message or "Invalid string value")
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.allowed_chars = set(allowed_chars) if allowed_chars else None

    def validate(self, value: Any) -> ValidationResult:
        """Validate string value."""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message="Value must be a string",
                error_code="STRING_INVALID_TYPE",
            )

        # Check length
        if self.min_length is not None and len(value) < self.min_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"String must be at least {self.min_length} characters",
                error_code="STRING_TOO_SHORT",
            )

        if self.max_length is not None and len(value) > self.max_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"String must be at most {self.max_length} characters",
                error_code="STRING_TOO_LONG",
            )

        # Check pattern
        if self.pattern and not self.pattern.match(value):
            return ValidationResult(
                is_valid=False,
                error_message="String does not match required pattern",
                error_code="STRING_PATTERN_MISMATCH",
            )

        # Check allowed characters
        if self.allowed_chars:
            invalid_chars = set(value) - self.allowed_chars
            if invalid_chars:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"String contains invalid characters: {', '.join(invalid_chars)}",
                    error_code="STRING_INVALID_CHARS",
                )

        return ValidationResult(is_valid=True)


class FileValidator(BaseValidator):
    """File validator."""

    def __init__(
        self,
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: Optional[float] = None,
        check_exists: bool = True,
        error_message: Optional[str] = None,
    ):
        super().__init__(error_message or "Invalid file")
        self.allowed_extensions = (
            [ext.lower() for ext in allowed_extensions] if allowed_extensions else None
        )
        self.max_size_mb = max_size_mb
        self.check_exists = check_exists

    def validate(self, value: Any) -> ValidationResult:
        """Validate file."""
        if not isinstance(value, (str, Path)):
            return ValidationResult(
                is_valid=False,
                error_message="File path must be a string or Path object",
                error_code="FILE_INVALID_TYPE",
            )

        file_path = Path(value)

        # Check if file exists
        if self.check_exists and not file_path.exists():
            return ValidationResult(
                is_valid=False,
                error_message=f"File does not exist: {file_path}",
                error_code="FILE_NOT_FOUND",
            )

        # Check extension
        if self.allowed_extensions:
            file_extension = file_path.suffix.lower()
            if file_extension not in self.allowed_extensions:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File extension not allowed. Allowed: {', '.join(self.allowed_extensions)}",
                    error_code="FILE_EXTENSION_NOT_ALLOWED",
                )

        # Check file size
        if self.max_size_mb and file_path.exists():
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File too large: {file_size_mb:.2f}MB (max: {self.max_size_mb}MB)",
                    error_code="FILE_TOO_LARGE",
                )

        return ValidationResult(is_valid=True)


class JSONValidator(BaseValidator):
    """JSON validator."""

    def __init__(
        self,
        schema: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        super().__init__(error_message or "Invalid JSON")
        self.schema = schema

    def validate(self, value: Any) -> ValidationResult:
        """Validate JSON."""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid JSON: {str(e)}",
                    error_code="JSON_INVALID_FORMAT",
                )
        elif isinstance(value, (dict, list)):
            pass
        else:
            return ValidationResult(
                is_valid=False,
                error_message="Value must be JSON string or dict/list",
                error_code="JSON_INVALID_TYPE",
            )

        # Schema validation would require jsonschema library
        # For now, we just validate that it's valid JSON

        return ValidationResult(is_valid=True)


class UUIDValidator(BaseValidator):
    """UUID validator."""

    def __init__(
        self, version: Optional[int] = None, error_message: Optional[str] = None
    ):
        super().__init__(error_message or "Invalid UUID")
        self.version = version

    def validate(self, value: Any) -> ValidationResult:
        """Validate UUID."""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message="UUID must be a string",
                error_code="UUID_INVALID_TYPE",
            )

        try:
            uuid_obj = uuid.UUID(value)
            if self.version and uuid_obj.version != self.version:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"UUID must be version {self.version}",
                    error_code="UUID_INVALID_VERSION",
                )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message=self.error_message,
                error_code="UUID_INVALID_FORMAT",
            )

        return ValidationResult(is_valid=True)


class PhoneNumberValidator(BaseValidator):
    """Phone number validator."""

    PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")

    def __init__(
        self, require_country_code: bool = False, error_message: Optional[str] = None
    ):
        super().__init__(error_message or "Invalid phone number")
        self.require_country_code = require_country_code

    def validate(self, value: Any) -> ValidationResult:
        """Validate phone number."""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message="Phone number must be a string",
                error_code="PHONE_INVALID_TYPE",
            )

        # Remove common separators
        clean_phone = re.sub(r"[\s\-\(\)]", "", value)

        if not self.PHONE_REGEX.match(clean_phone):
            return ValidationResult(
                is_valid=False,
                error_message=self.error_message,
                error_code="PHONE_INVALID_FORMAT",
                suggestions=["Use format: +1234567890 or 1234567890"],
            )

        if self.require_country_code and not clean_phone.startswith("+"):
            return ValidationResult(
                is_valid=False,
                error_message="Country code is required",
                error_code="PHONE_COUNTRY_CODE_REQUIRED",
            )

        return ValidationResult(is_valid=True)


class PasswordValidator(BaseValidator):
    """Password validator."""

    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        error_message: Optional[str] = None,
    ):
        super().__init__(error_message or "Invalid password")
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special

    def validate(self, value: Any) -> ValidationResult:
        """Validate password."""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message="Password must be a string",
                error_code="PASSWORD_INVALID_TYPE",
            )

        errors = []

        if len(value) < self.min_length:
            errors.append(f"At least {self.min_length} characters")

        if self.require_uppercase and not re.search(r"[A-Z]", value):
            errors.append("At least one uppercase letter")

        if self.require_lowercase and not re.search(r"[a-z]", value):
            errors.append("At least one lowercase letter")

        if self.require_digit and not re.search(r"\d", value):
            errors.append("At least one digit")

        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            errors.append("At least one special character")

        if errors:
            return ValidationResult(
                is_valid=False,
                error_message=f"Password must contain: {', '.join(errors)}",
                error_code="PASSWORD_REQUIREMENTS_NOT_MET",
                suggestions=errors,
            )

        return ValidationResult(is_valid=True)


# Convenience functions
def validate_email(email: str, allow_empty: bool = False) -> ValidationResult:
    """Validate email address."""
    return EmailValidator(allow_empty=allow_empty).validate(email)


def validate_url(url: str, require_https: bool = False) -> ValidationResult:
    """Validate URL."""
    return URLValidator(require_https=require_https).validate(url)


def validate_ip_address(ip: str, version: int = 4) -> ValidationResult:
    """Validate IP address."""
    return IPAddressValidator(version=version).validate(ip)


def validate_date(date_value: Any, date_format: str = "%Y-%m-%d") -> ValidationResult:
    """Validate date."""
    return DateValidator(date_format=date_format).validate(date_value)


def validate_numeric(
    value: Any,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> ValidationResult:
    """Validate numeric value."""
    return NumericValidator(min_value=min_value, max_value=max_value).validate(value)


def validate_string(
    value: Any, min_length: Optional[int] = None, max_length: Optional[int] = None
) -> ValidationResult:
    """Validate string value."""
    return StringValidator(min_length=min_length, max_length=max_length).validate(value)


def validate_file(
    file_path: Any,
    allowed_extensions: Optional[List[str]] = None,
    max_size_mb: Optional[float] = None,
) -> ValidationResult:
    """Validate file."""
    return FileValidator(
        allowed_extensions=allowed_extensions, max_size_mb=max_size_mb
    ).validate(file_path)


def validate_json(json_value: Any) -> ValidationResult:
    """Validate JSON."""
    return JSONValidator().validate(json_value)


def validate_uuid(uuid_value: Any, version: Optional[int] = None) -> ValidationResult:
    """Validate UUID."""
    return UUIDValidator(version=version).validate(uuid_value)


def validate_phone_number(
    phone: str, require_country_code: bool = False
) -> ValidationResult:
    """Validate phone number."""
    return PhoneNumberValidator(require_country_code=require_country_code).validate(
        phone
    )


def validate_password(password: str, min_length: int = 8) -> ValidationResult:
    """Validate password."""
    return PasswordValidator(min_length=min_length).validate(password)
