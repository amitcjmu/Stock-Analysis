"""
Audit Filters

Methods for filtering sensitive data from audit events.
"""

from app.core.logging import get_logger

from .models import AuditEvent

logger = get_logger(__name__)


class AuditFilters:
    """Audit event filtering methods"""

    @staticmethod
    def filter_sensitive_data(event: AuditEvent) -> AuditEvent:
        """Filter sensitive data from audit events"""
        sensitive_keys = ["password", "secret", "token", "key", "credential"]

        if event.details:
            for key in list(event.details.keys()):
                if any(
                    sensitive_key in key.lower() for sensitive_key in sensitive_keys
                ):
                    event.details[key] = "***FILTERED***"

        if event.metadata:
            for key in list(event.metadata.keys()):
                if any(
                    sensitive_key in key.lower() for sensitive_key in sensitive_keys
                ):
                    event.metadata[key] = "***FILTERED***"

        return event

    @staticmethod
    def filter_pii_data(event: AuditEvent) -> AuditEvent:
        """Filter PII data from audit events"""
        pii_keys = ["ssn", "social_security", "email", "phone", "address", "name"]

        if event.details:
            for key in list(event.details.keys()):
                if any(pii_key in key.lower() for pii_key in pii_keys):
                    event.details[key] = "***PII_FILTERED***"

        return event

    @staticmethod
    def filter_credentials(event: AuditEvent) -> AuditEvent:
        """Filter credential data from audit events"""
        if event.details and "configuration" in event.details:
            config = event.details["configuration"]
            if isinstance(config, dict):
                for key in list(config.keys()):
                    if any(
                        cred_key in key.lower()
                        for cred_key in ["api_key", "secret", "password", "token"]
                    ):
                        config[key] = "***CREDENTIAL_FILTERED***"

        return event

    @staticmethod
    def apply_all_filters(
        event: AuditEvent, audit_filters: dict[str, callable]
    ) -> AuditEvent:
        """
        Apply all registered audit filters to remove sensitive data

        Args:
            event: Audit event to filter
            audit_filters: Dictionary of filter functions

        Returns:
            Filtered audit event
        """
        filtered_event = event

        for filter_name, filter_func in audit_filters.items():
            try:
                filtered_event = filter_func(filtered_event)
            except Exception as e:
                logger.warning(f"Audit filter {filter_name} failed: {e}")

        return filtered_event
