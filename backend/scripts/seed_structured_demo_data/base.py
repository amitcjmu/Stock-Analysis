"""
Base module for structured demo data seeding.
Contains common utilities and base seeder class.
"""

import uuid
from typing import Dict


class BaseDemoSeeder:
    """Base class for structured demo data seeding"""

    def __init__(self):
        # Demo tenant identifiers - consistent across all environments
        self.demo_client_id = "11111111-1111-1111-1111-111111111111"
        self.demo_engagement_id = "22222222-2222-2222-2222-222222222222"
        self.demo_user_id = "33333333-3333-3333-3333-333333333333"

    def get_demo_ids(self) -> Dict[str, str]:
        """Get demo tenant identifiers"""
        return {
            "client_id": self.demo_client_id,
            "engagement_id": self.demo_engagement_id,
            "user_id": self.demo_user_id,
        }

    def generate_uuid(self) -> str:
        """Generate a new UUID string"""
        return str(uuid.uuid4())
