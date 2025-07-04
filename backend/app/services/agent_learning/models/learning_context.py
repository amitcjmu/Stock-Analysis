"""
Learning Context Model - Context information for scoped learning
"""

import hashlib
from dataclasses import dataclass
from typing import Optional


@dataclass
class LearningContext:
    """Context information for scoped learning."""
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    flow_id: Optional[str] = None
    context_hash: Optional[str] = None
    
    def __post_init__(self):
        """Generate context hash for namespacing."""
        if not self.context_hash:
            context_str = f"{self.client_account_id}:{self.engagement_id}:{self.flow_id}"
            self.context_hash = hashlib.md5(context_str.encode()).hexdigest()[:16]