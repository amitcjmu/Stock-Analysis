"""
Base utilities and imports for canonical applications models
"""

import hashlib
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates

from app.models.base import Base, TimestampMixin

# CC: Import pgvector types with fallback for environments without pgvector
try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    # Fallback to ARRAY(Float) if pgvector not available
    def Vector(dimensions):
        return ARRAY(Float, dimensions=dimensions)

    PGVECTOR_AVAILABLE = False


def normalize_name(name: str) -> str:
    """
    Normalize application name for consistent matching.

    Normalization strategy:
    - Convert to lowercase
    - Strip whitespace
    - Replace multiple spaces with single space
    - Remove special characters except alphanumeric, spaces, hyphens, underscores
    """
    if not name:
        return ""

    # Convert to lowercase and strip
    normalized = name.lower().strip()

    # Replace multiple whitespace with single space
    normalized = re.sub(r"\s+", " ", normalized)

    # Keep only alphanumeric, spaces, hyphens, underscores
    normalized = re.sub(r"[^a-z0-9\s\-_]", "", normalized)

    # Final trim
    return normalized.strip()


def generate_name_hash(normalized_name: str) -> str:
    """Generate SHA-256 hash of normalized name for fast exact matching"""
    if not normalized_name:
        return ""
    return hashlib.sha256(normalized_name.encode("utf-8")).hexdigest()


def calculate_text_similarity(str1: str, str2: str) -> float:
    """
    Calculate text similarity using Levenshtein distance.
    Returns similarity score between 0.0 and 1.0.
    """
    if not str1 or not str2:
        return 0.0
    if str1 == str2:
        return 1.0

    # Simple Levenshtein distance implementation
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    distance = levenshtein_distance(str1, str2)
    max_len = max(len(str1), len(str2))
    return 1.0 - (distance / max_len)
