"""
Configuration and constants for database initialization.
"""

import logging
import uuid
from typing import List

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Static UUIDs for Demo Mode ---
DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DEMO_SESSION_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
DEMO_USER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
ADMIN_USER_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")


def generate_mock_embedding(text: str) -> List[float]:
    """Generates a consistent, fake vector embedding for mock data."""
    # Use a simple hashing method to create a deterministic "random" vector
    np.random.seed(abs(hash(text)) % (2**32 - 1))
    return np.random.rand(1536).tolist()
