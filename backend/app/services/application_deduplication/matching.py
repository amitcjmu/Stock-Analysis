"""
Fuzzy matching utilities for application deduplication
"""

from typing import Optional, Tuple
import uuid
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_applications import CanonicalApplication


class FuzzyMatcher:
    """Handles fuzzy text matching for application names"""

    @staticmethod
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

    async def find_fuzzy_match(
        self,
        db: AsyncSession,
        normalized_name: str,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        threshold: float,
        max_candidates: int = 100,
    ) -> Optional[Tuple[CanonicalApplication, float]]:
        """Try fuzzy text matching using Levenshtein distance"""

        # Get all canonical applications for this engagement
        apps_query = (
            select(CanonicalApplication)
            .where(
                and_(
                    CanonicalApplication.client_account_id == client_account_id,
                    CanonicalApplication.engagement_id == engagement_id,
                )
            )
            .limit(max_candidates)
        )

        result = await db.execute(apps_query)
        all_apps = result.scalars().all()

        best_match = None
        best_similarity = 0.0

        for app in all_apps:
            similarity = self.calculate_text_similarity(
                normalized_name, app.normalized_name
            )

            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = app

        if best_match:
            return best_match, best_similarity

        return None
