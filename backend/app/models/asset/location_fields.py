"""Location and environment field definitions for the Asset model."""

from sqlalchemy import Column, String

from .base import SMALL_STRING_LENGTH, MEDIUM_STRING_LENGTH


class LocationFieldsMixin:
    """Mixin providing location and environment fields for the Asset model."""

    # Location and environment
    environment = Column(
        String(SMALL_STRING_LENGTH),
        index=True,
        comment="The operational environment (e.g., 'Production', 'Development', 'Test').",
        info={
            "display_name": "Environment",
            "short_hint": "Production / Staging / Development / QA",
            "category": "environment",
        },
    )
    location = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The geographical location or region of the asset.",
    )
    datacenter = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The datacenter where the asset is hosted.",
    )
    rack_location = Column(
        String(SMALL_STRING_LENGTH),
        comment="The specific rack location within the datacenter.",
    )
    availability_zone = Column(
        String(SMALL_STRING_LENGTH),
        comment="The cloud availability zone, if applicable.",
    )
