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
            "category": "identification",
        },
    )
    location = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The geographical location or region of the asset.",
        info={
            "display_name": "Location",
            "short_hint": "Geographical location or region",
            "category": "identification",
        },
    )
    datacenter = Column(
        String(MEDIUM_STRING_LENGTH),
        comment="The datacenter where the asset is hosted.",
        info={
            "display_name": "Datacenter",
            "short_hint": "Datacenter or facility",
            "category": "identification",
        },
    )
    rack_location = Column(
        String(SMALL_STRING_LENGTH),
        comment="The specific rack location within the datacenter.",
        info={
            "display_name": "Rack Location",
            "short_hint": "Rack identifier",
            "category": "identification",
        },
    )
    availability_zone = Column(
        String(SMALL_STRING_LENGTH),
        comment="The cloud availability zone, if applicable.",
        info={
            "display_name": "Availability Zone",
            "short_hint": "Cloud availability zone",
            "category": "identification",
        },
    )
