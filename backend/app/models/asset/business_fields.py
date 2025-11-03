"""Business and organizational field definitions for the Asset model."""

from sqlalchemy import Column, JSON, String

from .base import LARGE_STRING_LENGTH, MEDIUM_STRING_LENGTH


class BusinessFieldsMixin:
    """Mixin providing business and organizational fields for the Asset model."""

    # Business information
    business_owner = Column(
        String(LARGE_STRING_LENGTH),
        comment="The name of the business owner or department responsible for the asset.",
        info={
            "display_name": "Business Owner",
            "short_hint": "Business owner or stakeholder",
            "category": "business",
        },
    )
    technical_owner = Column(
        String(LARGE_STRING_LENGTH),
        comment="The name of the technical owner or team responsible for the asset.",
        info={
            "display_name": "Technical Owner",
            "short_hint": "Technical owner or administrator",
            "category": "business",
        },
    )
    department = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The business department or unit that uses this asset.",
        info={
            "display_name": "Department",
            "short_hint": "Department or organizational unit",
            "category": "business",
        },
    )
    application_name = Column(
        String(LARGE_STRING_LENGTH),
        comment="The primary application or service this asset supports.",
        info={
            "display_name": "Application Name",
            "short_hint": "Primary application or service",
            "category": "business",
        },
    )
    technology_stack = Column(
        String(LARGE_STRING_LENGTH),
        comment="A summary of the technology stack running on the asset.",
        info={
            "display_name": "Technology Stack",
            "short_hint": "Technology stack or platform",
            "category": "technical",
        },
    )
    criticality = Column(
        String(20),
        comment="The technical criticality of the asset (e.g., 'Low', 'Medium', 'High').",
        info={
            "display_name": "Technical Criticality",
            "short_hint": "Low / Medium / High",
            "category": "technical",
        },
    )
    business_criticality = Column(
        String(20),
        comment="The business impact or criticality of the asset.",
        info={
            "display_name": "Business Criticality",
            "short_hint": "1-5 scale (1=Low, 5=Critical)",
            "category": "business",
        },
    )
    custom_attributes = Column(
        JSON,
        comment="A JSON blob for storing any custom fields or attributes not in the standard schema.",
    )
    technical_details = Column(
        JSON,
        comment="A JSON blob containing technical details and enrichments for the asset.",
    )
